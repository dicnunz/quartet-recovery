"""Run pixel-only OMR on the eight-page scan. Never reads reference annotations."""
from pathlib import Path
import subprocess,os
ROOT=Path(__file__).resolve().parents[1]
def main():
    app=ROOT/'vendor/audiveris/opt/audiveris/lib';env=dict(os.environ);env['TESSDATA_PREFIX']=str(ROOT/'vendor/tessdata')
    cmd=[str(app/'runtime/bin/java'),'-Xmx8G','--add-exports=java.desktop/sun.awt.image=ALL-UNNAMED','--enable-native-access=ALL-UNNAMED','-cp',str(ROOT/'build/patch')+':'+str(app/'app/*'),'Audiveris','-batch','-transcribe','-export','-output',str(ROOT/'results/final-omr'),'--',str(ROOT/'data/scan.pdf')]
    with (ROOT/'build/final-omr.log').open('w') as log:subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
if __name__=='__main__':main()
