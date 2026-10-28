"""Circular roof with captive end grooves or an overlay and removable keepers."""
from math import asin, acos, sqrt, cos, sin, pi, ceil
from shapely import affinity, make_valid
from shapely.geometry import Polygon, Point, LineString, box
from cutter_checks import CutterFitError
from kerf_bending import plan_kerfs


def relieved_rectangle(x0,y0,x1,y1,cutter):
    cut=box(x0,y0,x1,y1)
    r=cutter/2
    if r:
        d=r/sqrt(2)
        for x,sx in ((x0,1),(x1,-1)):
            for y,sy in ((y0,1),(y1,-1)):
                cut=cut.union(Point(x+sx*d,y+sy*d).buffer(r,quad_segs=64))
    return cut


def add_curved_roof(layer,opts,shape_factory):
    width,length,height=opts['shirina'],opts['dlinna'],opts['visota']
    radius,thickness,k=opts['RoofRadius'],opts['RoofThickness'],opts['BendFactor']
    wall=opts['dMaterial'];gap,cutter=opts['Zazor'],opts['dFreza']
    overlay=opts['roof_mount']==1
    alpha=asin(min(1,width/(2*radius)))
    angle=2*alpha;offset=sqrt(max(0,radius*radius-width*width/4))
    rise=radius-offset;neutral=radius+k*thickness;developed=neutral*angle
    kerf=None
    if opts['roof_cut_type']==2:
        kerf=plan_kerfs(radius,angle,thickness,cutter,opts['KerfRemaining'],
                        opts['KerfTolerance'],opts['KerfMinWeb'],k)
        neutral=kerf['neutral_radius'];developed=kerf['developed_length']
    count=int(opts['KolPoShirine']) if opts['count_mode']==1 else max(1,round((developed/opts['DlinaShipa']-1)/2))
    pitch=developed/(2*count+1);step=angle/(2*count+1)
    throat=2*radius*sin(step/2)
    if min(throat,pitch-2*gap)<cutter-0.0001:
        raise CutterFitError([f'У дугового соединения доступно {min(throat,pitch-2*gap):.2f} мм; фреза {cutter:g} мм не проходит. Уменьшите количество шипов или диаметр фрезы.'])
    if cutter>0 and not overlay and thickness+2*gap<cutter+0.1-1e-6:
        raise CutterFitError([f'Ширина закрытого дугового паза {thickness+2*gap:.2f} мм: для внутреннего профиля фрезой {cutter:g} мм нужно не менее {cutter+0.1:.2f} мм. Увеличьте зазор или выберите меньшую фрезу.'])
    web=max(2,cutter)
    key_width=min(2*wall,throat-2*web-2*gap)
    if cutter>0 and overlay and wall+2*gap<cutter+0.1-1e-6:
        raise CutterFitError([f'Отверстие фиксатора {wall+2*gap:.2f} мм: для внутреннего профиля фрезой {cutter:g} мм нужно не менее {cutter+0.1:.2f} мм. Увеличьте зазор или выберите меньшую фрезу.'])
    if overlay and key_width<cutter+2*gap:
        raise CutterFitError(['Шип слишком узкий для отверстия съёмного фиксатора и боковых перемычек. Уменьшите количество шипов по ширине или диаметр фрезы.'])
    post_extra=2*gap+wall+web
    outer_radius=radius+thickness+(post_extra if overlay else opts['RoofInset'])
    steps=max(64,ceil(angle/(2*acos(max(-1,1-0.0005/outer_radius)))))
    bands=[(-alpha+step*(2*i+1),-alpha+step*(2*i+2)) for i in range(count)]
    for index,sign in ((0,-1),(4,1)):
        shape=layer.shapes[index]
        spring=shape.LeftX if sign<0 else shape.geometry.bounds[2]
        middle=shape.BottomY+width/2
        def point(phi,r):
            return (spring+sign*(r*cos(phi)-offset),middle+r*sin(phi))
        def sector(lo,hi,inner,outer):
            n=max(8,ceil((hi-lo)*steps/angle))
            angles=[lo+(hi-lo)*j/n for j in range(n+1)]
            return Polygon([point(a,outer) for a in angles]+
                           [point(a,inner) for a in reversed(angles)])
        cap_radius=radius if overlay else outer_radius
        cap=Polygon([(spring-sign*0.002,middle-width/2)]+
                    [point(-alpha+angle*j/steps,cap_radius) for j in range(steps+1)]+
                    [(spring-sign*0.002,middle+width/2)])
        shape.geometry=shape.geometry.union(cap)
        if overlay:
            for lo,hi in bands:
                shape.geometry=shape.geometry.union(sector(lo,hi,radius-0.002,outer_radius))
            r=cutter/2;diagonal=r/sqrt(2)
            if r:
                for lo,hi in bands:
                    for phi,direction in ((lo,-1),(hi,1)):
                        x,y=point(phi,radius)
                        cx=x+diagonal*(sign*cos(phi)-direction*sign*sin(phi))
                        cy=y+diagonal*(sin(phi)+direction*cos(phi))
                        shape.geometry=shape.geometry.difference(Point(cx,cy).buffer(r,quad_segs=64))
            for lo,hi in bands:
                phi=(lo+hi)/2
                # A keeper passes axially through the post above the bent roof.
                center_radius=radius+thickness+gap+wall/2
                hole=relieved_rectangle(-key_width/2-gap,-wall/2-gap,
                                        key_width/2+gap,wall/2+gap,cutter)
                hole=affinity.affine_transform(hole,[
                    -sign*sin(phi),sign*cos(phi),cos(phi),sin(phi),
                    spring+sign*(center_radius*cos(phi)-offset),
                    middle+center_radius*sin(phi)])
                if not shape.geometry.contains(hole):
                    raise CutterFitError(['Отверстие фиксатора выходит за границы шипа торца. Уменьшите количество шипов или фрезу.'])
                shape.geometry=shape.geometry.difference(hole)
        else:
            for lo,hi in bands:
                # Closed mortises retain the tongues against radial springback.
                clearance=gap/neutral;lo-=clearance;hi+=clearance
                inner,outer=radius-gap,radius+thickness+gap
                cut=sector(lo,hi,inner,outer)
                r=cutter/2;diagonal=r/sqrt(2)
                if r:
                    for phi,tangent_sign in ((lo,1),(hi,-1)):
                        for radial,radial_sign in ((inner,1),(outer,-1)):
                            x,y=point(phi,radial)
                            cx=x+diagonal*(radial_sign*sign*cos(phi)-tangent_sign*sign*sin(phi))
                            cy=y+diagonal*(radial_sign*sin(phi)+tangent_sign*cos(phi))
                            cut=cut.union(Point(cx,cy).buffer(r,quad_segs=64))
                if not shape.geometry.contains(cut):
                    raise CutterFitError(['Дуговой паз открывается наружу. Увеличьте отступ крыши или уменьшите количество шипов/фрезу.'])
                shape.geometry=shape.geometry.difference(cut)
        shape.geometry=make_valid(shape.geometry);shape.Name='ARCH_END'

    overhang=opts['RoofOverhang'] if overlay else 0
    panel_length=length+2*overhang
    panel=box(0,0,panel_length,developed);depth=wall+gap
    if overlay:
        for lo,hi in bands:
            y0=(lo+alpha)*neutral-gap;y1=(hi+alpha)*neutral+gap
            for x0,x1 in ((overhang-gap,overhang+wall+gap),
                          (overhang+length-wall-gap,overhang+length+gap)):
                panel=panel.difference(relieved_rectangle(x0,y0,x1,y1,cutter))
    else:
        # Odd bands are tongues; even bands stop against the inner end faces.
        for j in range(count+1):
            y0=-1 if j==0 else 2*j*pitch
            y1=developed+1 if j==count else (2*j+1)*pitch
            for x0,x1 in ((-1,depth),(length-depth,length+1)):
                panel=panel.difference(relieved_rectangle(x0,y0,x1,y1,cutter))
    dx,dy=max(s.geometry.bounds[2] for s in layer.shapes)+10,10
    roof=shape_factory(layer,affinity.translate(make_valid(panel),dx,dy));roof.Name='ROOF'
    if kerf:
        roof.stroke_settings=dict(operation='blind_kerf',side='inside',
            depth=kerf['depth'],remaining=kerf['remaining'],cutter=cutter,layer=kerf['layer'])
        for row in range(kerf['count']):
            y=dy+(row+0.5)*kerf['pitch']
            clipped=LineString([(dx-1,y),(dx+panel_length+1,y)]).intersection(roof.geometry)
            if clipped.geom_type=='LineString':roof.strokes.append(clipped)
            elif hasattr(clipped,'geoms'):
                roof.strokes.extend(g for g in clipped.geoms if g.geom_type=='LineString' and g.length>0.001)
    elif opts['roof_hinge']:
        margin=max(2*thickness,2*cutter)
        start=overhang+wall+margin;end=overhang+length-wall-margin
        segments=opts['ProrKolPoShirine'];bridge=opts['ProrMezduLin']
        cut_length=(end-start-(segments+1)*bridge)/segments;pitch=cut_length+bridge
        if developed<=2*margin:raise ValueError('Мало места для гибких прорезей: уменьшите толщину крышки или отключите прорези.')
        rows=max(1,ceil((developed-2*margin)/opts['ProrMezduParal']))
        if rows>1000:raise ValueError('Слишком много рядов прорезей крышки: увеличьте шаг.')
        for row in range(rows+1):
            y=margin+(developed-2*margin)*row/rows
            for j in range(-1,segments+1):
                x=start+bridge+j*pitch+(pitch/2 if row%2 else 0)
                a,b=max(start+bridge,x),min(end-bridge,x+cut_length)
                if b>a+0.001:roof.strokes.append(LineString([(a+dx,y+dy),(b+dx,y+dy)]))
    if overlay:
        key_length=3*wall+2*web
        key_x=max(s.geometry.bounds[2] for s in layer.shapes)+10
        for index in range(2*count):
            key=shape_factory(layer,box(key_x,10+index*(key_width+10),
                                       key_x+key_length,10+index*(key_width+10)+key_width))
            key.Name='ROOF_LOCK'
    return dict(radius=radius,thickness=thickness,factor=k,angle_degrees=angle*180/pi,
                rise=rise,developed_length=developed,panel_length=panel_length,
                total_height=height+outer_radius-offset,roof_top_height=height+rise+thickness,
                tab_count=count,straight_height=height,mount='overlay' if overlay else 'inset',
                cut_pattern='blind_kerf' if kerf else 'through' if opts['roof_hinge'] else 'none',
                kerf=kerf,
                inset=0 if overlay else opts['RoofInset'],overhang=overhang,
                lock_count=2*count if overlay else 0,lock_thickness=wall if overlay else 0,
                lock_width=key_width if overlay else 0,lock_length=(3*wall+2*web) if overlay else 0,
                joints=[dict(start=(lo+alpha)*neutral,end=(hi+alpha)*neutral) for lo,hi in bands])
