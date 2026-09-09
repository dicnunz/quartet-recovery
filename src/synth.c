/* MIT-licensed offline MIDI-event renderer. TinySoundFont is separately MIT. */
#define TSF_IMPLEMENTATION
#include "tsf.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#define RATE 44100
static void u32(FILE*f,uint32_t n){for(int i=0;i<4;i++)fputc((n>>(8*i))&255,f);}
static void u16(FILE*f,uint16_t n){fputc(n&255,f);fputc(n>>8,f);}
int main(int argc,char**argv){
 if(argc!=4){fprintf(stderr,"synth font.sf2 events.txt output.wav\n");return 2;}
 tsf*s=tsf_load_filename(argv[1]);if(!s)return 3;tsf_set_output(s,TSF_STEREO_INTERLEAVED,RATE,-18);
 int programs[]={40,40,41,42};float pans[]={.15,.38,.62,.85};
 for(int i=0;i<4;i++){tsf_channel_set_presetnumber(s,i,programs[i],0);tsf_channel_set_pan(s,i,pans[i]);}
 FILE*in=fopen(argv[2],"r"),*out=fopen(argv[3],"wb");if(!in||!out)return 4;
 fwrite("RIFF",1,4,out);u32(out,0);fwrite("WAVEfmt ",1,8,out);u32(out,16);u16(out,1);u16(out,2);u32(out,RATE);u32(out,RATE*4);u16(out,4);u16(out,16);fwrite("data",1,4,out);u32(out,0);
 unsigned long at=0,target;double time;int channel,pitch,velocity,on;short buf[1024*2];
 while(fscanf(in,"%lf %d %d %d %d",&time,&channel,&pitch,&velocity,&on)==5){
  target=(unsigned long)(time*RATE+.5);if(target<at)return 5;
  while(at<target){int n=(target-at)>1024?1024:target-at;tsf_render_short(s,buf,n,0);fwrite(buf,4,n,out);at+=n;}
  if(on)tsf_channel_note_on(s,channel,pitch,velocity/127.0f);else tsf_channel_note_off(s,channel,pitch);
 }
 for(int i=0;i<RATE*2;i+=1024){int n=(RATE*2-i)>1024?1024:RATE*2-i;tsf_render_short(s,buf,n,0);fwrite(buf,4,n,out);at+=n;}
 fseek(out,4,SEEK_SET);u32(out,36+at*4);fseek(out,40,SEEK_SET);u32(out,at*4);fclose(in);fclose(out);tsf_close(s);printf("frames=%lu duration=%.3f\n",at,(double)at/RATE);return 0;
}
