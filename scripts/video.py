"""A 64-second film using actual scan pixels, engraved OMR and synthesized events."""
from pathlib import Path
import json,subprocess,math
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];W,H=1920,1080;FPS=24;DURATION=64
BG='#f1eee6';INK='#142d38';MUT='#667676';COL=['#387f95','#ab674b','#8172a1','#5b8b68']
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';serif='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
def f(n,s=False):return ImageFont.truetype(serif if s else font,n)
def text(d,xy,s,n=26,fill=INK,ser=False):d.text(xy,s,font=f(n,ser),fill=fill)
def fit(p,box):
 im=Image.open(p).convert('RGB');im.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS);return im,(box[0]+(box[2]-im.width)//2,box[1]+(box[3]-im.height)//2)
def main():
 scan=Image.open(R/'build/page-000.png').convert('RGB');scan.thumbnail((715,730),Image.Resampling.LANCZOS)
 notation=Image.open(R/'results/notation/page-01.png').convert('RGB');notation.thumbnail((970,750),Image.Resampling.LANCZOS)
 notes=[];active={}
 for line in (R/'results/playback-events.txt').read_text().splitlines():
  t,c,p,v,on=line.split();t=float(t);key=(int(c),int(p))
  if int(on):active.setdefault(key,[]).append(t)
  elif active.get(key):notes.append((active[key].pop(0),t,*key))
 met=json.loads((R/'results/metrics.json').read_text()); out=R/'demo/clara.mp4'
 cmd=['ffmpeg','-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r',str(FPS),'-i','-','-i',str(R/'build/performance.wav'),'-filter_complex','[1:a]adelay=8000|8000,atrim=duration=64,afade=t=out:st=60:d=4[a]','-map','0:v','-map','[a]','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(DURATION),'-movflags','+faststart',str(out)]
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 for frame in range(DURATION*FPS):
  t=frame/FPS;im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
  d.line((64,98,1856,98),fill=INK,width=2);text(d,(64,38),'CLARA  /  RECOVERING A QUARTET',24);text(d,(1465,38),'SCHUBERT · D.703',24)
  if t<8:
   text(d,(90,195),'Music, recovered',82,ser=True);text(d,(90,305),'from the page.',82,ser=True)
   text(d,(96,490),'Eight scanned pages. Four instruments.',31);text(d,(96,545),'A complete, uncorrected optical transcription.',29)
   text(d,(96,700),'01   READ THE PIXELS',23);text(d,(96,750),'02   FREEZE THE PREDICTION',23);text(d,(96,800),'03   LISTEN, THEN MEASURE',23)
   sm=scan.copy();sm.thumbnail((550,790));im.paste(sm,(1240,150))
  elif t<21:
   text(d,(64,124),'The scan becomes editable notation',46,ser=True)
   text(d,(64,195),'Original engraving · page 1',22);text(d,(855,195),'Audiveris prediction · opening measures',22)
   im.paste(scan,(72,240));im.paste(notation,(840,238));text(d,(855,975),'MusicXML exported directly from the eight-page scan.',23)
  elif t<55:
   q=t-8;text(d,(64,124),'Four voices from the frozen prediction',46,ser=True)
   text(d,(64,194),'Uncorrected OMR performance  /  168 quarter notes per minute',24)
   left=320;right=1830;top=285;lane=145;win=9
   for c,label in enumerate(['VIOLIN I','VIOLIN II','VIOLA','CELLO']):
    y=top+c*lane;d.rounded_rectangle((left,y,right,y+118),12,fill='#e4e5df');text(d,(67,y+38),label,25,fill=COL[c])
    for a,b,ch,p in notes:
     if ch!=c or b<q-1 or a>q+win:continue
     x1=left+(a-q+1)/(win+1)*(right-left);x2=left+(b-q+1)/(win+1)*(right-left);yy=y+103-(p-36)/60*90
     d.rounded_rectangle((max(left,x1),yy,max(left+2,min(right,x2)),yy+8),3,fill=COL[c])
   x=left+(right-left)/10;d.line((x,top-15,x,top+3*lane+130),fill=INK,width=3)
   text(d,(320,905),f'{int(q)//60:02}:{int(q)%60:02}  /  05:40 full audio included',26)
   text(d,(320,955),'Written durations; valid ties sustained; no recognized tremolos to expand.',23)
  else:
   text(d,(90,152),'Recovery is measurable.',65,ser=True)
   for x,num,label in [(95,'4,453','predicted note segments'),(730,'47.04%','pitch + onset F1'),(1320,'42.57%','pitch + onset + duration F1')]:
    text(d,(x,345),num,78,ser=True);text(d,(x,459),label,25)
   text(d,(95,615),'Compared with 4,352 reference notes only after the prediction was frozen.',29)
   text(d,(95,680),'Missed measures, rhythm errors and false ties remain in the output.',29)
   text(d,(95,770),'Reference-assisted measure alignment: 87.20% pitch + onset F1.',27)
   text(d,(95,825),'Diagnostic only. A playable draft that still needs correction.',27)
   text(d,(95,905),'Scan · MusicXML · full audio · evaluation · reproducible code',25)
  d.line((64,1030,1856,1030),fill='#c8cec8',width=1);d.line((64,1030,64+1792*t/DURATION,1030),fill=COL[0],width=4)
  text(d,(64,1043),'PIXELS → NOTATION → SOUND',16);text(d,(1550,1043),f'{t:04.1f} / {DURATION} seconds',16)
  if frame==30*FPS:im.save(R/'demo/poster.png')
  proc.stdin.write(im.tobytes())
 proc.stdin.close();assert proc.wait()==0
if __name__=='__main__':main()
