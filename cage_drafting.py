"""Manufacturing sheets in physical paper mm: fixed text, dimensions and scales."""
import hashlib,json,math,os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from shapely.geometry import Polygon
from cage_pdf import local_contours,assembly_iso,joint_drawing

ROLES={'side':'Боковая панель','back':'Задняя панель','front':'Передняя панель без двери','top':'Верхняя панель','floor':'Основание над лотком','shelf':'Полка','divider':'Перегородка','tray_base':'Дно лотка','tray_side':'Борт лотка','tray_front_back':'Передний / задний борт лотка','corner_plate_x':'Угловая накладка X','corner_plate_y':'Угловая накладка Y'}
SCALES=[10,5,2,1,.5,.4,.25,.2,.1,.05,.04,.025,.02,.01,.005,.002,.001]

def number(v):return f'{v:.2f}'.rstrip('0').rstrip('.')
def scale_name(s):return '1:'+number(1/s) if s<1 else number(s)+':1'
def select_scale(w,h,bw,bh):
 fit=min(bw/max(w,.01),bh/max(h,.01))
 return next((s for s in SCALES if s<=fit+1e-8),SCALES[-1])

def sheet_groups(parts):
 groups=[]
 for p in parts:
  ctr=local_contours(p);shape=Polygon(ctr[0],ctr[1:])
  match=next((g for g in groups if g[0][0]['role']==p['role'] and g[0][0]['thickness']==p['thickness'] and shape.equals_exact(g[1],.0001,normalize=True)),None)
  if match:match[0].append(p)
  else:groups.append(([p],shape))
 return [g[0] for g in groups]

class Paper:
 def __init__(self,path,result):
  self.r=result;self.o=result['options'];self.w=self.o['CagePdfWidth'];self.h=self.o['CagePdfHeight'];self.c=canvas.Canvas(path if hasattr(path,'write') else str(path),pagesize=(self.w*mm,self.h*mm))
  self.c.setTitle('Клетка - сборочные и рабочие чертежи');self.c.setAuthor('ШипоМастер Aspire')
  pdfmetrics.registerFont(TTFont('DraftArial',str(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/'arial.ttf')))
  geometry={k:v for k,v in self.o.items() if 'Pdf' not in k and k not in ('CageLayoutWidth','cage_pdf_only')}
  geometry['dimension_basis']=result['cage'].get('dimension_basis','legacy_frame')
  self.code='SM.KL.'+hashlib.sha256(json.dumps(geometry,sort_keys=True).encode()).hexdigest()[:8].upper()
  self.left=20 if self.w>=200 else 10;self.right=self.w-5;self.width=self.right-self.left
  self.stamp=55 if self.width>=185 else 35;self.bottom=5+self.stamp+8;self.top=self.h-13;self.total=0;self.index=0;self.scales=[]
 def line(self,x,y,X,Y,kind='thin'):
  c=self.c;c.setStrokeColorRGB(0,0,0);c.setLineWidth((.5 if kind=='outline' else .18)*mm)
  c.setDash(([5*mm,1*mm,1*mm,1*mm] if kind=='axis' else [2*mm,1*mm] if kind=='hidden' else []));c.line(x*mm,y*mm,X*mm,Y*mm);c.setDash([])
 def rect(self,x,y,w,h,kind='outline'):
  for a,b in [((x,y),(x+w,y)),((x+w,y),(x+w,y+h)),((x+w,y+h),(x,y+h)),((x,y+h),(x,y))]:self.line(*a,*b,kind)
 def text(self,x,y,value,size=2.5,align='left',rotate=0):
  c=self.c;c.saveState();c.translate(x*mm,y*mm);c.rotate(rotate);c.setFillColorRGB(0,0,0);c.setFont('DraftArial',size*mm)
  getattr(c,{'left':'drawString','center':'drawCentredString','right':'drawRightString'}[align])(0,0,str(value));c.restoreState()
 def wrap(self,x,y,value,width,size=2.5,leading=4):
  words=str(value).split();line=''
  for word in words:
   test=(line+' '+word).strip()
   if pdfmetrics.stringWidth(test,'DraftArial',size*mm)>width*mm and line:self.text(x,y,line,size);y-=leading;line=word
   else:line=test
  if line:self.text(x,y,line,size);y-=leading
  return y
 def circle(self,x,y,r,kind='thin'):
  self.c.setLineWidth((.5 if kind=='outline' else .18)*mm);self.c.circle(x*mm,y*mm,r*mm,stroke=1,fill=0)
 def arrow(self,x,y,angle):
  size=1.6
  for a in (angle+.24,angle-.24):self.line(x,y,x+size*math.cos(a),y+size*math.sin(a))
 def dim_h(self,x1,x2,feature_y,dim_y,label):
  if abs(x2-x1)<.01:return
  self.line(x1,feature_y,x1,dim_y+(-1 if dim_y<feature_y else 1));self.line(x2,feature_y,x2,dim_y+(-1 if dim_y<feature_y else 1));self.line(x1,dim_y,x2,dim_y)
  self.arrow(x1,dim_y,0);self.arrow(x2,dim_y,math.pi);self.text((x1+x2)/2,dim_y+1,label,2.5,'center')
 def dim_v(self,y1,y2,feature_x,dim_x,label):
  self.line(feature_x,y1,dim_x+1,y1);self.line(feature_x,y2,dim_x+1,y2);self.line(dim_x,y1,dim_x,y2)
  self.arrow(dim_x,y1,math.pi/2);self.arrow(dim_x,y2,-math.pi/2);self.text(dim_x-1,(y1+y2)/2,label,2.5,'center',90)
 def leader(self,anchor,x,y,label):
  self.circle(*anchor,.35);self.line(*anchor,x,y);tw=pdfmetrics.stringWidth(str(label),'DraftArial',2.8*mm)/mm
  self.line(x,y,x+tw+1,y);self.text(x+.5,y+1,label,2.8)
 def table(self,x,top,widths,rows,row=6,font=2.5):
  y=top
  for values in rows:
   heights=[]
   for val,w in zip(values,widths):
    words=str(val).split();length=0;lines=1
    for word in words:
     a=pdfmetrics.stringWidth(word+' ','DraftArial',font*mm)/mm
     if length+a>w-3:lines+=1;length=a
     else:length+=a
    heights.append(lines*3.7+2)
   height=max(row,*heights)
   xx=x
   for val,w in zip(values,widths):self.rect(xx,y-height,w,height,'thin');self.wrap(xx+1.5,y-3.7,val,w-3,font,3.7);xx+=w
   y-=height
  return y
 def begin(self,title,code,scale='-',material=''):
  if self.index:self.c.showPage()
  self.index+=1;self.scales.append(scale);self.rect(self.left,5,self.width,self.h-10)
  self.text(self.left+3,self.top,title,3.5)
  x=self.right-min(185,self.width);y=5;w=self.right-x;h=self.stamp
  self.rect(x,y,w,h)
  if w<185:
   self.line(x,y+12,x+w,y+12);self.line(x,y+23,x+w,y+23);self.text(x+2,y+26,code,2.5);self.text(x+2,y+15,title,2.5);self.text(x+2,y+4,f'М {scale}   Лист {self.index}/{self.total}',2.5);return
  self.line(x+65,y,x+65,y+55);self.line(x+135,y,x+135,y+40);self.line(x+65,y+40,x+185,y+40);self.line(x+65,y+15,x+185,y+15)
  for yy in [5,10,15,20,25,30,35,40,45,50]:self.line(x,y+yy,x+65,y+yy)
  for xx in [17,40,55]:self.line(x+xx,y,x+xx,y+55)
  for yy,label in [(32,'Разраб.'),(27,'Пров.'),(22,'Т.контр.'),(12,'Н.контр.'),(7,'Утв.')]:self.text(x+1,y+yy,label,2.2)
  for xx,label in [(1,'Изм.'),(18,'Лист'),(41,'№ док.'),(56,'Дата')]:self.text(x+xx,y+51.3,label,1.8)
  self.text(x+68,y+46,code,3.5);self.wrap(x+68,y+32,title,64,3,4.5);self.wrap(x+68,y+9,material,64,2.5,4)
  self.line(x+135,y+25,x+185,y+25);self.line(x+135,y+32,x+185,y+32);self.line(x+151,y+25,x+151,y+40);self.line(x+168,y+25,x+168,y+40)
  self.text(x+143,y+35,'Лит.',2.2,'center');self.text(x+159,y+35,'Масса',2.2,'center');self.text(x+176,y+35,'Масштаб',2.2,'center');self.text(x+176,y+27,scale,2.8,'center')
  self.text(x+137,y+18,f'Лист {self.index}   Листов {self.total}',2.5);self.text(x+160,y+6,'ШипоМастер',2.8,'center')
 def finish(self):self.c.save()

class View:
 def __init__(self,p,bounds,area,scale=None):
  x0,y0,x1,y1=bounds;x,y,w,h=area;self.p=p;self.s=scale or select_scale(x1-x0,y1-y0,w,h);self.x=x+(w-(x1-x0)*self.s)/2-x0*self.s;self.y=y+(h-(y1-y0)*self.s)/2-y0*self.s
 def point(self,x,y):return self.x+x*self.s,self.y+y*self.s
 def line(self,x,y,X,Y,kind='outline'):self.p.line(*self.point(x,y),*self.point(X,Y),kind)
 def rect(self,x,y,w,h,kind='outline'):a,b=self.point(x,y);self.p.rect(a,b,w*self.s,h*self.s,kind)
 def circle(self,x,y,r):self.p.circle(*self.point(x,y),r*self.s)
 def paths(self,contours):
  for points in contours:
   for a,b in zip(points,points[1:]):self.line(*a,*b)

def render_drawing(p,d,area,draw=True):
 pts=[]
 for kind,layer,a in d.items:
  if kind=='line':pts.extend([a[:2],a[2:]])
  elif kind=='circle':pts.extend([(a[0]-a[2],a[1]-a[2]),(a[0]+a[2],a[1]+a[2])])
 bounds=(min(a[0] for a in pts),min(a[1] for a in pts),max(a[0] for a in pts),max(a[1] for a in pts));v=View(p,bounds,area)
 for kind,layer,a in (d.items if draw else []):
  if kind=='line':v.line(*a,'thin' if layer in ('DIM','LABEL') else 'outline')
  elif kind=='circle':v.circle(*a)
 return v

def ortho(p,r,axis,area,s):
 o=r['cage']['options'];w=o['CageWidth'];dep=o['CageDepth'];h=o['CageHeight'];extent=w if axis!='side' else dep
 margin=(r['cage']['finished_size'][0]-w)/2
 bounds=(-margin,-margin if axis=='top' else 0,extent+margin,dep+margin if axis=='top' else r['cage']['finished_size'][2])
 v=View(p,bounds,area,s);seen=set()
 for m in r['cage']['members']:
  x,y,z=m['origin'];sx,sy,sz=m['size']
  if axis=='front' and m['role']=='rail_y' or axis=='side' and m['role']=='rail_x':continue
  rect=(x,y,sx,sy) if axis=='top' else ((x,z,sx,sz) if axis=='front' else (y,z,sy,sz))
  if rect not in seen:v.rect(*rect);seen.add(rect)
 for part in r['parts']:
  if part['role'] not in ('floor','shelf','tray_base','divider','top'):continue
  x,y,z=part['origin'];u=part['panel_width'];vv=part['panel_height'];t=part['thickness'];sx,sy,sz=(u,vv,t) if part['axes']=='XY' else (u,t,vv) if part['axes']=='XZ' else (t,u,vv)
  if axis=='top':
   if part['role'] in ('shelf','top'):v.rect(x,y,sx,sy,'hidden')
  else:v.rect(x if axis=='front' else y,z,sx if axis=='front' else sy,sz,'thin')
 x0,y0=v.point(bounds[0],bounds[1]);X,Y=v.point(bounds[2],bounds[3])
 p.dim_h(x0,X,y0,y0-10,number(bounds[2]-bounds[0]));p.dim_v(y0,Y,X,X+10,number(bounds[3]-bounds[1]));return v

def assembly_sheet(p,r):
 o=r['cage']['options'];avail=p.top-p.bottom-12;upper=avail*.62;lower=avail-upper;left=p.left+8;w=p.width-18
 s=select_scale(max(r['options']['CageWidth'],r['options']['CageDepth']),r['options']['CageHeight'],w*.46-8,upper-20)
 p.begin('Клетка. Сборочный чертёж',p.code+'.СБ',scale_name(s),'Разборный каркас; панели снаружи')
 a=(left,p.bottom+lower+8,w*.46,upper-20);b=(left+w*.53,p.bottom+lower+8,w*.43,upper-20)
 vf=ortho(p,r,'front',a,s);vs=ortho(p,r,'side',b,s)
 p.text(a[0]+a[2]/2,p.top-10,'Вид спереди',2.8,'center');p.text(b[0]+b[2]/2,p.top-10,'Вид слева',2.8,'center')
 st=select_scale(o['CageWidth'],o['CageDepth'],w*.46-15,lower-20);ortho(p,r,'top',(left,p.bottom+8,w*.46,lower-20),st)
 p.text(left+w*.23,p.bottom+lower-4,'Вид сверху (М '+scale_name(st)+')',2.8,'center')
 y=p.bottom+lower-10;x=left+w*.54;tw=w*.45
 for text in ['Все размеры в миллиметрах.','Передняя и боковая обшивка условно снята для видимости каркаса и полок.','Общий габарит: '+' × '.join(number(v) for v in r['cage']['finished_size'])+'. Каркас: '+' × '.join(number(v) for v in r['cage']['frame_size'])+'.','Позиции - по спецификации. Уровни - от нижнего торца стойки.']:
  y=p.wrap(x,y,text,tw,2.5,3.8)-2
 # Call out each selected type once; positions come from the same specification.
 members=[m for m in r['cage']['members'] if (m['role']=='post' and m['origin'][0]==0 and m['origin'][1]==0) or (m['role']=='rail_x' and m['origin'][1]==0)]
 unique={m['tube_id']:m for m in members}
 for i,m in enumerate(unique.values()):
  anchor=vf.point(m['origin'][0]+m['size'][0]*.3,m['origin'][2]+m['size'][2]*.6)
  p.leader(anchor,a[0]+2,a[1]+a[3]-9-i*13,str(p.pos[m['tube_id']]))

def iso_sheet(p,r,groups,exploded=False):
 title='Сборка - разнесённые панели и лоток' if exploded else 'Каркас. Сборка и позиции труб'
 p.begin(title,p.code+('.СБ.02' if exploded else '.СБ.01'),'по видам','Позиции соответствуют спецификации')
 d=assembly_iso(r if exploded else dict(r,parts=[]),exploded);area=(p.left+27,p.bottom+20,p.width-54,p.top-p.bottom-35);v=render_drawing(p,d,area,draw=exploded)
 if not exploded:
  for m in sorted(r['cage']['members'],key=lambda m:m['origin'][0]+m['origin'][1]-m['origin'][2],reverse=True):
   x,y,z=m['origin'];sx,sy,sz=m['size']
   for face in [[(x,y,z+sz),(x+sx,y,z+sz),(x+sx,y+sy,z+sz),(x,y+sy,z+sz)],[(x,y,z),(x+sx,y,z),(x+sx,y,z+sz),(x,y,z+sz)],[(x,y,z),(x,y+sy,z),(x,y+sy,z+sz),(x,y,z+sz)]]:
    pts=[v.point(.866025403784*(xx-yy),zz+.5*(xx+yy)) for xx,yy,zz in face];path=p.c.beginPath();path.moveTo(pts[0][0]*mm,pts[0][1]*mm)
    for xx,yy in pts[1:]:path.lineTo(xx*mm,yy*mm)
    path.close();p.c.setFillColorRGB(1,1,1);p.c.setStrokeColorRGB(0,0,0);p.c.setLineWidth(.35*mm);p.c.drawPath(path,stroke=1,fill=1)
 def project(q):return v.point(.866025403784*(q[0]-q[1]),q[2]+.5*(q[0]+q[1]))
 items=[]
 if not exploded:
  for t in r['cage']['tubes']:
   m=next(m for m in r['cage']['members'] if m['id']==t['members'][0]);q=[m['origin'][i]+m['size'][i]/2 for i in range(3)];items.append((p.pos[t['id']],project(q),t['id']))
 else:
  from cage_pdf import world_point
  o=r['cage']['options']
  for g in groups:
   part=g[0]
   if part['role'].startswith('corner_plate'):continue
   q=list(world_point(part,part['panel_width']/2,part['panel_height']/2));role=part['role']
   if role=='side':q[0]+=(-1 if part['origin'][0]<0 else 1)*o['CageWidth']*.45
   elif role=='back':q[1]+=o['CageDepth']*.7
   elif role=='front':q[1]-=o['CageDepth']*.7
   elif role=='top':q[2]+=o['CageHeight']*.35
   elif role.startswith('tray'):q[1]-=o['CageDepth']*.85
   items.append((p.pos[part['name'].split('_')[0]],project(q),part['name'].split('_')[0]))
 for side in [0,1]:
  subset=items[side::2]
  for i,(pos,anchor,mark) in enumerate(subset):
   yy=p.top-20-i*min(17,(p.top-p.bottom-35)/max(len(subset),1));xx=p.left+2 if side==0 else p.right-24;p.leader(anchor,xx,yy,f'{pos} ({mark})')
 p.text(p.left+3,p.bottom+6,'М '+scale_name(v.s)+'. Позиции на полках выносок; C - панели, T - типы труб.',2.5)

def tube_sheet(p,r,t):
 o=r['cage']['options'];L=t['length'];a=o['CageTubeA'];b=o['CageTubeB'];s=select_scale(L,b,p.width-30,14);left=p.left+13
 p.begin(t['id']+' - труба. Рабочий чертёж',p.code+'.'+t['id'],scale_name(s),f'Труба Al {number(a)}×{number(b)}×{number(o["CageTubeWall"])}')
 p.table(p.left+3,p.top-7,[p.width*.18,p.width*.31,p.width*.23,p.width*.24],[['Поз. / марка','Профиль, мм','Длина, мм','Количество'],[str(p.pos[t['id']])+' / '+t['id'],f'{number(a)}×{number(b)}×{number(o["CageTubeWall"])}',number(L),str(t['quantity'])]],font=2.5)
 y=p.top-40;step=21
 for face,fw in [('F1',a),('F2',b),('F3',a),('F4',b)]:
  v=View(p,(0,0,L,fw),(left,y,p.width-28,fw*s),s);v.rect(0,0,L,fw)
  p.text(p.left+3,y+fw*s/2,face,2.8)
  v.line(0,fw/2,L,fw/2,'axis');x0,y0=v.point(0,0);X,Y=v.point(L,fw)
  holes=[h for h in t['holes'] if face in h['faces']]
  for h in holes:
   v.circle(h['along'],h['across'],h['diameter']/2);xx,yy=v.point(h['along'],h['across']);p.line(xx,yy-2,xx,yy+2,'axis');p.line(xx-2,yy,xx+2,yy,'axis')
   p.line(xx,y0,xx,y0-6);p.text(xx-.8,y0-6.5,number(h['along']),2.5,'right',90)
  if face=='F1':p.dim_h(x0,X,Y,Y+10,number(L))
  p.text(x0,y0+fw*s+2,'0',2.2)
  y-=step
 top=y+step-19
 rows=[['Грань','X от торца 0, мм','Y от нижней кромки','Отверстия']]
 for face in ['F1','F2','F3','F4']:
  holes=[h for h in t['holes'] if face in h['faces']]
  rows.append([face,'; '.join(number(h['along']) for h in holes) or '-', '; '.join(sorted({number(h['across']) for h in holes})) or '-',(f'{len(holes)} отв. Ø'+number(holes[0]['diameter'])) if holes else 'Без отверстий'])
 tablebottom=p.table(p.left+3,top,[p.width*.12,p.width*.39,p.width*.25,p.width*.20],rows,font=2.5)
 section_y=max(p.bottom+28,tablebottom-38);xs=p.left+15;cs=select_scale(a,b,27,30)
 p.text(xs,tablebottom-5,'Профиль (М '+scale_name(cs)+')',2.5);p.rect(xs,section_y,a*cs,b*cs);wall=o['CageTubeWall'];p.rect(xs+wall*cs,section_y+wall*cs,(a-2*wall)*cs,(b-2*wall)*cs,'thin');p.dim_h(xs,xs+a*cs,section_y,section_y-10,number(a));p.dim_v(section_y,section_y+b*cs,xs+a*cs,xs+a*cs+10,number(b));p.text(xs+32,section_y+2,'s = '+number(wall),2.5)
 holes=t['holes'];h0=holes[0] if holes else None
 if h0:
  xx=p.left+p.width*.56;yy=section_y;ww=min(45,p.width*.38);facewidth=a if h0['faces'][0] in ('F1','F3') else b;zoom=select_scale(45,facewidth,ww,30);hh=facewidth*zoom
  p.text(xx,tablebottom-5,'Фрагмент отверстия, М '+scale_name(zoom),2.5);p.rect(xx,yy,ww,hh,'thin');cx=xx+min(h0['along'],20)*zoom;cy=yy+h0['across']*zoom
  p.circle(cx,cy,h0['diameter']*zoom/2);p.line(cx,yy-2,cx,yy+hh+2,'axis');p.line(xx-2,cy,xx+ww+2,cy,'axis');p.leader((cx,cy),xx+ww*.65,yy+hh*.75,'Ø'+number(h0['diameter']))
  p.text(xx,yy-7,'Y='+number(h0['across'])+'; грань '+h0['faces'][0],2.5)
 notes=['Сверлить только указанную наружную стенку трубы.','F1/F3: A; F2/F4: B. X от торца 0; Y от нижней кромки. Без зеркалирования.',{'post':'Торец 0 - нижний. F1: -Y; F2: +X; F3: +Y; F4: -X.','rail_x':'Торец 0 - левый. F2: -Y; F4: +Y.','rail_y':'Торец 0 - передний. F2: +X; F4: -X.'}[t['role']],'Торцы 90°. s - толщина стенки. Марки установки: '+', '.join(t['members'])+'.']
 yy=p.bottom+15
 for text in notes:yy=p.wrap(p.left+3,yy,text,p.width-6,2.5,3.7)

def part_sheet(p,r,group):
 part=group[0];w=part['panel_width'];h=part['panel_height'];t=part['thickness'];s=select_scale(w,h,p.width-45,p.top-p.bottom-83)
 marks=', '.join(q['name'].split('_')[0] for q in group);role=ROLES[part['role']]
 p.begin(role,p.code+'.'+part['name'].split('_')[0],scale_name(s),'Лист; толщина '+number(t)+' мм')
 yy=p.wrap(p.left+3,p.top-9,f'Поз. {p.pos[part["name"].split("_")[0]]}. Марки: {marks}. Количество: {len(group)} шт.',p.width-6,2.5,4)
 contours=local_contours(part);v=View(p,(0,0,w,h),(p.left+20,p.bottom+50,p.width-45,p.top-p.bottom-83),s);v.paths(contours);x0,y0=v.point(0,0);X,Y=v.point(w,h)
 p.dim_h(x0,X,y0,y0-10,number(w));p.dim_v(y0,Y,X,X+10,number(h));p.text(x0-3,y0-4,'0',2.5)
 xs=sorted({round(x,3) for x,y in contours[0]});ys=sorted({round(y,3) for x,y in contours[0]})
 if len(xs)>2 and len(xs)<=8:
  for x in xs[1:-1]:xx,yy=v.point(x,0);p.line(xx,y0,xx,y0-17);p.text(xx-1,y0-17,number(x),2.5,'right',90)
 if len(ys)>2 and len(ys)<=8:
  for y in ys[1:-1]:xx,yy=v.point(0,y);p.line(x0,yy,x0-12,yy);p.text(x0-13,yy,number(y),2.5,'right')
 holes=[]
 for ctr in contours[1:]:
  xx=[q[0] for q in ctr];yy=[q[1] for q in ctr];cx=(min(xx)+max(xx))/2;cy=(min(yy)+max(yy))/2;diam=max(xx)-min(xx);holes.append((cx,cy,diam))
  ax,ay=v.point(cx,cy);p.line(ax-3,ay,ax+3,ay,'axis');p.line(ax,ay-3,ax,ay+3,'axis')
 if len(holes)<=4:
  rows=[['Отв.','X от базы 0','Y от базы 0','Диаметр, мм']]+[[str(i+1),number(x),number(y),'Ø'+number(d)] for i,(x,y,d) in enumerate(holes)]
  if holes:p.table(p.left+3,p.bottom+37,[p.width*.12,p.width*.28,p.width*.28,p.width*.28],rows,row=5,font=2.5)
 else:
  ux=sorted({round(x,4) for x,y,d in holes});uy=sorted({round(y,4) for x,y,d in holes})
  y=p.wrap(p.left+3,p.bottom+33,f'Вентиляция: {len(holes)} отв. Ø{number(holes[0][2])}; шаг {number(r["options"]["CageVentPitch"])}.',p.width-6)
  p.wrap(p.left+3,y,f'Центры X: {number(ux[0])}...{number(ux[-1])}, {len(ux)} рядов; Y: {number(uy[0])}...{number(uy[-1])}, {len(uy)} рядов.',p.width-6)
 p.text(p.left+3,p.bottom+5,'Вид снаружи. Координаты от левого нижнего угла; толщина '+number(t)+' мм.',2.5)

def specification_rows(p,r,groups):
 rows=[];pos=0
 for t in r['cage']['tubes']:
  pos+=1;p.pos[t['id']]=pos;rows.append([str(pos),t['id'],'Труба Al '+str(number(r['options']['CageTubeA']))+'×'+number(r['options']['CageTubeB'])+'×'+number(r['options']['CageTubeWall']),str(t['quantity']),'L='+number(t['length'])])
 for g in groups:
  pos+=1
  for part in g:p.pos[part['name'].split('_')[0]]=pos
  rows.append([str(pos),', '.join(part['name'].split('_')[0] for part in g),ROLES[g[0]['role']],str(len(g)),'s='+number(g[0]['thickness'])])
 for item in r['cage']['fasteners']:
  pos+=1;p.pos[item['name']]=pos;rows.append([str(pos),'-',{'M5_bolt':'Болт М5; длину выбрать по узлу','M5_rivet_nut':'Заклёпочная гайка М5','Self_tapping_screw':'Саморез Ø'+number(r['options']['CageScrewDiameter'])+'; исполнение выбрать'}[item['name']],str(item['quantity']),'-'])
 return rows

def joint_sheet(p,r,role):
 label='Узел X' if role=='rail_x' else 'Узел Y';p.begin(label+' - крепление обвязки',p.code+'.'+label[-1],'по виду','Накладка; М5 / саморез по модели')
 from cage_export import Drawing
 o=r['cage']['options'];member=next(m for m in r['cage']['members'] if m['role']==role)
 pairs=zip(r['cage']['plates'],[q for q in r['parts'] if q['role'].startswith('corner_plate')])
 plate=next(q for connection,q in pairs if connection['member']==member['id'] and connection['end']==0)
 side=role=='rail_y';a=o['CageTubeB'] if side else o['CageTubeA'];b=o['CageTubeB'];d=Drawing();d.rect(0,0,a,b+35);d.rect(a,0,o['CageHoleEnd']+40,b)
 offset=(plate['origin'][1] if side else plate['origin'][0],plate['origin'][2]);holes=[]
 for i,ctr in enumerate(local_contours(plate)):
  if not i:
   for q,z in zip(ctr,ctr[1:]):d.line(q[0]+offset[0],q[1]+offset[1],z[0]+offset[0],z[1]+offset[1],'DIM')
  else:
   xs=[x for x,y in ctr];ys=[y for x,y in ctr];cx=(min(xs)+max(xs))/2+offset[0];cy=(min(ys)+max(ys))/2+offset[1];d.circle(cx,cy,(max(xs)-min(xs))/2);holes.append((cx,cy))
 v=render_drawing(p,d,(p.left+22,p.bottom+78,p.width-49,p.top-p.bottom-105))
 x0,y0=v.point(0,0);xa,_=v.point(a,0);xb,_=v.point(a+o['CageHoleEnd'],0)
 p.dim_h(x0,xa,y0,y0-10,number(a));p.dim_h(xa,xb,y0,y0-18,number(o['CageHoleEnd']))
 for i,(cx,cy) in enumerate(holes):
  xx,yy=v.point(cx,cy);p.line(xx-3,yy,xx+3,yy,'axis');p.line(xx,yy-3,xx,yy+3,'axis');p.dim_v(y0,yy,x0,x0-10-i*8,number(cy))
 if holes:p.leader(v.point(a/2,b*.15),p.left+5,p.top-20,'Поз. '+str(p.pos[plate['name'].split('_')[0]])+' - накладка')
 o=r['cage']['options'];yy=p.bottom+53
 for text in [label+'. Масштаб вида '+scale_name(v.s)+'.',r['cage']['connection_note'],f'Проход в накладке Ø{number(o["CageScrewDiameter"]+.3 if o["cage_self_tap"] else o["CageBoltHole"])}; труба Ø{number(o["CageScrewPilot"] if o["cage_self_tap"] else o["CageInsertHole"])}. Только наружная стенка.',f'Накладка s={number(o["CagePlateT"])}. Центр на поперечине от торца: {number(o["CageHoleEnd"])}.',f'Разнос осей стойки: {number(o["CageBoltStagger"])}. Координаты - на рабочих чертежах труб.', 'Панели снаружи через проставки. Трубы встык, торцы 90°; сварка не предусмотрена.']:
  yy=p.wrap(p.left+3,yy,text,p.width-6,2.5,4)-1
 if not r['options']['cage_self_tap']:
  p.text(p.left+3,p.bottom+4,f'Крепёж по спецификации: поз. {p.pos["M5_bolt"]} - болт М5; поз. {p.pos["M5_rivet_nut"]} - гайка М5.',2.5)

def write_cage_pdf(path,result):
 if result['options']['CagePdfWidth']<200 or result['options']['CagePdfHeight']<290:
  from copy import deepcopy
  from io import BytesIO
  from pypdf import PdfReader,PdfWriter,Transformation
  original=result['options'];model=deepcopy(result);model['options']['CagePdfWidth']=210;model['options']['CagePdfHeight']=297
  source=BytesIO();write_cage_pdf(source,model);source.seek(0);reader=PdfReader(source);writer=PdfWriter()
  width=original['CagePdfWidth']*mm;height=original['CagePdfHeight']*mm
  ratio=min(width/(210*mm),height/(297*mm))
  rotated=abs(original['CagePdfWidth']-297)<.001 and abs(original['CagePdfHeight']-210)<.001
  for page in reader.pages:
   target=writer.add_blank_page(width=width,height=height)
   transform=Transformation().rotate(-90).translate(0,210*mm) if rotated else Transformation().scale(ratio).translate((width-210*mm*ratio)/2,(height-297*mm*ratio)/2)
   target.merge_transformed_page(page,transform)
   if not rotated:
    overlay=BytesIO();copy=canvas.Canvas(overlay,pagesize=(width,height));copy.setFont('DraftArial',2*mm);copy.drawString(4*mm,height-3*mm,'Уменьшенная копия A4. Масштабы указаны для исходного A4.');copy.save();overlay.seek(0);target.merge_page(PdfReader(overlay).pages[0])
  with open(path,'wb') as out:writer.write(out)
  return
 p=Paper(path,result);groups=sheet_groups(result['parts']);p.pos={};spec=specification_rows(p,result,groups)
 # Keep every table on a separate framed sheet, repeating its column headings.
 per=max(7,int((p.top-p.bottom-24)/10));chunks=[spec[i:i+per] for i in range(0,len(spec),per)]
 plan=[lambda:assembly_sheet(p,result),lambda:iso_sheet(p,result,groups),lambda:iso_sheet(p,result,groups,True)]
 for chunk in chunks:
  def draw_spec(rows=chunk):
   p.begin('Спецификация сборочной единицы',p.code+'.СП','-','Клетка; каркас и листовые детали')
   p.table(p.left+2,p.top-9,[p.width*.08,p.width*.24,p.width*.4,p.width*.09,p.width*.17],[['Поз.','Марка','Наименование','Кол.','Примечание']]+rows,row=7,font=2.5)
  plan.append(draw_spec)
 for role in ['rail_x','rail_y']:plan.append(lambda role=role:joint_sheet(p,result,role))
 def notes():
  p.begin('Сборка. Уровни и технические указания',p.code+'.СБ.03','-','Размеры в миллиметрах')
  y=p.table(p.left+3,p.top-9,[p.width*.4,p.width*.56],[['Обвязка','Верх трубы Z от нижнего торца стойки']]+[[str(i+1),number(z)] for i,z in enumerate(result['cage']['ring_tops'])],row=6)-9
  for text in ['Порядок: трубы и отверстия → накладки и каркас → основание/полки → направляющие и лоток → наружные панели.',f'Лоток: '+ ' × '.join(number(result['cage']['tray'][k]) for k in ['width','depth','height'])+'.',f'Место направляющей с каждой стороны: {number(p.o["CageGuide"])}; монтажный зазор: {number(p.o["CageClearance"])}.', 'Сплав алюминия, марка панелей, допуски изготовления и исполнение крепежа не заданы; определить по фактическим материалам и фурнитуре.','Передняя панель цельная, без дверей.','Отверстия направляющих, обшивки и перегородок не назначены без чертежей выбранной фурнитуры.','Проверить прямоугольность каркаса по диагоналям и свободное движение лотка.','Изображения печатать без подгонки, 100%, если требуется сохранить указанный масштаб. Все размерные числа - натуральные значения.']:
   y=p.wrap(p.left+3,y,text,p.width-6,2.5,4)-3
 plan.append(notes)
 for t in result['cage']['tubes']:plan.append(lambda t=t:tube_sheet(p,result,t))
 for g in groups:plan.append(lambda g=g:part_sheet(p,result,g))
 p.total=len(plan)
 for draw in plan:draw()
 p.finish()
