"""Render the actual generated contours, rather than a schematic assembly."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
import sys


def main():
    canvas=Image.new('RGB',(1440,1060),'#f3f6fa')
    draw=ImageDraw.Draw(canvas)
    regular=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
    title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',30)
    def text(x,y,value,font=regular,color='#21384c'):
        draw.text((x,y),value,font=font,fill=color)
    text(35,20,'Изогнутая крыша: два варианта крепления',title)
    text(35,62,'Реальные контуры расчёта: 200 × 100 × 100 мм, материал 4 мм, R = 50 мм, фреза 4 мм.',small)
    if len(sys.argv)>1:
        results=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    else:
        from geometry_worker import build
        results=[build(dict(mode=8,roof_mount=m,dMaterial=4,count_mode=1)) for m in (0,1)]
    for mount in (0,1):
        top=110+mount*465
        result=results[mount]
        info=result['roof']
        text(35,top,('1. С отступом в закрытые пазы торцов' if mount==0 else
                     '2. Накладная: закрытые пазы + съёмные фиксаторы'),title)
        end=next(p for p in result['parts'] if p['role']=='arch_end')
        roof=next(p for p in result['parts'] if p['role']=='lid')
        for part,ox,oy,rotate,scale in ((end,70,top+65,True,1.85),
                                       (roof,475,top+60,False,1.85)):
            closed=[c for c in part['contours'] if c['closed']]
            allxy=[xy for c in closed for xy in c['points']]
            minx=min(p[0] for p in allxy);miny=min(p[1] for p in allxy)
            def mapped(points):
                return [((y-miny)*scale+ox,(x-minx)*scale+oy) if rotate else
                        ((x-minx)*scale+ox,(y-miny)*scale+oy) for x,y in points]
            for contour in closed:
                coords=mapped(contour['points'])
                draw.polygon(coords,fill='#2686b5' if contour['hole'] else '#e8c58a')
                draw.line(coords,fill='#36536b',width=2)
            for c in part['contours']:
                if not c['closed']:draw.line(mapped(c['points']),fill='#659bb1',width=1)
        text(65,top+390,'Торец (таких деталей две)',small)
        text(475,top+390,f'Развёртка крыши {info["panel_length"]:g} × {info["developed_length"]:.2f} мм',small)
        if mount==0:
            text(920,top+85,'Синие дуги — закрытые пазы.',small)
            text(920,top+120,'Шипы находятся на крышке.',small)
            text(920,top+155,'Над пазами остаётся материал:',small)
            text(920,top+185,'он не даёт крыше подняться.',small)
            text(920,top+235,'Собирать до установки',small)
            text(920,top+265,'второго торца.',small)
        else:
            text(920,top+85,'Синие пазы крыши надеваются',small)
            text(920,top+115,'на выступающие шипы торцов.',small)
            text(920,top+155,'В синие отверстия над крышей',small)
            text(920,top+185,'вставить фиксаторы ROOF_LOCK.',small)
            key=next(p for p in result['parts'] if p['role']=='roof_lock')
            points=key['contours'][0]['points']
            minx=min(x for x,y in points);miny=min(y for x,y in points)
            draw.polygon([(920+(x-minx)*4,top+245+(y-miny)*4) for x,y in points],
                         fill='#d48232',outline='#36536b',width=2)
            text(920,top+295,f'Фиксаторов: {info["lock_count"]}, толщина {info["lock_thickness"]:g} мм.',small)
    text(35,1030,'Синим показаны удаляемые области. Тонкие линии на крыше — отдельные прорези для изгиба.',small)
    output=Path('development/roof_mounts.png')
    output.parent.mkdir(exist_ok=True)
    canvas.save(output)
    print(output.resolve())


if __name__=='__main__':main()
