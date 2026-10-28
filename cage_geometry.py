"""Rectangular tube cage model. Coordinates: X width, Y depth, Z height, mm."""
from math import isfinite
from shapely.geometry import box, Point
from shapely import affinity
from version import VERSION

CAGE_DEFAULTS = dict(CageWidth=600,CageDepth=500,CageHeight=1000,
    CageTubeA=20,CageTubeB=30,CageTubeWall=1,CageSaw=3,
    CagePanelT=3,CageShelfT=6,CageDividerT=4,CageShelves=1,
    CagePartitions=0,CagePassage=80,
    CageTrayT=3,CageTrayHeight=40,CageGuide=12.5,CageClearance=2,
    CageShelfLevels='',CageBoltHole=5.5,CageScrewPilot=2.5,CageScrewDiameter=3.5,
    CageHoleEnd=20,CageBoltStagger=10,CagePlateT=3,CageVentDiameter=0,CageVentPitch=25,CageLayoutWidth=1500,
    CageInsertHole=7,CageInsertEnvelope=9,CageInsertDepth=10,CageInsertHead=1,CageInsertGripMin=.5,CageInsertGripMax=3,
    CageFastenerHeadHeight=5,CagePdfWidth=210,CagePdfHeight=297)


def normalize_cage(raw):
    opts={}
    for key,default in CAGE_DEFAULTS.items():
        value=raw.get(key,default)
        if isinstance(default,str):opts[key]=str(value);continue
        try:value=float(str(value).replace(',','.'))
        except (TypeError,ValueError):raise ValueError('Неверное число: '+key)
        if not isfinite(value):raise ValueError('Число должно быть конечным: '+key)
        opts[key]=value
    for key in ('CageShelves','CagePartitions'):
        if opts[key]!=int(opts[key]):raise ValueError('Требуется целое число: '+key)
        opts[key]=int(opts[key])
    for key in CAGE_DEFAULTS:
        if key in ('CageShelfLevels','CagePassage','CageShelves','CagePartitions','CageGuide','CageSaw','CageVentDiameter','CageFastenerHeadHeight'):continue
        if not 0<opts[key]<=10000:raise ValueError('Положительный размер до 10000 мм: '+key)
    for key in ('CagePassage','CageGuide','CageSaw','CageVentDiameter','CageFastenerHeadHeight'):
        if not 0<=opts[key]<=1000:raise ValueError('Размер от 0 до 1000 мм: '+key)
    if not 0<=opts['CageShelves']<=10 or not 0<=opts['CagePartitions']<=10:
        raise ValueError('Полок и перегородок: от 0 до 10.')
    if 2*opts['CageTubeWall']>=min(opts['CageTubeA'],opts['CageTubeB']):
        raise ValueError('Толщина стенки трубы должна быть меньше половины сечения.')
    if opts['CageTrayHeight']<=2*opts['CageTrayT']:
        raise ValueError('Лоток слишком низкий для указанной толщины.')
    opts['cage_self_tap']=str(raw.get('cage_self_tap',False)).lower() in ('true','1')
    opts['cage_pdf_only']=str(raw.get('cage_pdf_only',False)).lower() in ('true','1')
    if not (min(opts['CagePdfWidth'],opts['CagePdfHeight'])>=148 and
            210<=max(opts['CagePdfWidth'],opts['CagePdfHeight'])<=2000):
        raise ValueError('Лист PDF: не меньше А5 (148 x 210 мм), стороны до 2000 мм.')
    return opts


def build_cage(raw):
    o=normalize_cage(raw)
    W,D,H=(o[k] for k in ('CageWidth','CageDepth','CageHeight'))
    A,B=o['CageTubeA'],o['CageTubeB'];g=o['CageClearance']
    st,dt,pt=(o[k] for k in ('CageShelfT','CageDividerT','CagePanelT'))
    innerW,innerD=W-2*A,D-2*B
    floor=2*B+2*g+o['CageTrayHeight']
    floorTop=floor+st
    if min(innerW,innerD)<=max(4*g,2*o['CageTrayT']+2*o['CageGuide']+2*g):
        raise ValueError('Внутренний проём слишком мал для лотка и панелей.')
    if H-B-floorTop<=2*B+st+4*g:
        raise ValueError('Недостаточно высоты над лотком.')
    if o['CageShelfLevels'].strip():
        try:levels=[float(v.strip().replace(',','.')) for v in o['CageShelfLevels'].split(';')]
        except ValueError:raise ValueError('Высоты полок: числа в мм через точку с запятой.')
        if len(levels)!=o['CageShelves']:raise ValueError('Число высот должно совпадать с количеством полок.')
    else:levels=[floorTop+(H-B-floorTop)*i/(o['CageShelves']+1) for i in range(1,o['CageShelves']+1)]
    last=floorTop
    for level in levels:
        if not isfinite(level) or level-B<=last+2*g or level+st>=H-B-2*g:
            raise ValueError('Полки пересекают трубы, соседнюю полку или верхнюю обвязку. Высоты задавайте по возрастанию.')
        last=level+st
    tops=[B,floor,*levels,H]
    members=[]
    def member(role,origin,size,length):
        ident=f'M{len(members)+1:03d}'
        members.append(dict(id=ident,role=role,origin=list(origin),size=list(size),length=length,holes=[]))
    for x in (0,W-A):
        for y in (0,D-B):member('post',(x,y,0),(A,B,H),H)
    for top in tops:
        for y in (0,D-A):member('rail_x',(A,y,top-B),(innerW,A,B),innerW)
        for x in (0,W-A):member('rail_y',(x,B,top-B),(A,innerD,B),innerD)
    # Face codes are specified by the connector module before grouping/export.
    configure_connections(members,tops,o)
    groups={};tubes=[]
    for m in members:
        signature=(m['length'],tuple((tuple(h['faces']),h['along'],h['across'],h['diameter']) for h in m['holes']))
        if signature not in groups:
            tube=dict(id=f'T{len(tubes)+1:02d}',role=m['role'],length=m['length'],quantity=0,members=[],holes=m['holes'])
            groups[signature]=tube;tubes.append(tube)
        t=groups[signature];t['quantity']+=1;t['members'].append(m['id']);m['tube_id']=t['id']
    parts=[];cursor=10
    def panel(role,w,h,t,origin,axes,cutout=None,geometry=None,drill=False):
        nonlocal cursor
        if min(w,h)<=0:raise ValueError('Не помещается деталь: '+role)
        shape=geometry if geometry is not None else box(0,0,w,h)
        if role in ('side','back') and o['CageVentDiameter']>0:
            from shapely.ops import unary_union
            r=o['CageVentDiameter']/2;pitch=o['CageVentPitch'];margin=max(30,2*r+g)
            if pitch<2*r+max(2,g):raise ValueError('Шаг вентиляции слишком мал: отверстия сливаются.')
            nx=max(0,int((w-2*margin)/pitch)+1);ny=max(0,int((h-2*margin)/pitch)+1)
            if nx*ny>2500:raise ValueError('Более 2500 отверстий на панели. Увеличьте шаг вентиляции.')
            if nx==0 or ny==0:raise ValueError('Вентиляция не помещается в панели. Уменьшите отверстия.')
            holes=[Point(margin+i*pitch,margin+j*pitch).buffer(r,quad_segs=16) for i in range(nx) for j in range(ny)]
            shape=shape.difference(unary_union(holes))
        if cutout:
            cx,cy,r=cutout
            if min(cx-r,cy-r,w-cx-r,h-cy-r)<max(g,5):
                raise ValueError('Проход в полке слишком велик. Уменьшите его диаметр или число перегородок.')
            shape=shape.difference(Point(cx,cy).buffer(r,quad_segs=64))
        placed=affinity.translate(shape,cursor,10)
        contours=[dict(closed=True,hole=False,points=[list(p) for p in placed.exterior.coords])]
        contours.extend(dict(closed=True,hole=True,points=[list(p) for p in r.coords],
                             **({'layer':'CAGE_DRILL','operation':'drill'} if drill else {})) for r in placed.interiors)
        parts.append(dict(name=f'C{len(parts)+1:03d}_{role}',role=role,thickness=t,
            panel_width=w,panel_height=h,origin=list(origin),axes=axes,contours=contours,area=shape.area))
        cursor+=w+10
    add_enclosure_panels(panel,o,tops)
    # Floor is continuous; tray is underneath it, and is not a walking surface.
    def supported_outline(left,right):
        shape=box(0,0,right-left,D-2*g)
        # Corner clearances around the full-height posts; the remaining edges
        # overlap the ring, so the shelf really rests on the tube top faces.
        if left<A+g:
            for yy in (0,D-2*g-B):shape=shape.difference(box(0,yy,A+g-left,yy+B))
        if right>W-A-g:
            for yy in (0,D-2*g-B):shape=shape.difference(box(W-A-g-left,yy,right-left,yy+B))
        return shape
    panel('floor',W-2*g,D-2*g,st,(g,g,floor),'XY',geometry=supported_outline(g,W-g))
    n=o['CagePartitions'];divx=[A+innerW*i/(n+1) for i in range(1,n+1)]
    bounds=[g]+[v+dt/2+g for v in divx]
    ends=[v-dt/2-g for v in divx]+[W-g]
    for x in divx:panel('divider',innerD-2*g,H-B-g-floorTop,dt,(x-dt/2,B+g,floorTop),'YZ')
    for level in levels:
        for idx,(left,right) in enumerate(zip(bounds,ends)):
            w=right-left;dep=D-2*g;r=o['CagePassage']/2
            hole=(w/2,dep/2,r) if r>0 and idx==0 else None
            panel('shelf',w,dep,st,(left,g,level),'XY',hole,geometry=supported_outline(left,right))
    tt=o['CageTrayT'];tw=innerW-2*(g+o['CageGuide']);td=innerD-2*g;th=o['CageTrayHeight']
    tx=(W-tw)/2;ty=B+g;tz=B+g
    if min(tw,td)<=2*tt+2*g:raise ValueError('Стенки лотка занимают весь внутренний объём.')
    panel('tray_base',tw,td,tt,(tx,ty,tz),'XY')
    for y in (ty,ty+td-tt):panel('tray_front_back',tw,th-tt,tt,(tx,y,tz+tt),'XZ')
    for x in (tx,tx+tw-tt):panel('tray_side',td-2*tt,th-tt,tt,(x,ty+tt,tz+tt),'YZ')
    plates=add_connection_plates(panel,members,o)
    # Shelf packing, with separate bands per thickness. Never scale parts.
    layoutWidth=max(o['CageLayoutWidth'],max(p['panel_width'] for p in parts)+20)
    cx=cy=10;rowHeight=0;usedWidth=0;lastThickness=None
    for p in sorted(parts,key=lambda p:(-p['thickness'],-p['panel_height'])):
        if (lastThickness is not None and p['thickness']!=lastThickness) or cx+p['panel_width']+10>layoutWidth:
            cx=10;cy+=rowHeight+10;rowHeight=0
        lowx=min(x for c in p['contours'] for x,y in c['points'])
        lowy=min(y for c in p['contours'] for x,y in c['points'])
        for c in p['contours']:c['points']=[[round(x-lowx+cx,6),round(y-lowy+cy,6)] for x,y in c['points']]
        cx+=p['panel_width']+10;usedWidth=max(usedWidth,cx);rowHeight=max(rowHeight,p['panel_height']);lastThickness=p['thickness']
    net=sum(m['length'] for m in members);saw=len(members)*o['CageSaw']
    cage=dict(options=o,members=members,tubes=tubes,shelf_levels=levels,ring_tops=tops,
        net_tube_length=net,saw_allowance=saw,tube_with_saw=net+saw,
        tray=dict(width=tw,depth=td,height=th,origin=[tx,ty,tz],opening_height=th+2*g),
        connection_note=CONNECTION_NOTE,assembly_notes=assembly_notes(o),plates=plates,
        finished_size=[W+2*(panel_offset(o)+pt),D+2*(panel_offset(o)+pt),H+pt])
    cage['fasteners']=[dict(name='Self_tapping_screw' if o['cage_self_tap'] else 'M5_bolt',quantity=2*len(plates))]
    if not o['cage_self_tap']:cage['fasteners'].append(dict(name='M5_rivet_nut',quantity=2*len(plates)))
    return dict(ok=True,version=VERSION,options=o,parts=parts,cage=cage,roof=None,
        width=usedWidth,height=cy+rowHeight+10,
        thickness=max(p['thickness'] for p in parts),joint_lock_count=0)


CONNECTION_NOTE='Наружные плоские угловые накладки собственного чертежа; отверстия под покупные уголки могут отличаться.'
def configure_connections(members,tops,options):
    o=options;A=o['CageTubeA'];B=o['CageTubeB'];wall=o['CageTubeWall']
    diameter=o['CageScrewPilot'] if o['cage_self_tap'] else o['CageInsertHole']
    if o['cage_self_tap'] and o['CageScrewPilot']>=o['CageScrewDiameter']:
        raise ValueError('Сверло под саморез должно быть меньше его наружного диаметра.')
    if not o['cage_self_tap'] and o['CageBoltHole']<5.1:
        raise ValueError('Для М5 задайте проходное отверстие не меньше 5.1 мм.')
    if not o['cage_self_tap']:
        if not o['CageInsertGripMin']<=wall<=o['CageInsertGripMax']:
            raise ValueError('Толщина трубы вне диапазона обжатия заклёпочной гайки. Укажите параметры подходящей гайки.')
        if o['CageInsertEnvelope']<o['CageInsertHole']:
            raise ValueError('Габарит установленной гайки не может быть меньше посадочного отверстия.')
        depth=o['CageInsertDepth'];envelope=o['CageInsertEnvelope']
        if depth>=min(A,B)-wall-1:
            raise ValueError('Гайка/конец винта достаёт до противоположной стенки трубы. Уменьшите выступ или увеличьте профиль.')
        distance=(max(A/2-depth,0)**2+max(B/2-depth,0)**2+o['CageBoltStagger']**2)**.5
        if distance<envelope+0.5:
            raise ValueError('Габариты соседних заклёпочных гаек пересекаются. Увеличьте разнос осей или сечение трубы.')
    s=o['CageBoltStagger'];end=o['CageHoleEnd'];low=(B-s)/2;high=(B+s)/2
    if s<diameter+2*wall:
        raise ValueError('Разнос осей болтов должен быть не меньше диаметра отверстия + двух толщин стенки трубы.')
    if min(low-diameter/2,A/2-diameter/2)<max(2,2*wall):
        raise ValueError('Отверстия слишком близки к краю трубы. Увеличьте сечение или уменьшите разнос осей/диаметр.')
    if end-diameter/2<max(2*wall,2):raise ValueError('Увеличьте отступ отверстий от торца трубы.')
    for m in members:
        role=m['role'];x,y,z=m['origin']
        def hole(faces,along,across):
            m['holes'].append(dict(faces=faces,along=round(along,6),across=round(across,6),diameter=diameter,
                through=False))
        if role=='post':
            for top in tops:
                faces=['F1' if y==0 else 'F3']
                hole(faces,top-B+low,A/2)
                faces=['F4' if x==0 else 'F2']
                hole(faces,top-B+high,B/2)
        else:
            if m['length']<=2*end+diameter+2*wall:raise ValueError('Труба слишком короткая для двух торцевых отверстий.')
            faces=(['F2' if y==0 else 'F4'] if role=='rail_x' else ['F4' if x==0 else 'F2'])
            for at in (end,m['length']-end):hole(faces,at,high if role=='rail_x' else low)

def add_enclosure_panels(panel,options,tops):
    o=options;W=o['CageWidth'];D=o['CageDepth'];H=o['CageHeight'];pt=o['CagePanelT']
    g=o['CageClearance'];off=panel_offset(o)
    # Panels stand clear of the outer gussets. Their dimensions include corner seams.
    for x in (-off-pt,W+off):panel('side',D+2*off,H,pt,(x,-off,0),'YZ')
    panel('back',W+2*(off+pt),H,pt,(-off-pt,D+off,0),'XZ')
    panel('top',W+2*(off+pt),D+2*(off+pt),pt,(-off-pt,-off-pt,H),'XY')
    floor=tops[1]
    panel('front',W+2*(off+pt),H-floor-g,pt,(-off-pt,-off-pt,floor+g),'XZ')

def assembly_notes(options):
    o=options
    fastener=(f'Саморез: номинал {o["CageScrewDiameter"]:g}; сверло {o["CageScrewPilot"]:g} мм, только наружная стенка.'
              if o['cage_self_tap'] else f'М5 в заклёпочные гайки: труба D{o["CageInsertHole"]:g}; накладка D{o["CageBoltHole"]:g}. Только наружная стенка!')
    return [f'Каркас (без наружных панелей): {o["CageWidth"]:g} x {o["CageDepth"]:g} x {o["CageHeight"]:g} мм.',
        f'Стойки: A={o["CageTubeA"]:g} по X; B={o["CageTubeB"]:g} по Y. Горизонтальные трубы: B по Z.',
        'Наружные угловые накладки: собственная геометрия, не универсальный шаблон магазинного уголка.',
        fastener,
        f'Только наружная стенка: НЕ сверлить насквозь трубу. Посадочные параметры гайки проверяются по её чертежу.',
        f'Разнос осей двух направлений в стойке: {o["CageBoltStagger"]:g} мм.',
        f'Наружные панели: отступ от трубы {panel_offset(o):g} мм; учтены накладка, головка крепежа и зазор.',
        'Верхняя панель лежит на верхней рамке, Z=высота каркаса, без бокового отступа по высоте.',
        'Стойки сверлить от нижнего торца; торцы горизонтальных труб - прямые, 90 градусов.',
        'Панели снаружи через проставки; основание над лотком опирается на отдельную обвязку.',
        'Полки лежат на обвязках, углы обходят стойки; перегородки делят полки на отдельные детали.',
        'Отверстия направляющих и обшивки не назначены без размеров выбранной фурнитуры.',
        'Саморез и его сверло выбираются по фактическому крепежу; несущая способность здесь не рассчитывается.',
        'Расход: один рез на каждую заготовку; это не оптимизация раскроя хлыстов.']


def panel_offset(o):
    return o['CagePlateT']+o['CageFastenerHeadHeight']+o['CageClearance']+(0 if o['cage_self_tap'] else o['CageInsertHead'])


def add_connection_plates(panel,members,o):
    from shapely.ops import unary_union
    A=o['CageTubeA'];B=o['CageTubeB'];end=o['CageHoleEnd'];s=o['CageBoltStagger'];arm=min(A,B)-2
    clearance=o['CageScrewDiameter']+.3 if o['cage_self_tap'] else o['CageBoltHole']
    if clearance>=arm-4:raise ValueError('Недостаточно материала вокруг отверстий угловой накладки.')
    plates=[]
    for m in members:
        if m['role']=='post':continue
        axis=m['role']=='rail_x';postHalf=(A if axis else B)/2
        for endIndex in (0,1):
            x,y,z=m['origin']
            span=o['CageWidth'] if axis else o['CageDepth']
            postPos=postHalf if endIndex==0 else span-postHalf
            railPos=2*postHalf+end if endIndex==0 else span-2*postHalf-end
            pz=z+((B-s)/2 if axis else (B+s)/2)
            qz=z+((B+s)/2 if axis else (B-s)/2)
            shape=unary_union([box(postPos-arm/2,min(pz,qz)-arm/2,postPos+arm/2,max(pz,qz)+arm/2),
                               box(min(postPos,railPos)-arm/2,qz-arm/2,max(postPos,railPos)+arm/2,qz+arm/2)])
            for hx,hy in ((postPos,pz),(railPos,qz)):shape=shape.difference(Point(hx,hy).buffer(clearance/2,quad_segs=32))
            minx,miny,maxx,maxy=shape.bounds
            shape=affinity.translate(shape,-minx,-miny)
            if axis:
                head=0 if o['cage_self_tap'] else o['CageInsertHead']
                origin=[minx,-o['CagePlateT']-head if y==0 else o['CageDepth']+head,miny]
            else:
                head=0 if o['cage_self_tap'] else o['CageInsertHead']
                origin=[-o['CagePlateT']-head if x==0 else o['CageWidth']+head,minx,miny]
            panel('corner_plate_x' if axis else 'corner_plate_y',maxx-minx,maxy-miny,o['CagePlateT'],origin,'XZ' if axis else 'YZ',geometry=shape,drill=True)
            plates.append(dict(member=m['id'],end=endIndex,local_holes=[[postPos-minx,pz-miny],[railPos-minx,qz-miny]],diameter=clearance,
                               post_hole_z=pz,rail_hole_z=qz,part_name=None))
    return plates
