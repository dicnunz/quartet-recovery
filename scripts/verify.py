"""Validate provenance, playback alignment, signal and the complete film."""
from pathlib import Path
import json,hashlib,subprocess,collections,tempfile
from fractions import Fraction
import wave
import numpy as np,mido
R=Path(__file__).resolve().parents[1]
def expected_playback(j):
    """Resolve labels and valid ties independently using exact rational time."""
    duration_by_key={}; key_by_measure={}
    for part in j['parts']:
        seen=collections.Counter()
        for measure in part['measures']:
            label=measure['label'];assert label.isdigit()
            key=(int(label),seen[label]);seen[label]+=1
            key_by_measure[part['index'],measure['index']]=key
            duration_by_key[key]=max(duration_by_key.get(key,Fraction(0)),Fraction(measure['nominal_quarters']))
    starts={};elapsed=Fraction(0)
    for key in sorted(duration_by_key):
        starts[key]=elapsed;elapsed+=duration_by_key[key]
    grouped=collections.defaultdict(list)
    for event in j['events']:
        start=starts[key_by_measure[event['part'],event['measure']]]+Fraction(event['onset'])
        duration=Fraction(event['duration'])
        if duration>0:
            grouped[event['part'],event['voice'],event['midi']].append((start,duration,event))
    segments=[];merge_count=0
    for group in grouped.values():
        pending=None
        for start,duration,event in sorted(group,key=lambda x:x[0]):
            if 'stop' in event['tie'] and pending is not None and pending[1]==start:
                pending[1]=start+duration;segment=pending;merge_count+=1
            else:
                segment=[start,start+duration,event['part'],event['midi'],event['velocity']]
                segments.append(segment)
            pending=segment if 'start' in event['tie'] else None
    events=[]
    for start,end,channel,pitch,velocity in segments:
        events.extend([(float(start*Fraction(5,14)),channel,pitch,velocity,1),
                       (float(end*Fraction(5,14)),channel,pitch,0,0)])
    expected_alignment=[{'label':str(key[0]),'occurrence':key[1],
                         'quarter_onset':float(starts[key]),'quarters':float(duration_by_key[key])}
                        for key in sorted(starts)]
    return events,expected_alignment,merge_count


def canonical(events):
    return sorted((round(e[0],8),*map(int,e[1:])) for e in events)


def main():
 freeze=json.loads((R/'results/freeze.json').read_text())
 for n,h in freeze['files'].items():assert hashlib.sha256((R/'results'/n).read_bytes()).hexdigest()==h,n
 assert hashlib.sha256((R/'scripts/events.py').read_bytes()).hexdigest()==freeze['event_extractor_sha256']
 original=subprocess.check_output(['git','show','a29c52a2e920ee4f4b79c2bee6eeb1f7c1bb7c46:results/freeze.json'],cwd=R);assert json.loads(original)==freeze
 for row in json.loads((R/'data/sources.json').read_text()):
  p=R/row['path']
  if p.exists():assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
 j=json.loads((R/'results/prediction-events.json').read_text());assert len(j['parts'])==4
 alignment=json.loads((R/'results/playback-alignment.json').read_text())['measures'];positions={(m['label'],m['occurrence']):m['quarter_onset'] for m in alignment}
 keys=[]
 for part in j['parts']:
  seen=collections.Counter();partkeys={}
  for m in part['measures']:
   key=m['label'],seen[m['label']];seen[m['label']]+=1;partkeys[key]=positions[key]
  keys.append(partkeys)
 for key in set.intersection(*(set(k) for k in keys)):assert len({k[key] for k in keys})==1
 expected,expected_alignment,merged=expected_playback(j)
 assert alignment==expected_alignment,'Timeline differs from frozen labels and nominal durations'
 events=[list(map(float,l.split())) for l in (R/'results/playback-events.txt').read_text().splitlines()];assert all(a[0]<=b[0] for a,b in zip(events,events[1:]));assert set(e[1] for e in events)=={0,1,2,3}
 assert canonical(events)==canonical(expected),'Playback pitches, timings, velocities or ties differ from frozen notes'
 performance=json.loads((R/'results/performance.json').read_text())
 assert performance['valid_tie_continuations_merged']==merged==150
 assert performance['sounding_segments']==sum(e[-1] for e in expected)
 balance=collections.Counter()
 for t,c,n,v,on in events:
  balance[c,n]+=1 if on else -1;assert balance[c,n]>=0
 assert not any(balance.values())
 midi=mido.MidiFile(R/'results/performance.mid');assert abs(midi.length-events[-1][0])<.002
 assert midi.ticks_per_beat==480 and len(midi.tracks)==1
 programs={};ticks=0;midievents=[]
 for message in midi.tracks[0]:
  ticks+=message.time
  if message.type=='program_change':programs[message.channel]=message.program
  if message.type=='set_tempo':assert message.tempo==500000
  if message.type in ['note_on','note_off']:
   midievents.append((ticks,message.channel,message.note,message.velocity,int(message.type=='note_on')))
 assert programs=={0:40,1:40,2:41,3:42}
 assert midievents==[(round(t*960),int(c),int(n),int(v),int(on)) for t,c,n,v,on in events]
 # Re-synthesize the complete event schedule and compare the actual encoded audio.
 with tempfile.TemporaryDirectory() as directory:
  waveform=Path(directory)/'performance.wav'
  subprocess.run([str(R/'build/synth'),str(R/'vendor/soundfont/usr/share/sounds/sf2/TimGM6mb.sf2'),str(R/'results/playback-events.txt'),str(waveform)],check=True)
  with wave.open(str(waveform),'rb') as wav:
   assert wav.getframerate()==44100 and wav.getnchannels()==2 and wav.getsampwidth()==2
   pcm=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').reshape(-1,2)
  regenerated=pcm.astype(np.float64).mean(axis=1)/32768
  assert hashlib.sha256(waveform.read_bytes()).hexdigest()==hashlib.sha256((R/'build/performance.wav').read_bytes()).hexdigest()
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(R/'results/performance.mp3'),'-f','f32le','-ac','1','-']);samples=np.frombuffer(raw,dtype=np.float32);assert len(samples)/44100>338;assert np.sqrt(np.mean(samples**2))>.001;assert np.max(np.abs(samples))<.98,'Clipped or insufficient headroom'
 audio_n=min(len(samples),len(regenerated));audio_correlation=float(np.corrcoef(samples[:audio_n],regenerated[:audio_n])[0,1]);assert audio_correlation>.98
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(R/'demo/clara.mp4')]))
 v=next(s for s in probe['streams'] if s['codec_type']=='video');assert (v['width'],v['height'])==(1920,1080);assert any(s['codec_type']=='audio' for s in probe['streams']);assert abs(float(probe['format']['duration'])-64)<.1
 subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(R/'demo/clara.mp4'),'-f','null','-'],check=True)
 video_audio=subprocess.check_output(['ffmpeg','-v','error','-i',str(R/'demo/clara.mp4'),'-vn','-ac','1','-ar','44100','-f','f32le','-'])
 video_samples=np.frombuffer(video_audio,dtype=np.float32)
 excerpt=video_samples[8*44100:60*44100]
 video_correlation=float(np.corrcoef(excerpt,regenerated[:len(excerpt)])[0,1]);assert video_correlation>.98
 from events import extract
 from aligned_diagnostic import diagnostic
 reference=extract(R/'data/reference.musicxml')
 aligned=json.loads(json.dumps(diagnostic(j,reference)));saved_aligned=json.loads((R/'results/aligned-diagnostic.json').read_text())
 assert all(saved_aligned[k]==v for k,v in aligned.items())
 strict=json.loads((R/'results/metrics.json').read_text())
 for name,fields in [('pitch_onset',['part','measure','onset','midi']),('pitch_onset_duration',['part','measure','onset','midi','duration'])]:
  a=collections.Counter(tuple(e[k] for k in fields) for e in j['events']);b=collections.Counter(tuple(e[k] for k in fields) for e in reference['events'])
  matches=sum((a&b).values());assert strict[name]['matches']==matches
  assert strict[name]['f1']==2*strict[name]['precision']*strict[name]['recall']/(strict[name]['precision']+strict[name]['recall'])
  assert strict[name]['precision']==matches/len(j['events']) and strict[name]['recall']==matches/len(reference['events'])
 out={'frozen_playback_events':'exact match with rational-time source reconstruction','synthesis_mp3_correlation':audio_correlation,'video_excerpt_correlation':video_correlation,'strict_and_aligned_metrics':'recomputed','frozen_hashes':'pass','freeze_commit':'pass','source_hashes':'pass','common_measure_alignment':'pass','balanced_four_part_events':'pass','midi_duration_seconds':midi.length,'audio_seconds':len(samples)/44100,'audio_rms':float(np.sqrt(np.mean(samples**2))),'audio_peak':float(np.max(np.abs(samples))),'engraved_pages':len(list((R/'results/notation').glob('*.svg'))),'video':'1920x1080, 64 seconds, audio, full decode passed'}
 (R/'results/verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
