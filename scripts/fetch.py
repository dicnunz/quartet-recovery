"""Fetch hash-pinned inputs. Reference access is a separate post-freeze action."""
from pathlib import Path
import json,hashlib,urllib.request,argparse,subprocess
R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--reference',action='store_true');a=p.parse_args()
if a.reference:
 f=R/'results/freeze.json';assert f.exists(),'Freeze and commit pixel predictions first'
 subprocess.run(['git','ls-files','--error-unmatch','results/freeze.json'],cwd=R,check=True,stdout=subprocess.DEVNULL)
for row in json.loads((R/'data/sources.json').read_text()):
 if (row['phase']=='reference')!=a.reference:continue
 dest=R/row['path'];dest.parent.mkdir(parents=True,exist_ok=True)
 if not dest.exists():dest.write_bytes(urllib.request.urlopen(row['url']).read())
 assert hashlib.sha256(dest.read_bytes()).hexdigest()==row['sha256'],row['path']
 print(row['path'])
