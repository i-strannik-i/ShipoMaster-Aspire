"""Printable INFO vectors, separate from machining geometry (Windows Arial)."""
from functools import lru_cache
from pathlib import Path
import os
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from shapely.geometry import Polygon,box

NAMES={'wall':'СТЕНКА','bottom':'ДНО','lid':'КРЫШКА','arch_end':'АРОЧНЫЙ ТОРЕЦ','roof_lock':'ФИКСАТОР КРЫШИ','divider':'ПЕРЕГОРОДКА','side':'БОКОВИНА','back':'ЗАДНЯЯ ПАНЕЛЬ','top':'ВЕРХНЯЯ ПАНЕЛЬ','front':'ПЕРЕДНЯЯ ПАНЕЛЬ','floor':'ОСНОВАНИЕ','shelf':'ПОЛКА','tray_base':'ДНО ЛОТКА','tray_front_back':'БОРТ ЛОТКА','tray_side':'БОКОВИНА ЛОТКА','corner_plate_x':'НАКЛАДКА X','corner_plate_y':'НАКЛАДКА Y'}

class Pen(BasePen):
 def __init__(self,glyphs):super().__init__(glyphs);self.paths=[];self.current=[]
 def _moveTo(self,p):self.current=[p]
 def _lineTo(self,p):self.current.append(p)
 def _qCurveToOne(self,p1,p2):
  p0=self._getCurrentPoint()
  for i in range(1,9):
   t=i/8;self.current.append(tuple((1-t)**2*p0[j]+2*(1-t)*t*p1[j]+t*t*p2[j] for j in [0,1]))
 def _curveToOne(self,p1,p2,p3):
  p0=self._getCurrentPoint()
  for i in range(1,13):
   t=i/12;self.current.append(tuple((1-t)**3*p0[j]+3*(1-t)**2*t*p1[j]+3*(1-t)*t*t*p2[j]+t**3*p3[j] for j in [0,1]))
 def _closePath(self):
  if self.current:self.paths.append(self.current+[self.current[0]])
 def _endPath(self):self._closePath()

@lru_cache(maxsize=1)
def font():
 f=TTFont(Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/'arial.ttf');return f,f.getGlyphSet(),f.getBestCmap(),f['OS/2'].sCapHeight

@lru_cache(maxsize=256)
def glyph(ch):
 f,gs,cmap,cap=font();name=cmap.get(ord(ch),'.notdef');pen=Pen(gs);gs[name].draw(pen)
 return f['hmtx'][name][0]/cap,[[(x/cap,y/cap) for x,y in p] for p in pen.paths]

def width(text,h):return sum(glyph(c)[0] for c in text)*h

def text_contours(text,x,y,h):
 result=[]
 for c in text:
  advance,paths=glyph(c)
  for points in paths:result.append({'closed':True,'points':[[round(x+px*h,5),round(y+py*h,5)] for px,py in points]})
  x+=advance*h
 return result

def part_shape(part):
 outer=[c for c in part['contours'] if c['closed'] and not c.get('hole')]
 holes=[c['points'] for c in part['contours'] if c.get('hole')]
 return Polygon(outer[0]['points'],holes)

def add_info(result,sheet_width=0,sheet_height=0):
 if not result.get('parts'):return result
 rows=[]
 for part in result['parts']:
  shape=part_shape(part);x0,y0,x1,y1=shape.bounds;ident=part['name'].split('_')[0]
  label=f"{ident}  {NAMES.get(part['role'],part['role'].upper())}  {x1-x0:.1f} × {y1-y0:.1f} × {part['thickness']:g}"
  rows.append((part,shape,ident,label))
 # A4 printable area with 10 mm margins; scale also accounts for the legend.
 hpaper=2.6;rowpaper=4.5;legendpaper=max(width(r[3],hpaper) for r in rows)+4
 if legendpaper>125:hpaper*=125/legendpaper;legendpaper=125
 columns=1
 # More than one A4 can be needed for very large part lists; keep labels legible.
 scale=min((190-legendpaper-6)/result['width'],277/result['height'],277/((len(rows)+3)*rowpaper))
 if sheet_width>0:scale=min(scale,190/sheet_width)
 if sheet_height>0:scale=min(scale,277/sheet_height)
 h=hpaper/scale;step=rowpaper/scale;legendx=result['width']+6/scale
 height=max(result['height'],(len(rows)+3)*step+10)
 contours=[];labels=[]
 contours+=text_contours('ДЕТАЛИ — РАЗМЕРЫ, ММ',legendx,height-step,h)
 contours+=text_contours('Ш × Д × Т; INFO НЕ ФРЕЗЕРОВАТЬ',legendx,height-2*step,h*.72)
 for i,(part,shape,ident,label) in enumerate(rows):
  x0,y0,x1,y1=shape.bounds;mh=min(h,(x1-x0)*.7/max(width(ident,1),1),(y1-y0)*.35)
  anchor=shape.representative_point();x=anchor.x-width(ident,mh)/2;y=anchor.y-mh/2
  # Shrink only the locator where the detail is tiny. The legend stays A4-readable.
  for attempt in range(12):
   if shape.covers(box(x,y,x+width(ident,mh),y+mh)):break
   mh*=.8;x=anchor.x-width(ident,mh)/2;y=anchor.y-mh/2
  contours+=text_contours(ident,x,y,mh)
  contours+=text_contours(label,legendx,height-(i+3)*step,h)
  labels.append(dict(part=part['name'],text=label,x=x,y=y,height=mh))
 result['cut_width']=result['width'];result['cut_height']=result['height']
 result['width']=legendx+legendpaper/scale+10;result['height']=height
 result['info']={'layer':'INFO','contours':contours,'labels':labels,'paper_text_height':hpaper,'a4_scale':scale,'note':'Габариты по внешнему контуру; мелкие номера уточняйте по таблице. Слой INFO не фрезеровать.'}
 return result
