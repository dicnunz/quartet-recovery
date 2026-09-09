"""Freeze uncorrected pixel-derived predictions before accessing ground truth."""
from pathlib import Path
import hashlib,json,shutil,datetime
from events import xml_bytes,extract
ROOT=Path(__file__).resolve().parents[1]
def main():
    out=ROOT/'results'
    if (out/'freeze.json').exists():raise RuntimeError('Predictions are already frozen; do not overwrite after reference access')
    mxl=list((out/'final-omr').glob('*.mxl'))
    assert len(mxl)==1,f'Expected one complete movement; found {mxl}'
    shutil.copy2(mxl[0],out/'prediction.mxl');(out/'prediction.musicxml').write_bytes(xml_bytes(mxl[0]))
    events=extract(out/'prediction.musicxml');assert len(events['parts'])==4
    (out/'prediction-events.json').write_text(json.dumps(events,indent=2))
    files=['prediction.mxl','prediction.musicxml','prediction-events.json']
    manifest={'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reference_accessed':False,'input_sha256':hashlib.sha256((ROOT/'data/scan.pdf').read_bytes()).hexdigest(),'files':{f:hashlib.sha256((out/f).read_bytes()).hexdigest() for f in files},'event_extractor_sha256':hashlib.sha256((ROOT/'scripts/events.py').read_bytes()).hexdigest(),'corrections':'None. Raw Audiveris output; retained all recognition errors.','parts':[{k:v for k,v in p.items() if k!='measures'} for p in events['parts']]}
    (out/'freeze.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
