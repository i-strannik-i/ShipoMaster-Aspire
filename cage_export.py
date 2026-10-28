"""Dimensioned cage manufacturing documents; independent of legacy box DXF."""
from pathlib import Path
import csv
import json
import os


class Drawing:
    def __init__(self):
        self.items = []

    def line(self, x1, y1, x2, y2, layer='OUTLINE'):
        self.items.append(('line', layer, (x1, y1, x2, y2)))

    def rect(self, x, y, w, h, layer='OUTLINE'):
        for a, b in (((x,y),(x+w,y)), ((x+w,y),(x+w,y+h)),
                     ((x+w,y+h),(x,y+h)), ((x,y+h),(x,y))):
            self.line(*a, *b, layer)

    def text(self, x, y, text, size=4, layer='LABEL'):
        self.items.append(('text', layer, (x, y, str(text), size)))

    def circle(self, x, y, radius, layer='HOLES'):
        self.items.append(('circle', layer, (x, y, radius)))

    def dim(self, x1, y1, x2, y2, offset=12):
        """Orthogonal dimensions in mm; extension lines preserve actual geometry."""
        horizontal = abs(y1-y2) < 1e-7
        if horizontal:
            y = y1+offset
            self.line(x1,y1,x1,y+3,'DIM'); self.line(x2,y2,x2,y+3,'DIM')
            self.line(x1,y,x2,y,'DIM')
            for x in (x1,x2): self.line(x-2,y-2,x+2,y+2,'DIM')
            self.text((x1+x2)/2-6,y+2,f'{abs(x2-x1):.2f}',3.5,'DIM')
        else:
            x = x1+offset
            self.line(x1,y1,x+3,y1,'DIM'); self.line(x2,y2,x+3,y2,'DIM')
            self.line(x,y1,x,y2,'DIM')
            for y in (y1,y2): self.line(x-2,y-2,x+2,y+2,'DIM')
            self.text(x+3,(y1+y2)/2,f'{abs(y2-y1):.2f}',3.5,'DIM')

    def dxf(self, path):
        import ezdxf
        doc = ezdxf.new('R2010', setup=True)
        doc.units = 4
        doc.header['$MEASUREMENT'] = 1
        space = doc.modelspace()
        for layer, color in [('OUTLINE',7),('HOLES',1),('DIM',4),('LABEL',3)]:
            if layer not in doc.layers: doc.layers.new(layer, dxfattribs={'color':color})
        for kind, layer, args in self.items:
            attr = {'layer':layer}
            if kind == 'line': space.add_line(args[:2],args[2:],dxfattribs=attr)
            elif kind == 'circle': space.add_circle(args[:2],args[2],dxfattribs=attr)
            else:
                x,y,label,size = args
                space.add_text(label,dxfattribs={**attr,'height':size,'insert':(x,y)})
        doc.saveas(path)

    def pdf(self, canvas, x, y, width, height, font):
        # Text bounds are included so long tube labels cannot disappear at edges.
        bounds=[]
        for kind,_,a in self.items:
            if kind=='line':bounds.extend([a[:2],a[2:]])
            elif kind=='circle':bounds.extend([(a[0]-a[2],a[1]-a[2]),(a[0]+a[2],a[1]+a[2])])
            else:bounds.extend([(a[0],a[1]-a[3]*.3),(a[0]+len(a[2])*a[3]*.65,a[1]+a[3])])
        lowx=min(p[0] for p in bounds);lowy=min(p[1] for p in bounds)
        highx=max(p[0] for p in bounds);highy=max(p[1] for p in bounds)
        scale=min(width/(highx-lowx+10),height/(highy-lowy+10))
        bx=x+(width-(highx-lowx+10)*scale)/2
        by=y+(height-(highy-lowy+10)*scale)/2
        def point(px,py):return bx+5*scale+(px-lowx)*scale,by+5*scale+(py-lowy)*scale
        for kind,layer,a in self.items:
            canvas.setStrokeColorRGB(*({'HOLES':(.7,.1,.1),'DIM':(.1,.4,.55)}.get(layer,(.15,.2,.25))))
            canvas.setFillColorRGB(.15,.2,.25);canvas.setLineWidth(.55)
            if kind=='line':canvas.line(*point(*a[:2]),*point(*a[2:]))
            elif kind=='circle':canvas.circle(*point(*a[:2]),a[2]*scale,stroke=1,fill=0)
            else:
                canvas.setFont(font,max(6,min(11,a[3]*scale)))
                canvas.drawString(*point(*a[:2]),a[2])


def assembly_drawing(cage):
    d=Drawing();o=cage['options'];w=o['CageWidth'];depth=o['CageDepth'];h=o['CageHeight']
    a=o['CageTubeA'];b=o['CageTubeB'];spacing=max(100,w*.25)
    for label,axis,ox in [('FRONT','front',0),('SIDE','side',w+spacing)]:
        extent=w if axis=='front' else depth
        d.text(ox,h+40,label,8)
        for member in cage['members']:
            x,y,z=member['origin'];sx,sy,sz=member['size']
            px,pw=(x,sx) if axis=='front' else (y,sy)
            d.rect(ox+px,z,pw,sz)
            if member['role']==('rail_x' if axis=='front' else 'rail_y') or member['role']=='post':
                # Show front/right members only; rear duplicates share their types.
                if (axis=='front' and y==0) or (axis=='side' and x==0):
                    if member['role']=='post':
                        d.text(ox+(a+10 if px==0 else extent-a-100),h*.65,f'{member["id"]}/{member["tube_id"]}',8)
                    else:d.text(ox+px+pw/2,z+sz/2,f'{member["id"]}/{member["tube_id"]}',8)
        for z in cage['shelf_levels']:
            d.line(ox+a,z+o['CageShelfT'],ox+extent-a,z+o['CageShelfT'],'DIM')
        d.dim(ox,0,ox+extent,0,-25)
        d.dim(ox+extent,0,ox+extent,h,25)
        for z in cage['ring_tops'][1:-1]:
            d.text(ox+extent+50,z,f'Z={z:.2f}',4)
    tx=w+depth+2*spacing+150;oy=h-depth
    d.text(tx,oy+depth+40,'TOP / X,Y,Z in mm',8)
    d.rect(tx,oy,w,depth)
    for x in (0,w-a):
        for y in (0,depth-b):d.rect(tx+x,oy+y,a,b)
    d.rect(tx+a,oy,w-2*a,a);d.rect(tx+a,oy+depth-a,w-2*a,a)
    d.rect(tx,oy+b,a,depth-2*b);d.rect(tx+w-a,oy+b,a,depth-2*b)
    d.dim(tx,oy,tx+w,oy,-25);d.dim(tx+w,oy,tx+w,oy+depth,25)
    return d


def tube_drawing(tube, options):
    d=Drawing();length=tube['length'];a=options['CageTubeA'];b=options['CageTubeB'];wall=options['CageTubeWall']
    y=0
    for face,width in [('F1',a),('F2',b),('F3',a),('F4',b)]:
        faceholes=[hole for hole in tube['holes'] if face in hole['faces']]
        label=f'{face} / {tube["id"]}'
        if faceholes:label+=f' / Y={faceholes[0]["across"]:.2f} / D={faceholes[0]["diameter"]:g}'
        d.rect(0,y,length,width);d.text(0,y+width+7,label,5)
        for hole in tube['holes']:
            if face not in hole['faces']:continue
            d.circle(hole['along'],y+hole['across'],hole['diameter']/2)
            d.line(hole['along']-4,y+hole['across'],hole['along']+4,y+hole['across'],'DIM')
            d.text(hole['along']+4,y+hole['across']+2,
                   f'X={hole["along"]:.2f}',4)
        d.dim(0,y,length,y,-12)
        y+=width+100
    d.rect(0,y,a,b);d.rect(wall,y+wall,a-2*wall,b-2*wall)
    d.dim(0,y,a,y,-12);d.dim(a,y,a,y+b,15)
    d.text(a+45,y+8,f'{a:g} x {b:g} x {wall:g} / ends 90 deg',4)
    return d


def export_cage(result, destination):
    """Each run gets its own directory. Manifest and exports share the same model."""
    from datetime import datetime
    folder=Path(destination)
    if not folder.is_dir():raise ValueError('Выберите существующую папку для чертежей клетки.')
    folder=folder/('Cage_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir()
    cage=result['cage'];options=cage['options']
    from cage_pdf import write_cage_pdf
    write_cage_pdf(folder/'cage_drawings.pdf',result)
    if options.get('cage_pdf_only'):return str(folder)
    assembly_drawing(cage).dxf(folder/'frame_assembly.dxf')
    for tube in cage['tubes']:tube_drawing(tube,options).dxf(folder/f'{tube["id"]}_tube.dxf')
    with (folder/'tube_cutlist.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,delimiter=';');writer.writerow(['ID','A_mm','B_mm','Wall_mm','Length_mm','Qty','Ends_deg','Member_IDs'])
        for t in cage['tubes']:
            writer.writerow([t['id'],options['CageTubeA'],options['CageTubeB'],options['CageTubeWall'],t['length'],t['quantity'],90,','.join(t['members'])])
    for part in result['parts']:
        import ezdxf
        doc=ezdxf.new('R2010');doc.units=4;space=doc.modelspace()
        minx=min(x for c in part['contours'] for x,y in c['points'])
        miny=min(y for c in part['contours'] for x,y in c['points'])
        for contour in part['contours']:
            points=[(x-minx,y-miny) for x,y in contour['points'][:-1]]
            attr={'layer':contour.get('layer','CUT')}
            if contour.get('operation')=='drill':
                x0=min(p[0] for p in points);x1=max(p[0] for p in points)
                y0=min(p[1] for p in points);y1=max(p[1] for p in points)
                space.add_circle(((x0+x1)/2,(y0+y1)/2),(x1-x0)/2,dxfattribs=attr)
            else:space.add_lwpolyline(points,close=True,dxfattribs=attr)
        # Local coordinates make per-part machining independent of layout placement.
        doc.saveas(folder/f'{part["name"]}_{part["thickness"]:g}mm.dxf')
    (folder/'cage_model.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    with (folder/'panels.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,delimiter=';');writer.writerow(['ID','Role','Width_mm','Height_mm','Thickness_mm'])
        for p in result['parts']:writer.writerow([p['name'],p['role'],p['panel_width'],p['panel_height'],p['thickness']])
    with (folder/'hardware.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,delimiter=';');writer.writerow(['Part','Qty'])
        for item in cage['fasteners']:writer.writerow([item['name'],item['quantity']])
    return str(folder)
