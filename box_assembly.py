"""Assembly views as INFO vectors, independent of machining contours."""
from math import sin,cos,pi,sqrt,asin
from collections import OrderedDict
from itertools import combinations,islice
from layout_info import text_contours,width,part_shape,NAMES
from shapely import affinity
from shapely.geometry import LineString,box

MODES=['Простой ящик','Ящик с перегородками','Дно в пазы','Дно в пазы и перегородки','Шип-паз под крышку','Книжка с прорезями','Заготовка с прорезями','Дно и крышка в пазы','Изогнутая крышка']
class Sheet:
 def __init__(self):self.contours=[];self.texts=[]
 def line(self,a,b):self.contours.append(dict(closed=False,points=[list(a),list(b)]))
 def path(self,points,closed=False):self.contours.append(dict(closed=closed,points=[list(p) for p in points]))
 def text(self,x,y,label,h=2.8,center=False):
  self.texts.append(str(label));self.contours+=text_contours(str(label),x-width(str(label),h)/2 if center else x,y,h)
 def wrap(self,x,y,label,maxwidth=182,h=2.8,step=4.5):
  line=''
  for word in str(label).split():
   test=(line+' '+word).strip()
   if width(test,h)>maxwidth and line:self.text(x,y,line,h);y-=step;line=word
   else:line=test
  if line:self.text(x,y,line,h);y-=step
  return y
 def dim(self,a,b,value,vertical=False):
  self.line(a,b)
  for x,y in (a,b):self.line((x-1,y-1),(x+1,y+1))
  if vertical:self.text(a[0]+2,(a[1]+b[1])/2,str(value),2.6)
  else:self.text((a[0]+b[0])/2,a[1]-5,str(value),2.6,True)
 def callout(self,label,anchor,x,y):
  h=min(3.2,14/max(width(label,1),.01));self.text(x,y,label,h)
  w=width(label,h);end=(x+w if x<anchor[0] else x,y-1)
  self.path([anchor,end])
  self.line((x,y-1),(x+w,y-1))
  ax,ay=anchor;self.path([(ax-.45,ay),(ax,ay+.45),(ax+.45,ay),(ax,ay-.45),(ax-.45,ay)],True)
  return dict(leader=[list(anchor),list(end)],label_bounds=[x,y,x+w,y+h])

def fmt(v):return f'{v:.1f}'.rstrip('0').rstrip('.')
def rectangle(w,h):return [(0,0),(w,0),(w,h),(0,h),(0,0)]
def fit_path(s,paths,area):
 pts=[p for path in paths for p in path];x0=min(x for x,y in pts);y0=min(y for x,y in pts);x1=max(x for x,y in pts);y1=max(y for x,y in pts)
 x,y,w,h=area;k=min(w/max(x1-x0,.01),h/max(y1-y0,.01));ox=x+(w-(x1-x0)*k)/2;oy=y+(h-(y1-y0)*k)/2
 def point(u,v):return ox+(u-x0)*k,oy+(v-y0)*k
 for path in paths:s.path([point(*p) for p in path])
 return point,(x1-x0,y1-y0)

def leader_rows(column,x,extra=0):
 """Choose separated shelves whose diagonal leaders do not cross each other."""
 n=len(column)
 if not n:return []
 for slots in (max(9,n),max(13,n)):
  rows=[102+extra-(48+extra)*i/max(1,slots-1) for i in range(slots)]
  best=None
  for indexes in islice(combinations(range(slots),n),20000):
   ys=[rows[i] for i in indexes]
   if any(a-b<4.5 for a,b in zip(ys,ys[1:])):continue
   lines=[];valid=True
   for c,y in zip(column,ys):
    end=(x+min(width(c['id'],3.2),14) if x<c['anchor'][0] else x,y-1)
    line=LineString([c['anchor'],end])
    if any(line.intersects(other) for other in lines):valid=False;break
    lines.append(line)
   if valid:
    score=sum((y-1-c['anchor'][1])**2 for c,y in zip(column,ys))
    if best is None or score<best[0]:best=(score,ys)
  if best:return best[1]
 raise ValueError('Для выносок на сборочном чертеже недостаточно места. Уменьшите количество перегородок или фиксаторов.')

def build_box_assembly(result):
 o=result['options'];mode=o['mode'];L=o['dlinna'];W=o['shirina'];H=o['visota'];t=o['dMaterial'];bt=o['DMaterialDna'];roof=result.get('roof');s=Sheet()
 count=len(result['parts'])-sum(p['role']=='roof_lock' for p in result['parts'])+(2 if roof and roof['lock_count'] else 0)
 extra=max(0,((count+1)//2-1)*6-48);page_height=297+extra
 s.path(rectangle(210,page_height),True);s.text(105,284,'СБОРОЧНЫЙ ЧЕРТЁЖ',4,True);s.text(105,276,MODES[mode].upper(),3.2,True)
 s.text(105,268,(f'Заготовка: Д {fmt(L)} × Ш {fmt(W)} × Т {fmt(bt)} мм' if mode==6 else f'Корпус: Ш {fmt(W)} × Д {fmt(L)} × В {fmt(H)} мм'),2.8,True)
 front=[rectangle(W,H)];side=[rectangle(L,H)];fullH=H
 if mode==8:
  part=next(p for p in result['parts'] if p['role']=='arch_end');shape=part_shape(part);b=shape.bounds
  if abs((b[2]-b[0])-roof['total_height'])<abs((b[3]-b[1])-roof['total_height']):shape=affinity.rotate(shape,90,origin=(0,0))
  x0,y0,x1,y1=shape.bounds
  bottom=shape.intersection(LineString([(x0-1,y0+(y1-y0)*.05),(x1+1,y0+(y1-y0)*.05)])).length
  top=shape.intersection(LineString([(x0-1,y0+(y1-y0)*.95),(x1+1,y0+(y1-y0)*.95)])).length
  if bottom<top:shape=affinity.scale(shape,yfact=-1,origin=(0,0))
  x0,y0,_,_=shape.bounds;shape=affinity.translate(shape,-x0,-y0);front=[list(shape.exterior.coords)]+[list(r.coords) for r in shape.interiors]
  fullH=max(shape.bounds[3],roof['roof_top_height']);oh=roof['overhang']
  silhouette=box(0,0,L,H).union(box(-oh,H,L+oh,roof['roof_top_height'])).union(box(0,H,t,fullH)).union(box(L-t,H,L,fullH))
  side=[list(silhouette.exterior.coords),[(0,H),(L,H)]]
 elif mode==5:
  profile=[(0,0),(L,0)]+[(L+H/2*sin(pi*i/40),H/2-H/2*cos(pi*i/40)) for i in range(1,41)]+[(0,H),(0,0)]
  front=[profile];side=[rectangle(W,H)]
 elif mode==6:
  p=result['parts'][0];front=[c['points'] for c in p['contours']];side=[rectangle(L,bt)]
 bottom=o['SmeshenieDno']+bt if mode in (2,3,7) or mode==8 and o['bottom_in_grooves'] else bt
 if mode!=6:side.append([(0,bottom),(L,bottom)])
 if mode in (4,7):side.append([(0,H-bt),(L,H-bt)])
 p,bounds=fit_path(s,front,(20,126,65,42));s.text(53,175,'ВИД СПЕРЕДИ',2.6,True)
 front_span=bounds[0]
 a=p(0,0);z=p(bounds[0],0);s.dim((a[0],a[1]-5),(z[0],z[1]-5),fmt(bounds[0]))
 front_ids=[part['name'].split('_')[0] for part in result['parts'] if part['role']=='arch_end' or part['name'].startswith(('001_','005_'))]
 q=p(bounds[0]/2,bounds[1]*.4);s.text(*q,', '.join(front_ids),3.2,True)
 side_ids=[part['name'].split('_')[0] for part in result['parts'] if part['role']=='wall' and part['name'].startswith(('002_','004_'))]
 p,bounds=fit_path(s,side,(125,195,60,50));s.text(155,252,'ВИД СБОКУ',2.6,True);xmin=min(x for path in side for x,y in path);a=p(xmin,0);z=p(xmin,bounds[1]);s.dim((a[0]-6,a[1]),(a[0]-6,z[1]),fmt(bounds[1]),True)
 if side_ids:s.text(*p(L/2,H*.45),', '.join(side_ids),3.2,True)
 bottom_ids=[part['name'].split('_')[0] for part in result['parts'] if part['role']=='bottom']
 lid_ids=[part['name'].split('_')[0] for part in result['parts'] if part['role']=='lid']
 side_marks=list(side_ids)
 for ids,level,y in ((bottom_ids,bt/2 if mode==6 else bottom-bt/2,195),(lid_ids,(H+fullH)/2 if mode==8 else H-bt/2,239)):
  if ids:s.callout(', '.join(ids),p(L*.8,level),194,y);side_marks+=ids
 views=[dict(name='front',part_ids=front_ids),dict(name='side',part_ids=side_marks)]
 # Plan views: the removable cover is visible from above; the bottom from below.
 for name,title,area,ids in [('top','ВИД СВЕРХУ',(20,195,65,50),lid_ids),('bottom','ВИД СНИЗУ',(125,126,60,42),bottom_ids)]:
  plan=[rectangle(W,L)]
  plan_min,plan_max=0,W;plan_ymin,plan_ymax=0,L
  if mode==8:
   margin=(front_span-W)/2;over=min(margin,roof['thickness'])
   plan_min,plan_max=-margin,W+margin
   plan_ymin,plan_ymax=-roof['overhang'],L+roof['overhang']
   silhouette=box(-over,plan_ymin,W+over,plan_ymax).union(box(plan_min,0,plan_max,t)).union(box(plan_min,L-t,plan_max,L))
   plan=[list(silhouette.exterior.coords)]
   if name=='bottom':plan.append(rectangle(W,L))
  if not ids and mode!=6:plan.append([(t,t),(W-t,t),(W-t,L-t),(t,L-t),(t,t)])
  if name=='top' and not lid_ids and mode in (1,3):
   for n,axis in ((int(o['KolPeregorodokPoDline']),0),(int(o['KolPeregorodokPoShirine']),1)):
    for i in range(1,n+1):
     plan.append([(t,L*i/(n+1)),(W-t,L*i/(n+1))] if axis==0 else [(W*i/(n+1),t),(W*i/(n+1),L-t)])
  q,_=fit_path(s,plan,area);cx=area[0]+area[2]/2
  s.text(cx,252 if name=='top' else 175,title,2.6,True)
  marks=list(ids) if ids else front_ids+side_ids
  if ids:s.text(*q(W/2,L/2),', '.join(ids),3.2,True)
  else:
   for i,ident in enumerate(front_ids):s.text(*q(W/2,L*(.1 if i==0 else .88)),ident,2.6,True)
   for i,ident in enumerate(side_ids):
    pos=q(0 if i==0 else W,L*.5);s.text(pos[0]+(-7 if i==0 else 1),pos[1],ident,2.6)
   if name=='top' and mode!=6:
    if bottom_ids:s.text(*q(W*.27,L*.23),', '.join(bottom_ids),2.6,True);marks+=bottom_ids
    dividers=[part['name'].split('_')[0] for part in result['parts'] if part['role']=='divider']
    nl=int(o['KolPeregorodokPoDline']);nw=int(o['KolPeregorodokPoShirine'])
    for i,ident in enumerate(dividers):
     pos=q(W*.25,L*(i+1)/(nl+1)) if i<nl else q(W*(i-nl+1)/(nw+1),L*.8)
     s.text(pos[0]+.7,pos[1]+.7,ident,2.1);marks.append(ident)
  a=q(plan_min,plan_ymin);b=q(plan_max,plan_ymin);s.dim((a[0],a[1]-4),(b[0],b[1]-4),fmt(plan_max-plan_min))
  z=q(plan_max,plan_ymax);s.dim((b[0]+6,b[1]),(z[0]+6,z[1]),fmt(plan_ymax-plan_ymin),True)
  views.append(dict(name=name,part_ids=marks))
 if extra:
  for c in s.contours[1:]:c['points']=[[x,y+extra] for x,y in c['points']]
 # Axonometric schematic with the actual roof arc; dimensions are on orthogonal views.
 def P(x,y,z):return (.866025403784*(x-y),z+.5*(x+y))
 paths=[]
 def edge(a,b):paths.append([P(*a),P(*b)])
 if mode==6:
  for z in (0,bt):paths.append([P(x,y,z) for x,y in rectangle(L,W)])
 else:
  for z in (0,H):paths.append([P(x,y,z) for x,y in rectangle(L,W)])
  for x in (0,L):
   for y in (0,W):edge((x,y,0),(x,y,H))
  bottom=o['SmeshenieDno']+bt if mode in (2,3,7) or mode==8 and o['bottom_in_grooves'] else bt
  paths.append([P(x,y,bottom) for x,y in rectangle(L,W)])
  if mode==8:
   R=roof['radius'];alpha=asin(W/(2*R));drop=sqrt(max(0,R*R-W*W/4));rr=R+roof['thickness']
   for x in (0,L):paths.append([P(x,W/2+rr*sin(-alpha+2*alpha*i/40),H+rr*cos(-alpha+2*alpha*i/40)-drop) for i in range(41)])
   for i in range(0,41,8):a=-alpha+2*alpha*i/40;y=W/2+rr*sin(a);z=H+rr*cos(a)-drop;edge((0,y,z),(L,y,z))
  elif mode in (4,7):paths.append([P(x,y,H-bt) for x,y in rectangle(L,W)])
  for n,axis in [(o['KolPeregorodokPoDline'],0),(o['KolPeregorodokPoShirine'],1)]:
   if mode not in (1,3):continue
   for i in range(1,int(n)+1):
    if axis==0:x=L*i/(n+1);edge((x,0,bottom),(x,W,bottom));edge((x,0,H),(x,W,H))
    else:y=W*i/(n+1);edge((0,y,bottom),(L,y,bottom));edge((0,y,H),(L,y,H))
 if mode==5:
  profile=front[0];paths=[[P(x,y,z) for x,z in profile] for y in (0,W)]
  for i in range(0,len(profile),5):x,z=profile[i];paths.append([P(x,0,z),P(x,W,z)])
 iso,_=fit_path(s,paths,(24,59,68,43+extra));s.text(61,109+extra,'ИЗОМЕТРИЯ (СХЕМА)',2.6,True)
 # Use the SAME identifiers as the cut layout, with leaders terminating on each part.
 targets=[];divider_index=0;lock_index=0
 bottom=o['SmeshenieDno']+bt if mode in (2,3,7) or mode==8 and o['bottom_in_grooves'] else bt
 for part in result['parts']:
  ident=part['name'].split('_')[0];role=part['role'];number=int(ident)
  if role=='bottom':xyz=(L*.5,W*.5,bt if mode==6 else bottom)
  elif role=='lid':xyz=(L*.5,W*.5,fullH)
  elif role=='divider':
   nl=int(o['KolPeregorodokPoDline']);nw=int(o['KolPeregorodokPoShirine']);divider_index+=1
   xyz=(L*divider_index/(nl+1),W*.3,bottom+min(o['VisotaPeregorodok'],H-bottom)*.6) if divider_index<=nl else (L*.65,W*(divider_index-nl)/(nw+1),bottom+min(o['VisotaPeregorodok'],H-bottom)*.6)
  elif role=='roof_lock':
   count=roof['tab_count'];joint=roof['joints'][lock_index%count]
   angle=roof['angle_degrees']*pi/180;neutral=roof['developed_length']/angle
   theta=(joint['start']+joint['end'])/(2*neutral)-angle/2
   rr=roof['radius']+roof['thickness'];drop=sqrt(max(0,roof['radius']**2-W*W/4))
   xyz=(0 if lock_index<count else L,W/2+rr*sin(theta),H+rr*cos(theta)-drop);lock_index+=1
  elif number in (1,5):xyz=(0 if number==1 else L,W*.5,H*.55)
  else:xyz=(L*.5,0 if number==2 else W,H*.6)
  targets.append(dict(part=part['name'],parts=[part['name']],ids=[ident],id=ident,anchor=iso(*P(*xyz))))
 if roof and roof['lock_count']:
  normal=[c for c in targets if not c['part'].endswith('_roof_lock')]
  locks=[c for c in targets if c['part'].endswith('_roof_lock')];n=roof['tab_count']
  for batch in (locks[:n],locks[n:]):
   c=batch[len(batch)//2].copy();c['parts']=[v['part'] for v in batch];c['ids']=[v['id'] for v in batch]
   c['id']=c['ids'][0]+'–'+c['ids'][-1] if len(batch)>1 else c['ids'][0];normal.append(c)
  targets=normal
 # Split leaders on either side of the view; arrange their labels top to bottom.
 ordered=sorted(targets,key=lambda c:c['anchor'][0]);middle=(len(ordered)+1)//2
 for column,x in ((ordered[:middle],8),(ordered[middle:],100)):
  column=sorted(column,key=lambda c:-c['anchor'][1])
  for c,y in zip(column,leader_rows(column,x,extra)):
   c['label_position']=(x,y)
   c.update(s.callout(c['id'],c['anchor'],x,y))
 views.append(dict(name='isometric',part_ids=[p['name'].split('_')[0] for p in result['parts']]))
 views.sort(key=lambda v:['top','side','front','bottom','isometric'].index(v['name']))
 y=103+extra;notes=[f'Стенки {fmt(t)} мм; дно / крышка {fmt(bt)} мм.','Размеры натуральные, в миллиметрах.','Шипы и прорези на схеме условные. Точные контуры - в раскладке.']
 if roof:
  notes=[f'R внутренний {fmt(roof["radius"])} мм.',f'Полная высота торца {fmt(fullH)} мм.','Крыша: закрытые пазы и фиксаторы.' if roof['mount']=='overlay' else 'Крыша: шипы в закрытых пазах торцов.']+notes
 for note in notes:y=s.wrap(115,y,note,82,2.7,4.4)-2
 s.text(8,50,'ПЕРЕЧЕНЬ ДЕТАЛЕЙ',2.8)
 groups=OrderedDict()
 for part in result['parts']:
  shape=part_shape(part);b=shape.bounds;key=(part['role'],round(b[2]-b[0],2),round(b[3]-b[1],2),part['thickness']);groups.setdefault(key,[]).append(part['name'].split('_')[0])
 columns=[8,43,114,132,202]
 for x,label in zip((10,45,116,134),('ПОЗ.','ДЕТАЛЬ','КОЛ.','РАЗМЕРЫ, ММ')):s.text(x,42,label,2.3)
 s.line((8,46),(202,46));s.line((8,40),(202,40));y=40
 for (role,w,h,th),ids in groups.items():
  a=s.wrap(10,y-3.2,', '.join(ids),31,2.1,3)
  b=s.wrap(45,y-3.2,NAMES.get(role,role.upper()),65,2.1,3)
  s.text(123,y-3.2,str(len(ids)),2.1,True)
  s.text(134,y-3.2,f'{fmt(w)} × {fmt(h)} × {fmt(th)}',2.1)
  y=min(a,b)+.7;s.line((8,y),(202,y))
 for x in columns:s.line((x,46),(x,y))
 space=max(0,13-y)
 if space:
  page_height+=space;s.contours[0]['points']=[list(p) for p in rectangle(210,page_height)]
  for c in s.contours[1:]:c['points']=[[x,y+space] for x,y in c['points']]
  for c in targets:
   for key in ('anchor','label_position'):c[key]=(c[key][0],c[key][1]+space)
   c['leader']=[[x,y+space] for x,y in c['leader']]
   c['label_bounds']=[v+(space if i%2 else 0) for i,v in enumerate(c['label_bounds'])]
 s.text(8,8,'СЛОЙ INFO. НЕ ФРЕЗЕРОВАТЬ. Схема по текущим параметрам.',2.3)
 # Match the diagram's size to the existing layout, preserving shape proportions.
 factor=max(1,result['height']/page_height,result['width']/450)
 for c in s.contours:c['points']=[[round(x*factor,5),round(y*factor,5)] for x,y in c['points']]
 for c in targets:
  for key in ('anchor','label_position'):c[key]=[round(v*factor,5) for v in c[key]]
  c['leader']=[[round(v*factor,5) for v in p] for p in c['leader']]
  c['label_bounds']=[round(v*factor,5) for v in c['label_bounds']]
 return {'ok':True,'version':result['version'],'parts':[],'width':210*factor,'height':page_height*factor,'thickness':result['thickness'],'info':{'layer':'INFO','contours':s.contours,'texts':s.texts,'callouts':targets,'views':views,'assembly':True,'source_parts':[p['name'] for p in result['parts']]}}
