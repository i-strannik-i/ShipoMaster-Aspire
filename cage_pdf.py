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
    d=Drawing();o=result['cage']['options'];w=o['CageWidth'];dep=o['CageDepth'];h=o['CageHeight']
    def project(x,y,z):return .866025403784*(x-y),z+.5*(x+y)
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
    d=Drawing();o=result['cage']['options'];c=result['cage'];w=o['CageWidth'];dep=o['CageDepth'];h=o['CageHeight']
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
    d=Drawing();c=result['cage'];o=result['cage']['options']
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
    from cage_drafting import write_cage_pdf as write
    return write(path,result)
