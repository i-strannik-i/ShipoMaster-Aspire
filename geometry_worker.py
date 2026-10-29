"""Standalone geometry engine for ShipoMaster Aspire 1.5.5.

Adaptation of the supplied ShipoYashchik V2.01 formulas (Ulibka,
Superbizon, alleks67, May 2015). No Corel installation or VBA required.
"""
from pathlib import Path
from types import SimpleNamespace
from math import isfinite, ceil, pi, acos
from copy import deepcopy
import json
import sys
import traceback

from shapely import affinity, make_valid, set_precision
from shapely.geometry import Point, Polygon, LineString, box
import migrated_geometry as geom
from curved_roof import add_curved_roof
from joint_locks import locked_cut
from cutter_checks import CutterFitError,TOOLS,rectangular_cut_issue,check_flex_cuts

from version import VERSION
DEFAULTS = dict(mode=2, shirina=100, dlinna=200, visota=100, dFreza=4,
    dMaterial=9, DMaterialDna=9, Zazor=0.2, DlinaShipa=20,
    KolPoVisote=3, KolPoShirine=3, KolPoDlinne=3, count_mode=0,
    KolPeregorodokPoDline=0, KolPeregorodokPoShirine=0,
    TolshinaPeregorodok=9, VisotaPeregorodok=100, SmeshenieDno=8,
    SmeshenieKr=3, RazmerPror=100, ProrKolPoShirine=3,
    ProrMezduLin=10, ProrMezduParal=5, ProrRasstOtKraya=50,
    bottom_same=True, divider_same=True, height_same=True, centered=True,
    RoofRadius=50, RoofThickness=4, BendFactor=0.5,
    radius_auto=True, roof_same=True, roof_hinge=True,
    roof_mount=0, RoofInset=8, RoofOverhang=8,
    KerfRemaining=1, kerf_auto_remaining=True, KerfTolerance=0.2, KerfMinWeb=1,
    bottom_in_grooves=False, roof_cut_type=-1, joint_locks=True, LockInterference=0.1)

def polygons(g):
    if g.geom_type == 'Polygon':
        yield g
    elif hasattr(g, 'geoms'):
        for sub in g.geoms:
            yield from polygons(sub)

def lines(g):
    if g.geom_type == 'LineString':
        if g.length > 1e-6:
            yield g
    elif hasattr(g, 'geoms'):
        for sub in g.geoms:
            yield from lines(sub)

class Shape:
    def __init__(self, layer, geometry):
        self.layer, self.geometry, self.Name = layer, geometry, ''
        self.strokes = []
        self.stroke_settings = {}
        self.kind = ''
        layer.shapes.append(self)
        layer.selected = self

    @property
    def LeftX(self): return self.geometry.bounds[0]
    @property
    def BottomY(self): return self.geometry.bounds[1]
    @property
    def SizeWidth(self): return self.geometry.bounds[2] - self.LeftX
    @property
    def SizeHeight(self): return self.geometry.bounds[3] - self.BottomY

    def Rotate(self, degrees):
        center = ((self.LeftX+self.geometry.bounds[2])/2,
                  (self.BottomY+self.geometry.bounds[3])/2)
        self.geometry = affinity.rotate(self.geometry, degrees, origin=center)
        self.strokes = [affinity.rotate(g, degrees, origin=center) for g in self.strokes]

    def _combine(self, target, union=False):
        if not union and self.kind=='rectangle':
            issue=rectangular_cut_issue(self.geometry,target.geometry,self.layer.cutter)
            if issue:self.layer.cut_issues.append(issue)
        if self.geometry.geom_type == 'LineString':
            target.strokes.extend(lines(self.geometry.intersection(target.geometry)))
        else:
            target.geometry = make_valid(target.geometry.union(self.geometry) if union
                                         else target.geometry.difference(self.geometry))
        self.layer.shapes.remove(self)
        self.layer.selected = target
        if target.geometry.is_empty:
            raise ValueError('Параметры полностью удаляют одну из деталей. Увеличьте размеры или уменьшите шип/фрезу.')
        return target

    def Trim(self, target, *_): return self._combine(target)
    def Weld(self, target, *_): return self._combine(target, True)

class Layer:
    def __init__(self): self.shapes, self.selected = [], None;self.cutter=0;self.cut_issues=[]
    def CreateRectangle(self,x1,y1,x2,y2):
        shape=Shape(self,box(min(x1,x2),min(y1,y2),max(x1,x2),max(y1,y2)));shape.kind='rectangle';return shape
    def CreateLockedJoint(self,x0,y0,x1,y1,gap,interference,closed):
        target=self.selected
        if closed:
            issue=rectangular_cut_issue(box(x0,y0,x1,y1),target.geometry,self.cutter)
            if issue:raise CutterFitError([issue])
        cut=locked_cut(x0,y0,x1,y1,self.cutter,gap,interference,closed=closed)
        if closed and not target.geometry.buffer(1e-6).covers(cut):
            raise CutterFitError(['Разгрузки замков выходят за край детали или соседнего выреза. Увеличьте отступ/размеры детали или выберите меньшую фрезу.'])
        self.lock_count=getattr(self,'lock_count',0)+2
        target.lock_count=getattr(target,'lock_count',0)+2
        return Shape(self,cut)
    def CreateEllipse(self,x1,y1,x2,y2):
        rx,ry=abs(x2-x1)/2,abs(y2-y1)/2
        radius=max(rx,ry)
        # Circular chords differ from the source curve by no more than 0.001 mm.
        segs=max(24,ceil(pi/(4*acos(max(-1,1-0.001/max(radius,0.001))))))
        g=affinity.scale(Point(0,0).buffer(1,quad_segs=segs),rx,ry,origin=(0,0))
        return Shape(self,affinity.translate(g,(x1+x2)/2,(y1+y2)/2))
    def CreateEllipse2(self,x,y,r,ry=None,*_):
        ry=r if ry is None else ry
        return self.CreateEllipse(x-r,y-ry,x+r,y+ry)
    def CreateLineSegment(self,x1,y1,x2,y2):
        return Shape(self,LineString([(x1,y1),(x2,y2)]))

class Selection:
    def __init__(self,layer): self.layer=layer;self.Shapes=self
    @property
    def First(self): return self.layer.selected

def normalize(options):
    opts=DEFAULTS | options
    for key,default in DEFAULTS.items():
        if isinstance(default,bool):
            if isinstance(opts[key],str): opts[key]=opts[key].lower() in ('true','1')
        else:
            opts[key]=float(str(opts[key]).replace(',','.'))
            if not isfinite(opts[key]): raise ValueError('Числа должны быть конечными: '+key)
    if opts['bottom_same']:opts['DMaterialDna']=opts['dMaterial']
    if opts['divider_same']:opts['TolshinaPeregorodok']=opts['dMaterial']
    if opts['roof_same']:opts['RoofThickness']=opts['dMaterial']
    if opts['kerf_auto_remaining']:opts['KerfRemaining']=0.15*opts['RoofThickness']
    if opts['radius_auto']:opts['RoofRadius']=opts['shirina']/2
    if opts['height_same']:opts['VisotaPeregorodok']=opts['visota']
    if opts['centered']:opts['ProrRasstOtKraya']=(opts['dlinna']-opts['RazmerPror'])/2
    for key in ['mode','count_mode','roof_mount','roof_cut_type','KolPoVisote','KolPoShirine','KolPoDlinne',
                'KolPeregorodokPoDline','KolPeregorodokPoShirine','ProrKolPoShirine']:
        if opts[key]!=int(opts[key]):raise ValueError('Здесь требуется целое число: '+key)
        opts[key]=int(opts[key])
    if opts['mode'] not in range(9):raise ValueError('Неизвестный вид ящика.')
    if opts['count_mode'] not in (0,1):raise ValueError('Неизвестный режим пазов.')
    for key in ['shirina','dlinna','visota','dMaterial','DMaterialDna','DlinaShipa',
                'TolshinaPeregorodok','VisotaPeregorodok','ProrMezduParal','ProrMezduLin','RazmerPror']:
        if not 0 < opts[key] <= 10000:raise ValueError('Положительный размер до 10000 мм: '+key)
    if not 0<=opts['dFreza']<=100:
        raise ValueError('Диаметр фрезы должен быть от 0 до 100 мм.')
    if not 0<=opts['Zazor']<=1:raise ValueError('Зазор должен быть от 0 до 1 мм.')
    if not 0<opts['LockInterference']<=0.5:raise ValueError('Натяг замка на торец: больше 0 и не более 0.5 мм.')
    for key in ['KolPeregorodokPoDline','KolPeregorodokPoShirine']:
        if not 0<=opts[key]<=20:raise ValueError('Количество перегородок: от 0 до 20.')
    for key in ['KolPoVisote','KolPoShirine','KolPoDlinne','ProrKolPoShirine']:
        if not 1<=opts[key]<=100:raise ValueError('Количество пазов/прорезей: от 1 до 100.')
    if min(opts['shirina'],opts['dlinna'],opts['visota'])<=2*opts['dMaterial']:
        raise ValueError('Габариты должны быть больше двойной толщины стенок.')
    if (opts['mode'] in (2,3,7) or opts['mode']==8 and opts['bottom_in_grooves']) and not 0<opts['SmeshenieDno']<opts['visota']-opts['DMaterialDna']:
        raise ValueError('Смещение дна должно быть положительным и помещаться по высоте.')
    if opts['mode']==7 and opts['visota'] <= 2*(opts['SmeshenieDno']+opts['DMaterialDna']+opts['Zazor']+opts['dFreza']):
        raise ValueError('Пазы дна и крышки слишком близко: увеличьте высоту или уменьшите смещение.')
    if opts['mode'] in (1,3):
        for count,dim in [('KolPeregorodokPoDline','dlinna'),('KolPeregorodokPoShirine','shirina')]:
            if opts[count]*opts['TolshinaPeregorodok'] >= opts[dim]-2*opts['dMaterial']:
                raise ValueError('Перегородки не помещаются внутри ящика.')
        if opts['VisotaPeregorodok']>opts['visota']:raise ValueError('Перегородки выше стенок ящика.')
    if opts['mode'] in (5,6):
        if opts['SmeshenieKr']<0:raise ValueError('Припуск крышки не может быть отрицательным.')
        if opts['mode']==6 and not 0<=opts['ProrRasstOtKraya']<=opts['dlinna']-opts['RazmerPror']:
            raise ValueError('Область гибких прорезей выходит за край прямоугольника.')
        if (opts['ProrKolPoShirine']+1)*opts['ProrMezduLin'] >= opts['shirina']:
            raise ValueError('Перемычки занимают всю ширину. Уменьшите их количество или размер.')
        if opts['RazmerPror']/opts['ProrMezduParal']>1000:
            raise ValueError('Слишком много рядов прорезей (максимум 1000).')
    if opts['mode']==8:
        if opts['roof_cut_type'] not in (-1,0,1,2):
            raise ValueError('Неизвестный рисунок прорезей крыши.')
        if opts['roof_cut_type']==-1:
            opts['roof_cut_type']=2 if opts['roof_mount']==2 else 1 if opts['roof_hinge'] else 0
        if opts['roof_mount']==2:opts['roof_mount']=0  # Migrate the 1.3 combined selector.
        opts['roof_hinge']=opts['roof_cut_type']==1
        if opts['roof_mount'] not in (0,1,2):
            raise ValueError('Неизвестный вариант крепления крыши.')
        if opts['roof_mount'] in (0,2) and not max(2,opts['dFreza'])<=opts['RoofInset']<=100:
            raise ValueError('Перемычка над дуговым пазом: от диаметра фрезы (минимум 2) до 100 мм.')
        if opts['roof_mount']==1 and not max(2,opts['dFreza']+opts['Zazor'])<=opts['RoofOverhang']<=100:
            raise ValueError('Свес накладной крыши: не меньше диаметра фрезы плюс зазор (минимум 2), до 100 мм.')
        if not opts['shirina']/2<=opts['RoofRadius']<=10000:
            raise ValueError(f'Внутренний радиус крышки: от {opts["shirina"]/2:g} до 10000 мм.')
        if not 0<opts['RoofThickness']<=100 or not 0<=opts['BendFactor']<=1:
            raise ValueError('Толщина крышки должна быть положительной до 100 мм; K — от 0 до 1.')
        if opts['roof_cut_type']==2:
            if not 0<opts['KerfRemaining']<opts['RoofThickness']:
                raise ValueError('Остаточный слой должен быть больше нуля и меньше толщины крыши.')
            if not 0<opts['KerfTolerance']<=10 or not 0<opts['KerfMinWeb']<=100:
                raise ValueError('Допуск огранки: до 10 мм; минимальное ребро: до 100 мм; оба больше нуля.')
        if opts['roof_hinge'] and opts['roof_mount']!=2:
            available=opts['dlinna']-2*(opts['dMaterial']+max(2*opts['RoofThickness'],2*opts['dFreza']))
            if available <= (opts['ProrKolPoShirine']+1)*opts['ProrMezduLin']:
                raise ValueError('Прорези крышки не помещаются по длине: уменьшите перемычки/число сегментов или увеличьте длину.')
    return opts

def _build(options):
    opts=normalize(options)
    layer=Layer()
    layer.cutter=opts['dFreza']
    selection=Selection(layer)
    geom.F=SimpleNamespace(**opts,OptionButton1=opts['count_mode']==0,OptionButton2=opts['count_mode']==1)
    geom.mode=2 if opts['mode']==7 else (2 if opts['bottom_in_grooves'] else 0) if opts['mode']==8 else opts['mode']
    geom.DnoVPaz=geom.mode in (2,3)
    geom.DelatKrishku=geom.mode==4
    geom.DelatProrezi=geom.mode in (5,6)
    geom.DelatPeregorodki=geom.mode in (1,3)
    geom.Zazor_vokrug_kvadrata=10
    geom.ActiveLayer=layer
    geom.ActivePage=SimpleNamespace(SizeHeight=0,SizeWidth=0,ActiveLayer=layer)
    geom.ActiveDocument=SimpleNamespace(Selection=selection,SelectionRange=selection)
    geom.Application=SimpleNamespace(Documents=SimpleNamespace(Count=1))
    geom.CommandButton2_Click()
    roof_info=add_curved_roof(layer,opts,Shape) if opts['mode']==8 else None
    if layer.cut_issues:raise CutterFitError(layer.cut_issues)
    if opts['mode']==7:
        # Mode 2 has the matching bottom fingers and lower mortises already.
        # Reflect those mortises through each wall's mid-height for the lid.
        for index,s in enumerate(layer.shapes):
            if s.Name=='DNO':continue
            holes=[Polygon(r.coords) for p in polygons(s.geometry) for r in p.interiors]
            if not holes:raise ValueError('Не удалось построить внутренние пазы для крышки.')
            center=((s.geometry.bounds[0]+s.geometry.bounds[2])/2,
                    (s.geometry.bounds[1]+s.geometry.bounds[3])/2)
            for hole in holes:
                reflected=affinity.scale(hole,xfact=-1 if index in (0,4) else 1,
                                        yfact=1 if index in (0,4) else -1,origin=center)
                s.geometry=make_valid(s.geometry.difference(reflected))
            if opts['joint_locks']:s.lock_count=getattr(s,'lock_count',0)+2*len(holes)
    parts=[]
    for index,s in enumerate(layer.shapes):
        # Remove sub-micron tangencies before rounding contours for Aspire.
        # Otherwise adjoining round-tool envelopes can serialize as a crossing.
        s.geometry=set_precision(s.geometry,0.00001)
        role='arch_end' if s.Name=='ARCH_END' else 'roof_lock' if s.Name=='ROOF_LOCK' else 'lid' if s.Name=='ROOF' else 'bottom' if s.Name=='DNO' or opts['mode']==6 else 'divider' if s.Name=='Peregorodka' else 'wall'
        thickness=opts['RoofThickness'] if s.Name=='ROOF' else opts['DMaterialDna'] if role=='bottom' else opts['TolshinaPeregorodok'] if role=='divider' else opts['dMaterial']
        contours=[]
        for poly in polygons(s.geometry):
            if poly.area<1e-5:continue
            contours.append({'closed':True,'points':list(poly.exterior.coords),'hole':False})
            contours.extend({'closed':True,'points':list(r.coords),'hole':True} for r in poly.interiors)
        contours.extend({'closed':False,'points':list(g.coords),'hole':False,**s.stroke_settings} for stroke in s.strokes for g in lines(stroke))
        if not contours:raise ValueError('Пустая деталь. Проверьте размеры.')
        if len(list(polygons(s.geometry)))>1:
            raise CutterFitError(['Выбранные размеры пазов и разгрузок разделяют деталь на несвязанные куски.'])
        parts.append(dict(name=f'{index+1:03d}_{role}',role=role,thickness=thickness,contours=contours,area=s.geometry.area,joint_lock_count=getattr(s,'lock_count',0)))
    if opts['mode'] in (4,7):
        # The old macro made the upper joints but left duplicating the lid to the user.
        # Include that matching second bottom panel as an explicit sixth part.
        lid=deepcopy(next(p for p in parts if p['role']=='bottom'))
        lid['name']='006_lid';lid['role']='lid'
        lid['thickness']=opts['DMaterialDna']
        max_x=max(s.geometry.bounds[2] for s in layer.shapes)
        lid_shape=next(s for s in layer.shapes if s.Name=='DNO')
        shift=max_x+10-lid_shape.LeftX
        for contour in lid['contours']:
            contour['points']=[(x+shift,y) for x,y in contour['points']]
        parts.append(lid)
    if not parts:raise ValueError('Не создано ни одной детали.')
    coords=[xy for p in parts for c in p['contours'] for xy in c['points']]
    bounds=[min(p[0] for p in coords),min(p[1] for p in coords),max(p[0] for p in coords),max(p[1] for p in coords)]
    # Place every layout completely inside positive sheet coordinates, with a 10 mm margin.
    dx,dy=10-bounds[0],10-bounds[1]
    for part in parts:
        for contour in part['contours']:
            contour['points']=[[round(x+dx,6),round(y+dy,6)] for x,y in contour['points']]
    check_flex_cuts(layer,opts['dFreza'])
    return dict(ok=True,version=VERSION,options=opts,parts=parts,roof=roof_info,
                joint_lock_count=sum(p['joint_lock_count'] for p in parts),
                width=bounds[2]-bounds[0]+20,height=bounds[3]-bounds[1]+20,
                thickness=max(part['thickness'] for part in parts))

def build(options):
    if str(options.get('task','')).lower()=='cage':
        from cage_geometry import build_cage
        return build_cage(options)
    opts=normalize(options)
    try:return _build(opts)
    except CutterFitError as error:
        diameter=opts['dFreza'];alternatives=[]
        for tool in TOOLS:
            if tool==diameter:continue
            try:_build(opts|{'dFreza':tool});alternatives.append(tool)
            except ValueError:pass
        raise CutterFitError(error.issues,diameter,alternatives) from error

def lua(value):
    if value is None:return 'nil'
    if value is True:return 'true'
    if value is False:return 'false'
    if isinstance(value,(int,float)):return repr(value)
    if isinstance(value,str):return json.dumps(value,ensure_ascii=False)
    if isinstance(value,list):return '{'+','.join(lua(v) for v in value)+'}'
    return '{'+','.join('['+lua(str(k))+']='+lua(v) for k,v in value.items())+'}'

def write_dxf(path,parts):
    pairs=[(0,'SECTION'),(2,'HEADER'),(9,'$ACADVER'),(1,'AC1015'),(9,'$INSUNITS'),(70,4),(0,'ENDSEC'),(0,'SECTION'),(2,'ENTITIES')]
    for p in parts:
        for c in p['contours']:
            pts=c['points'][:-1] if c['closed'] else c['points']
            pairs.extend([(0,'LWPOLYLINE'),(8,c.get('layer',p['role'])), (90,len(pts)),(70,int(c['closed']))])
            for x,y in pts:pairs.extend([(10,x),(20,y)])
    pairs.extend([(0,'ENDSEC'),(0,'EOF')])
    Path(path).write_text(''.join(f'{code}\n{value}\n' for code,value in pairs),encoding='ascii')

def machining_instructions(result):
    kerf=(result.get('roof') or {}).get('kerf')
    if not kerf:return ''
    return (f'ШипоМастер Aspire {VERSION}: НЕСКВОЗНЫЕ ПРОПИЛЫ КРЫШИ\n'
        f'Обрабатывать ВНУТРЕННЮЮ сторону будущего изгиба.\n'
        f'Фактическая толщина крыши: {kerf["thickness"]:.4f} мм.\n'
        f'Глубина от обрабатываемой поверхности: {kerf["depth"]:.4f} мм.\n'
        f'Оставить непрорезанный НАРУЖНЫЙ слой: {kerf["remaining"]:.4f} мм.\n'
        f'Прямая пазовая фреза с плоским торцом: диаметр {kerf["cutter"]:g} мм.\n'
        f'Количество: {kerf["count"]}; шаг центров: {kerf["pitch"]:.4f} мм; ребро: {kerf["rib"]:.4f} мм.\n'
        f'Слой: {kerf["layer"]}\n'
        f'Траектория ПО ЦЕНТРАЛЬНЫМ ЛИНИЯМ. Start depth = 0; cut depth = {kerf["depth"]:.4f} мм.\n'
        'DXF хранит 2D-векторы и имя слоя; глубина не назначается автоматически.\n'
        'Не объединять этот слой со сквозными прорезями HINGE_CUTS.\n'
        'Внешний контур и соединительные пазы обрабатываются отдельно на полную толщину.\n'
        'Наружная сторона остаётся целой. Фанера: сохранить наружный слой шпона;\n'
        'автооценка 15% толщины — исходная настройка, а не расчёт прочности.\n'
        'Перед основной деталью проверить изгиб и остаточный слой на пробнике из того же листа.\n')


def main():
    request,output=map(Path,sys.argv[1:3])
    try:
        text=request.read_text(encoding='utf-8-sig')
        opts=dict(line.split('=',1) for line in text.splitlines() if '=' in line)
        export_dir=opts.pop('export_dir','')
        cage_export_dir=opts.pop('cage_export_dir','')
        if opts.get('task') in ('update_check','update_download'):
            from gadget_updates import check_update,download_update
            result=check_update(VERSION) if opts['task']=='update_check' else download_update(VERSION)
        else:
            result=build(opts)
            if opts.get('task')=='box_assembly':
                from box_assembly import build_box_assembly
                result=build_box_assembly(result)
            else:
                from layout_info import add_info
                add_info(result,float(opts.get('info_sheet_width',0)),float(opts.get('info_sheet_height',0)))
        if cage_export_dir:
            if not result.get('cage'):raise ValueError('Экспорт каркаса доступен только для клетки.')
            from cage_export import export_cage
            result['export_path']=export_cage(result,cage_export_dir)
            result['pdf_path']=str(Path(result['export_path'])/'cage_drawings.pdf')
        if export_dir:
            folder=Path(export_dir)
            if not folder.is_dir():raise ValueError('Папка экспорта не существует.')
            from datetime import datetime
            stamp=datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            for p in result['parts']:
                write_dxf(folder/f'ShipoMaster_{stamp}_{p["name"]}_{p["thickness"]:g}mm.dxf',[p])
            instructions=machining_instructions(result)
            if instructions:
                (folder/f'ShipoMaster_{stamp}_KERF_DEPTH.txt').write_text(instructions,encoding='utf-8-sig')
        output.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
    except Exception as e:
        result={'ok':False,'error':str(e)}
        if isinstance(e,CutterFitError):result.update(kind='cutter',cutter_options=e.alternatives)
        output.with_suffix('.log').write_text(traceback.format_exc(),encoding='utf-8')
    output.with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
    output.write_text('return '+lua(result),encoding='utf-8')

if __name__=='__main__':main()
