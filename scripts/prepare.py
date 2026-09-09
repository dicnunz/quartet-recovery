"""Unpack tools, retain OMR sheets in memory, and build offline synthesis."""
from pathlib import Path
import subprocess,os
ROOT=Path(__file__).resolve().parents[1];V=ROOT/'vendor';B=ROOT/'build'
def main():
    B.mkdir(exist_ok=True)
    for name,folder in [('audiveris.deb','audiveris'),('soundfont.deb','soundfont')]:subprocess.run(['dpkg-deb','-x',str(V/name),str(V/folder)],check=True)
    source=(V/'CLI.java').read_text();old='boolean swap = (OMR.gui == null) || isSwap() || swapProcessedSheets();'
    assert source.count(old)==1
    (B/'CLI.java').write_text(source.replace(old,'boolean swap = false; // Clara: retain sheets to avoid 5.11 batch deserialization failure'))
    app=V/'audiveris/opt/audiveris/lib/app';cp=':'.join(str(p) for p in app.glob('*.jar'))
    subprocess.run(['java','-jar',str(V/'ecj.jar'),'-25','--system',str(app.parent/'runtime'),'-cp',cp,'-d',str(B/'patch'),str(B/'CLI.java')],check=True)
    subprocess.run(['gcc','-O2','-I'+str(V/'tinysoundfont'),str(ROOT/'src/synth.c'),'-lm','-o',str(B/'synth')],check=True)
    subprocess.run(['pdfimages','-png',str(ROOT/'data/scan.pdf'),str(B/'page')],check=True)
if __name__=='__main__':main()
