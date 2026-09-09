"""Extract exact written note events from MusicXML, without score correction."""
from fractions import Fraction
from pathlib import Path
import xml.etree.ElementTree as ET
import json,zipfile
STEP={'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
def xml_bytes(path):
    path=Path(path)
    if path.suffix=='.mxl':
        with zipfile.ZipFile(path) as z:
            container=ET.fromstring(z.read('META-INF/container.xml'));node=next(x for x in container.iter() if x.tag.endswith('rootfile'))
            return z.read(node.attrib['full-path'])
    return path.read_bytes()
def extract(path):
    root=ET.fromstring(xml_bytes(path));parts=[];all_events=[]
    names={x.attrib['id']:x.findtext('part-name','') for x in root.findall('./part-list/score-part')}
    for pi,part in enumerate(root.findall('part')):
        div=1;beats=Fraction(3);events=[];measures=[];dyn=72
        for mi,measure in enumerate(part.findall('measure')):
            cursor=Fraction(0);prev=Fraction(0);end=Fraction(0)
            for node in measure:
                if node.tag=='attributes':
                    if node.find('divisions') is not None:div=int(node.findtext('divisions'))
                    tm=node.find('time')
                    if tm is not None and tm.find('beats') is not None:
                        numerator=sum(int(x) for x in tm.findtext('beats').split('+'));beats=Fraction(4*numerator,int(tm.findtext('beat-type')))
                elif node.tag in ['backup','forward']:
                    dur=Fraction(node.findtext('duration','0'))/div;cursor+=dur if node.tag=='forward' else -dur
                elif node.tag=='direction':
                    dynamics=node.find('./direction-type/dynamics')
                    if dynamics is not None and len(dynamics):dyn={'ppp':35,'pp':44,'p':54,'mp':64,'mf':76,'f':88,'ff':102,'fff':112}.get(dynamics[0].tag,dyn)
                elif node.tag=='note':
                    dur=Fraction(node.findtext('duration','0'))/div;chord=node.find('chord') is not None;onset=prev if chord else cursor
                    pitch=node.find('pitch')
                    if pitch is not None:
                        midi=12*(int(pitch.findtext('octave'))+1)+STEP[pitch.findtext('step')]+int(float(pitch.findtext('alter','0')))
                        event={'part':pi,'measure':mi,'measure_label':measure.attrib.get('number',str(mi+1)),'onset':str(onset),'duration':str(dur),'midi':midi,'voice':node.findtext('voice','1'),'staff':node.findtext('staff','1'),'velocity':dyn,'tie':sorted(x.attrib.get('type','') for x in node.findall('tie')),'grace':node.find('grace') is not None,'tremolo':node.findtext('./notations/ornaments/tremolo')}
                        events.append(event)
                    if not chord:prev=onset;cursor+=dur
                    end=max(end,onset+dur)
            measures.append({'index':mi,'label':measure.attrib.get('number',str(mi+1)),'nominal_quarters':str(beats),'written_extent':str(end)})
        parts.append({'index':pi,'id':part.attrib['id'],'name':names.get(part.attrib['id'],''),'measure_count':len(measures),'note_count':len(events),'measures':measures});all_events.extend(events)
    return {'parts':parts,'events':all_events,'semantics':'written note segments; repeats and tremolos not expanded; grace durations preserved as written; exact rational quarter-note offsets'}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('output');a=p.parse_args();Path(a.output).write_text(json.dumps(extract(a.input),indent=2))
