"""Render the frozen MusicXML. Playback uses the independent event renderer."""
from pathlib import Path
import verovio,cairosvg,hashlib,json
R=Path(__file__).resolve().parents[1];x=R/'results/prediction.musicxml'
assert hashlib.sha256(x.read_bytes()).hexdigest()==json.loads((R/'results/freeze.json').read_text())['files'][x.name]
t=verovio.toolkit();t.setOptions({'pageWidth':1600,'pageHeight':2100,'scale':40,'adjustPageHeight':True,'breaks':'auto','header':'none','footer':'none','svgHtml5':True,'xmlIdSeed':1})
assert t.loadData(x.read_text())
p=R/'results/notation';p.mkdir(exist_ok=True)
for i in range(1,t.getPageCount()+1):
 s=t.renderToSVG(i);(p/f'page-{i:02}.svg').write_text(s)
 cairosvg.svg2png(bytestring=s.encode(),write_to=str(p/f'page-{i:02}.png'),output_width=1440,background_color='white')
print(t.getPageCount(),t.getVersion())
