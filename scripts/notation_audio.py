"""Engrave separately, then perform frozen written events without reference repairs."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,subprocess,mido
R=Path(__file__).resolve().parents[1]
def main():
 frozen=json.loads((R/'results/freeze.json').read_text());p=R/'results/prediction-events.json'
 assert hashlib.sha256(p.read_bytes()).hexdigest()==frozen['files'][p.name]
 j=json.loads(p.read_text()); starts={}; events=[]; quarter=60/168
 # Align shared printed measure labels and duplicate occurrences across staves.
 from collections import Counter
 keys={}; lengths={}
 for part in j['parts']:
  occurrences=Counter()
  for m in part['measures']:
   label=m['label'];key=(label,occurrences[label]);occurrences[label]+=1
   keys[part['index'],m['index']]=key
   lengths[key]=max(lengths.get(key,0),float(F(m['nominal_quarters'])))
 ordered=sorted(lengths,key=lambda k:(int(k[0]) if k[0].isdigit() else 100000,k[0],k[1]))
 position={};t=0
 for key in ordered:position[key]=t;t+=lengths[key]
 for k,key in keys.items():starts[k]=position[key]
 (R/'results/playback-alignment.json').write_text(json.dumps({'policy':'Union of numeric printed measure labels and duplicate occurrence across parts; absent measures become rests. Source-only interpretation, no reference used.','measures':[{'label':k[0],'occurrence':k[1],'quarter_onset':position[k],'quarters':lengths[k]} for k in ordered]},indent=2))
 segments=[];pending={};merged=0
 for e in sorted(j['events'],key=lambda e:(starts[e['part'],e['measure']]+float(F(e['onset'])),e['part'],e['midi'])):
  t=(starts[e['part'],e['measure']]+float(F(e['onset'])))*quarter;dur=float(F(e['duration']))*quarter
  if dur<=0:continue
  key=(e['part'],e['voice'],e['midi']);prior=pending.get(key)
  if 'stop' in e['tie'] and prior is not None and abs(segments[prior][1]-t)<1e-7:
   segments[prior][1]=t+dur;merged+=1;idx=prior
  else:
   idx=len(segments);segments.append([max(0,t),max(0,t)+dur,e['part'],e['midi'],e['velocity']])
  if 'start' in e['tie']:pending[key]=idx
  else:pending.pop(key,None)
 for a,b,c,n,v in segments:events.extend([(a,c,n,v,1),(b,c,n,0,0)])
 events.sort(key=lambda e:(e[0],e[4]));(R/'results/playback-events.txt').write_text(''.join(' '.join(map(str,e))+'\n' for e in events))
 mid=mido.MidiFile();track=mido.MidiTrack();mid.tracks.append(track);track.append(mido.MetaMessage('set_tempo',tempo=500000))
 for c,program in enumerate([40,40,41,42]):track.append(mido.Message('program_change',channel=c,program=program))
 prev=0
 for t,c,n,v,on in events:
  tick=round(t*960);track.append(mido.Message('note_on' if on else 'note_off',channel=c,note=n,velocity=v,time=tick-prev));prev=tick
 mid.save(R/'results/performance.mid')
 subprocess.run([str(R/'build/synth'),str(R/'vendor/soundfont/usr/share/sounds/sf2/TimGM6mb.sf2'),str(R/'results/playback-events.txt'),str(R/'build/performance.wav')],check=True)
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(R/'build/performance.wav'),'-c:a','libmp3lame','-b:a','192k',str(R/'results/performance.mp3')],check=True)
 summary={'quarter_bpm':168,'last_event_seconds':events[-1][0],'sounding_segments':sum(e[4] for e in events),'valid_tie_continuations_merged':merged,'recognized_tremolos':0,'parts':4,'semantics':'Written segments aligned by source measure label and duplicate occurrence, no repeat/tremolo expansion; valid adjacent ties merged, malformed ties rearticulated; zero-duration grace notes omitted. No reference repairs. Four string presets assigned by staff order.'}
 (R/'results/performance.json').write_text(json.dumps(summary,indent=2));print(summary)
if __name__=='__main__':main()
