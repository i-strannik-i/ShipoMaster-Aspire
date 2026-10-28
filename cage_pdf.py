"""One paginated manufacturing and assembly PDF; paper dimensions are user inputs."""
from pathlib import Path
import os
from xml.sax.saxutils import escape
from cage_export import Drawing, tube_drawing


def local_contours(part):
    x0=min(x for c in part['contours'] for x,y in c['points'])
    y0=min(y for c in part['contours'] for x,y in c['points'])
    return [[(x-x0,y-y0) for x,y in c['points']] for c in part['contours']]


def part_drawing(part):
    d=Drawing()
    for n,points in enumerate(local_contours(part)):
        for a,b in zip(points,points[1:]):d.line(*a,*b,'HOLES' if n else 'OUTLINE')
    w,h=part['panel_width'],part['panel_height']
    d.dim(0,0,w,0,-20);d.dim(w,0,w,h,20)
    return d


def world_point(part,u,v):
    x,y,z=part['origin']
    if part['axes']=='XY':return x+u,y+v,z
    if part['axes']=='XZ':return x+u,y,z+v
    return x,y+u,z+v


def assembly_iso(result,exploded=False):
    d=Drawing();o=result['options'];w=o['CageWidth'];dep=o['CageDepth'];h=o['CageHeight']
    def project(x,y,z):return x+.52*y,z+.30*y
    def segment(a,b,layer='OUTLINE'):d.line(*project(*a),*project(*b),layer)
    for m in result['cage']['members']:
        x,y,z=m['origin'];sx,sy,sz=m['size']
        vertices=[(x+i*sx,y+j*sy,z+k*sz) for i,j,k in ((0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1))]
        for a,b in ((0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)):segment(vertices[a],vertices[b])
    for p in result['parts']:
        if p['role'].startswith('corner_plate'):continue
        dx=dy=dz=0
        if exploded:
            if p['role']=='side':dx=(-1 if p['origin'][0]<0 else 1)*w*.45
            elif p['role']=='back':dy=dep*.7
            elif p['role']=='front':dy=-dep*.7
            elif p['role']=='top':dz=h*.35
            elif p['role'].startswith('tray'):dy=-dep*.85
        outer=local_contours(p)[0]
        points=[tuple(q+shift for q,shift in zip(world_point(p,u,v),(dx,dy,dz))) for u,v in outer]
        for a,b in zip(points,points[1:]):segment(a,b,'DIM')
        if exploded and (dx or dy or dz):
            center=world_point(p,p['panel_width']/2,p['panel_height']/2)
            displaced=(center[0]+dx,center[1]+dy,center[2]+dz)
            segment(center,displaced,'LABEL')
        else:displaced=world_point(p,p['panel_width']/2,p['panel_height']/2)
        if p['role'].startswith('tray') and p['role']!='tray_base':continue
        d.text(*project(*displaced),p['name'].split('_')[0],10)
    return d


def assembly_view(result,axis):
    d=Drawing();o=result['options'];c=result['cage'];w=o['CageWidth'];dep=o['CageDepth'];h=o['CageHeight']
    if axis=='top':
        for m in c['members']:
            x,y,z=m['origin'];sx,sy,sz=m['size'];d.rect(x,y,sx,sy)
        d.dim(0,0,w,0,-30);d.dim(w,0,w,dep,30)
        return d
    extent=w if axis=='front' else dep
    for m in c['members']:
        x,y,z=m['origin'];sx,sy,sz=m['size'];px,pw=(x,sx) if axis=='front' else (y,sy)
        d.rect(px,z,pw,sz)
        visible=(axis=='front' and y==0 and m['role']!='rail_y') or (axis=='side' and x==0 and m['role']!='rail_x')
        if visible:
            d.text(px+(30 if m['role']=='post' else pw/2),z+(sz*.65 if m['role']=='post' else sz/2),m['id']+'/'+m['tube_id'],7)
    for p in result['parts']:
        if p['role'] not in ('floor','shelf','divider','tray_base','tray_front_back','tray_side'):continue
        x,y,z=p['origin'];u,v=p['panel_width'],p['panel_height'];t=p['thickness']
        if p['axes']=='XY':sx,sy,sz=u,v,t
        elif p['axes']=='XZ':sx,sy,sz=u,t,v
        else:sx,sy,sz=t,u,v
        px,pw=(x,sx) if axis=='front' else (y,sy)
        d.rect(px,z,pw,sz,'DIM')
    d.dim(0,0,extent,0,-30);d.dim(extent,0,extent,h,30)
    for z in c['ring_tops'][1:-1]:d.text(extent+65,z,f'Z={z:.2f}',7)
    return d


def joint_drawing(result,role):
    d=Drawing();c=result['cage'];o=result['options']
    member=next(m for m in c['members'] if m['role']==role)
    pairs=zip(c['plates'],[p for p in result['parts'] if p['role'].startswith('corner_plate')])
    plate=next(p for connection,p in pairs if connection['member']==member['id'] and connection['end']==0)
    side=role=='rail_y';a=o['CageTubeB'] if side else o['CageTubeA'];b=o['CageTubeB']
    d.rect(0,0,a,b+45);d.rect(a,0,o['CageHoleEnd']+45,b)
    for i,contour in enumerate(local_contours(plate)):
        offset=(plate['origin'][1] if side else plate['origin'][0],plate['origin'][2])
        for p,q in zip(contour,contour[1:]):d.line(p[0]+offset[0],p[1]+offset[1],q[0]+offset[0],q[1]+offset[1],'HOLES' if i else 'DIM')
    d.dim(0,0,a,0,-15);d.dim(a,0,a+o['CageHoleEnd'],0,-30)
    lo=(b-o['CageBoltStagger'])/2;hi=(b+o['CageBoltStagger'])/2
    postz=hi if side else lo;railz=lo if side else hi
    d.text(0,b+55,f'{member["id"]}/{member["tube_id"]} + {plate["name"].split("_")[0]}',5)
    d.text(a+o['CageHoleEnd']+25,b+17,f'Post Z={postz:g}',3.5)
    d.text(a+o['CageHoleEnd']+25,b+27,f'Rail Z={railz:g}',3.5)
    return d


def write_cage_pdf(path,result):
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Flowable, KeepTogether
    from reportlab.lib.units import mm
    o=result['options'];c=result['cage'];pw=o['CagePdfWidth']*mm;ph=o['CagePdfHeight']*mm
    fontpath=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/'arial.ttf'
    pdfmetrics.registerFont(TTFont('CageFont',str(fontpath)))
    margin=14*mm;cw=pw-2*margin;ch=ph-2*margin-15
    doc=SimpleDocTemplate(str(path),pagesize=(pw,ph),leftMargin=margin,rightMargin=margin,
        topMargin=margin,bottomMargin=margin+15,title='Клетка - сборочные и рабочие чертежи',author='ШипоМастер Aspire')
    normal=ParagraphStyle('body',fontName='CageFont',fontSize=9,leading=12,spaceAfter=6)
    title=ParagraphStyle('heading',parent=normal,fontSize=15,leading=19,spaceAfter=9,textColor=HexColor('#214d66'))
    sub=ParagraphStyle('sub',parent=normal,fontSize=10,leading=13,textColor=HexColor('#466477'))
    story=[]
    roles={'side':'Боковая панель','back':'Задняя панель','front':'Передняя панель без двери','top':'Верхняя панель',
        'floor':'Основание над лотком','shelf':'Полка','divider':'Перегородка','tray_base':'Дно лотка','tray_side':'Борт лотка',
        'tray_front_back':'Передний / задний борт лотка','corner_plate_x':'Угловая накладка X','corner_plate_y':'Угловая накладка Y'}
    def para(text,style=normal):return Paragraph(escape(str(text)),style)
    def table(rows,widths=None):
        t=Table([[para(v) for v in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#e6eef3')),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('GRID',(0,0),(-1,-1),.3,HexColor('#bacbd5')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5)]))
        return t
    class Figure(Flowable):
        def __init__(self,drawing,height):super().__init__();self.drawing=drawing;self.width=cw;self.height=height
        def draw(self):self.drawing.pdf(self.canv,5,5,self.width-10,self.height-10,'CageFont')
    def page(heading,drawing=None,notes=()):
        if story:story.append(PageBreak())
        story.append(para(heading,title))
        wrapped=[para(n) for n in notes]
        reserved=45+sum(p.wrap(cw,ch)[1]+6 for p in wrapped)
        if drawing:story.append(Figure(drawing,max(70,ch-reserved-15)))
        story.extend(wrapped)
    page('Разборная клетка - сборочный чертёж',assembly_iso(result),[
        f'Каркас: ширина X {o["CageWidth"]:g}; длина Y {o["CageDepth"]:g}; высота Z {o["CageHeight"]:g} мм.',
        'Наружный габарит с обшивкой: '+' x '.join(f'{v:g}' for v in c['finished_size'])+' мм.',
        f'Лист {o["CagePdfWidth"]:g} x {o["CagePdfHeight"]:g} мм. Все размеры деталей - в мм. Масштаб изображений подобран по странице.',
        'Передняя панель цельная, без дверей. Cxxx - листовые детали; Mxxx - места труб; Txx - типы труб.'])
    page('Сборка - разнесённые наружные панели и лоток',assembly_iso(result,True),[
        'Панели показаны отнесёнными от каркаса; линии связывают детали с местом установки. Это схема сборки, а не изменение размеров.',
        'Сначала соберите каркас, установите основание, перегородки и полки; затем наружные панели и направляющие лотка.'])
    for axis,name in [('front','Вид спереди - каркас и внутренние детали'),('side','Вид слева - полки и лоток'),('top','Вид сверху - расположение стоек')]:
        page(name,assembly_view(result,axis),['Обшивка условно снята для видимости внутренних деталей. Z - высота верха опорной трубы от нижнего торца стойки.'])
    page('Уровни, лоток и расположение деталей')
    rows=[['Узел','Положение / размер, мм']]
    rows += [[f'Обвязка {i+1}',f'Верх Z={z:.2f}'] for i,z in enumerate(c['ring_tops'])]
    rows += [['Лоток, наружный размер',' x '.join(f'{c["tray"][k]:.2f}' for k in ('width','depth','height'))],
        ['Проём для лотка',f'Высота {c["tray"]["opening_height"]:.2f}'],['Место под направляющую',f'{o["CageGuide"]:g} с каждой стороны'],
        ['Монтажный зазор',f'{o["CageClearance"]:g} с каждой стороны']]
    story.append(table(rows,[cw*.4,cw*.6]))
    story.append(Spacer(1,12))
    story.append(para('Порядок сборки',sub))
    for text in ['1. Отрежьте трубы, промаркируйте M/T, просверлите указанные наружные грани.',
        '2. Для М5 установите заклёпочные гайки; соберите нижнюю обвязку и четыре стойки на накладках.',
        '3. Закрепите обвязку над лотком, промежуточные обвязки и верхнюю рамку; проверьте диагонали.',
        '4. Уложите основание и полки на трубы. Перегородки устанавливаются между секциями полок.',
        '5. Установите направляющие и собранный лоток, проверьте свободное выдвижение.',
        '6. Установите проставки, наружные панели и крышу. Передняя панель без петель.',
        'Отверстия под обшивку, перегородки и направляющие требуют размеров выбранной фурнитуры; они не назначены автоматически.']:
        story.append(para(text))
    for role,label in [('rail_x','Узел X - стойка, поперечина, угловая накладка'),('rail_y','Узел Y - стойка, поперечина, угловая накладка')]:
        page(label,joint_drawing(result,role),[
            c['connection_note'],
            f'Накладка {o["CagePlateT"]:g} мм. Разнос осей в стойке {o["CageBoltStagger"]:g} мм. Отступ от торца поперечины {o["CageHoleEnd"]:g} мм.',
            (f'Саморез {o["CageScrewDiameter"]:g}: отверстие трубы {o["CageScrewPilot"]:g} мм.' if o['cage_self_tap'] else
             f'М5: посадочное отверстие гайки в трубе {o["CageInsertHole"]:g}; проход в накладке {o["CageBoltHole"]:g} мм.'),
            'Сверлить только наружную стенку. Направления и координаты граней приведены на чертеже соответствующей трубы.'])
    page('Ведомость труб и крепежа')
    story.append(table([['Марка','Длина, мм','Кол-во','Места установки']]+[[t['id'],f'{t["length"]:.2f}',t['quantity'],', '.join(t['members'])] for t in c['tubes']],
                       [cw*.13,cw*.18,cw*.13,cw*.56]))
    story.extend([Spacer(1,12),para(f'Чистый расход {c["net_tube_length"]:.2f} мм; с резами {c["tube_with_saw"]:.2f} мм.'),
                  para(f'Накладки {len(c["plates"])} шт.; крепежей {2*len(c["plates"])} шт.')])
    page('Примечания к сборке и креплению')
    story.extend(para(s) for s in c['assembly_notes'])
    for t in c['tubes']:
        page(f'{t["id"]} - труба {o["CageTubeA"]:g} x {o["CageTubeB"]:g} x {o["CageTubeWall"]:g}',tube_drawing(t,o),[
            f'Длина {t["length"]:.2f} мм, количество {t["quantity"]}. Места: '+', '.join(t['members'])+'.',
            'F1/F3 - грань A; F2/F4 - грань B. X от маркированного торца; Y от нижнего края показанной грани. Противоположные грани - без зеркалирования.',
            {'post':'Стойка: F1 спереди (-Y), F3 сзади (+Y), F2 справа (+X), F4 слева (-X). Торец X=0 внизу.',
             'rail_x':'Поперечина X: F2 вперёд (-Y), F4 назад (+Y). Торец X=0 слева.',
             'rail_y':'Поперечина Y: F2 вправо (+X), F4 влево (-X). Торец X=0 спереди.'}[t['role']]])
    page('Ведомость листовых деталей')
    story.append(table([['Марка','Деталь','Размер, мм','Толщина']]+[[p['name'].split('_')[0],roles.get(p['role'],p['role']),f'{p["panel_width"]:.2f} x {p["panel_height"]:.2f}',f'{p["thickness"]:g}'] for p in result['parts']],
                       [cw*.13,cw*.32,cw*.38,cw*.17]))
    from shapely.geometry import Polygon
    groups=[]
    for p in result['parts']:
        contours=local_contours(p);shape=Polygon(contours[0],contours[1:])
        found=False
        for group in groups:
            if group[0][0]['role']==p['role'] and group[0][0]['thickness']==p['thickness'] and shape.equals_exact(group[1],.0001,normalize=True):
                group[0].append(p);found=True;break
        if not found:groups.append(([p],shape))
    for parts,_ in groups:
        p=parts[0];notes=[f'Марки: '+', '.join(q['name'].split('_')[0] for q in parts)+f'. Количество {len(parts)}.',
            f'Габарит {p["panel_width"]:.2f} x {p["panel_height"]:.2f}; толщина {p["thickness"]:g} мм.',
            'Контур показан со всеми вырезами. Размеры габаритные; внутренние отверстия не включать в наружную обрезку.']
        if p['role'].startswith('corner_plate'):
            notes.append('Круглые отверстия - сверление. Координаты центров от левого нижнего угла детали:')
            for contour in local_contours(p)[1:]:
                xs=[q[0] for q in contour];ys=[q[1] for q in contour]
                notes.append(f'X={(min(xs)+max(xs))/2:.2f}; Y={(min(ys)+max(ys))/2:.2f}; D={max(xs)-min(xs):.2f} мм.')
        if p['role'] in ('floor','shelf'):
            notes.append(f'Вырезы у стоек: сторона A={o["CageTubeA"]:g}, B={o["CageTubeB"]:g} мм; монтажный зазор {o["CageClearance"]:g} мм.')
            for contour in local_contours(p)[1:]:
                xs=[q[0] for q in contour];ys=[q[1] for q in contour]
                notes.append(f'Проход: центр X={(min(xs)+max(xs))/2:.2f}, Y={(min(ys)+max(ys))/2:.2f}; диаметр {max(xs)-min(xs):.2f} мм.')
        if p['role'] in ('side','back') and o['CageVentDiameter']>0:
            margin=max(30,o['CageVentDiameter']+o['CageClearance'])
            notes.append(f'Вентиляция: диаметр {o["CageVentDiameter"]:g}, шаг {o["CageVentPitch"]:g} мм; первый центр X=Y={margin:g} мм.')
        page(roles.get(p['role'],p['role']),part_drawing(p),notes)
    def footer(canvas,doc):
        canvas.setFont('CageFont',8);canvas.setFillColor(HexColor('#526b7d'))
        canvas.drawString(margin,20,'ШипоМастер | Все размеры в мм | Изображения не в масштабе 1:1')
        canvas.drawRightString(pw-margin,20,f'Лист {doc.page}')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
