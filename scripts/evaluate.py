"""Strict index-aligned note comparison, only after an immutable prediction freeze."""
from pathlib import Path
from collections import Counter
import json,hashlib,subprocess
from events import extract
R=Path(__file__).resolve().parents[1]
def main():
 f=json.loads((R/'results/freeze.json').read_text())
 assert hashlib.sha256((R/'scripts/events.py').read_bytes()).hexdigest()==f['event_extractor_sha256']
 for n,h in f['files'].items():
  p=R/('scripts/events.py' if n=='events.py' else 'results/'+n)
  assert hashlib.sha256(p.read_bytes()).hexdigest()==h
 pred=json.loads((R/'results/prediction-events.json').read_text());ref=extract(R/'data/reference.musicxml');out={}
 for name,fields in [('pitch_onset',['part','measure','onset','midi']),('pitch_onset_duration',['part','measure','onset','midi','duration'])]:
  a=Counter(tuple(e[x] for x in fields) for e in pred['events']);b=Counter(tuple(e[x] for x in fields) for e in ref['events']);n=sum((a&b).values());p=n/sum(a.values());r=n/sum(b.values())
  out[name]={'matches':n,'predicted':sum(a.values()),'reference':sum(b.values()),'precision':p,'recall':r,'f1':2*p*r/(p+r) if p+r else 0}
 out['predicted_measures']=[p['measure_count'] for p in pred['parts']];out['reference_measures']=[p['measure_count'] for p in ref['parts']]
 out['reference_sha256']=hashlib.sha256((R/'data/reference.musicxml').read_bytes()).hexdigest();out['method']='Multiset intersection of written segments by staff order and measure index. No alignment, transposition, repeat expansion or post-reference repair. Structural shifts penalize all later measures.'
 (R/'results/metrics.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
