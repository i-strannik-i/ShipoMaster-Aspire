"""Assembly views as INFO vectors, independent of machining contours."""
from math import sin,cos,pi,sqrt,asin
from collections import OrderedDict
from layout_info import text_contours,width,part_shape,NAMES
from shapely import affinity
from shapely.geometry import LineString

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

def fmt(v):return f'{v:.1f}'.rstrip('0').rstrip('.')
def rectangle(w,h):return [(0,0),(w,0),(w,h),(0,h),(0,0)]
def fit_path(s,paths,area):
 pts=[p for path in paths for p in path];x0=min(x for x,y in pts);y0=min(y for x,y in pts);x1=max(x for x,y in pts);y1=max(y for x,y in pts)
 x,y,w,h=area;k=min(w/max(x1-x0,.01),h/max(y1-y0,.01));ox=x+(w-(x1-x0)*k)/2;oy=y+(h-(y1-y0)*k)/2
 def point(u,v):return ox+(u-x0)*k,oy+(v-y0)*k
 for path in paths:s.path([point(*p) for p in path])
 return point,(x1-x0,y1-y0)

def build_box_assembly(result):
 o=result['options'];mode=o['mode'];L=o['dlinna'];W=o['shirina'];H=o['visota'];t=o['dMaterial'];bt=o['DMaterialDna'];roof=result.get('roof');s=Sheet()
 s.path(rectangle(210,297),True);s.text(105,284,'СБОРОЧНЫЙ ЧЕРТЁЖ',4,True);s.text(105,276,MODES[mode].upper(),3.2,True)
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
  fullH=roof['total_height'];side=[rectangle(L,fullH),[(0,H),(L,H)]]
 elif mode==5:
  profile=[(0,0),(L,0)]+[(L+H/2*sin(pi*i/40),H/2-H/2*cos(pi*i/40)) for i in range(1,41)]+[(0,H),(0,0)]
  front=[profile];side=[rectangle(W,H)]
 elif mode==6:
  p=result['parts'][0];front=[c['points'] for c in p['contours']];side=[rectangle(L,bt)]
 p,bounds=fit_path(s,front,(17,174,71,73));s.text(53,254,'ТОРЕЦ / ВИД СПЕРЕДИ',2.6,True);a=p(min(x for path in front for x,y in path),min(y for path in front for x,y in path));s.dim((a[0],a[1]-6),(a[0]+bounds[0]*min(71/bounds[0],73/bounds[1]),a[1]-6),fmt(bounds[0]))
 p,bounds=fit_path(s,side,(119,174,67,73));s.text(153,254,'ВИД СБОКУ',2.6,True);a=p(0,0);z=p(0,bounds[1]);s.dim((a[0]-6,a[1]),(a[0]-6,z[1]),fmt(bounds[1]),True)
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
 fit_path(s,paths,(16,87,91,63));s.text(61,156,'АКСОНОМЕТРИЯ (СХЕМА)',2.6,True)
 y=149;notes=[f'Стенки {fmt(t)} мм; дно / крышка {fmt(bt)} мм.','Размеры натуральные, в миллиметрах.','Шипы и прорези на схеме условные. Точные контуры - в раскладке.']
 if roof:
  notes=[f'R внутренний {fmt(roof["radius"])} мм.',f'Полная высота торца {fmt(fullH)} мм.','Крыша: закрытые пазы и фиксаторы.' if roof['mount']=='overlay' else 'Крыша: шипы в закрытых пазах торцов.']+notes
 for note in notes:y=s.wrap(115,y,note,82,2.7,4.4)-2
 s.text(8,75,'МАРКИ ДЕТАЛЕЙ ПО РАСКЛАДКЕ',2.8)
 groups=OrderedDict()
 for part in result['parts']:
  shape=part_shape(part);b=shape.bounds;key=(part['role'],round(b[2]-b[0],2),round(b[3]-b[1],2),part['thickness']);groups.setdefault(key,[]).append(part['name'].split('_')[0])
 y=67
 for (role,w,h,th),ids in groups.items():
  label=', '.join(ids)+'  '+NAMES.get(role,role.upper())+f'  {len(ids)} шт.; {fmt(w)} × {fmt(h)} × {fmt(th)}'
  y=s.wrap(8,y,label,193,2.5,3.8)-1
 s.text(8,8,'СЛОЙ INFO. НЕ ФРЕЗЕРОВАТЬ. Схема по текущим параметрам.',2.3)
 # Match the diagram's size to the existing layout, preserving shape proportions.
 factor=max(1,result['height']/297,result['width']/450)
 for c in s.contours:c['points']=[[round(x*factor,5),round(y*factor,5)] for x,y in c['points']]
 return {'ok':True,'version':result['version'],'parts':[],'width':210*factor,'height':297*factor,'thickness':result['thickness'],'info':{'layer':'INFO','contours':s.contours,'texts':s.texts,'assembly':True,'source_parts':[p['name'] for p in result['parts']]}}
