"""Draw a technical cross-section from the engine's exported JSON (Pillow)."""
from pathlib import Path
import json
import sys
from PIL import Image,ImageDraw,ImageFont


def main():
    result=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    plan=result['roof']['kerf']
    canvas=Image.new('RGB',(1240,740),'#f4f7fa');draw=ImageDraw.Draw(canvas)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',24)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
    heading=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',32)
    def text(x,y,label,f=font,color='#25465c'):draw.text((x,y),label,font=f,fill=color)
    text(40,25,'Третий вариант: несквозные пропилы',heading)
    text(40,77,f'Пример: крыша {plan["thickness"]:g} мм · фреза Ø{plan["cutter"]:g} мм · внутренний радиус {result["roof"]["radius"]:g} мм')
    text(40,135,'ВНУТРЕННЯЯ СТОРОНА — обрабатывать сверху ↓')
    left,top,width,height=40,190,680,200
    cut_height=height*plan['depth']/plan['thickness']
    cut_width=width*plan['cutter']/(6*plan['pitch'])
    draw.rectangle((left,top,left+width,top+height),fill='#d8b378',outline='#75532d',width=3)
    for i in range(6):
        x=left+(i+0.5)*width/6-cut_width/2
        draw.rectangle((x,top-2,x+cut_width,top+cut_height),fill='#e0edf6',outline='#337eaa',width=2)
    draw.line((750,top,750,top+cut_height),fill='#337eaa',width=3)
    for y in (top,top+cut_height,top+height):draw.line((740,y,760,y),fill='#337eaa',width=3)
    draw.line((750,top+cut_height,750,top+height),fill='#a66321',width=5)
    text(785,215,'ГЛУБИНА',heading)
    text(785,260,f'{plan["depth"]:.3f} мм',heading,color='#23779d')
    text(785,330,'ОСТАВИТЬ СНАРУЖИ',small)
    text(785,365,f'{plan["remaining"]:.3f} мм',heading,color='#a66321')
    text(40,415,'НАРУЖНАЯ СТОРОНА — оставить целой')
    text(40,470,f'Шаг центров: {plan["pitch"]:.3f} мм · ребро: {plan["rib"]:.3f} мм · всего {plan["count"]} пропилов')
    text(40,515,'Глубина = толщина крыши − оставленный наружный слой',small)
    text(40,555,plan['layer'],small,color='#23779d')
    text(40,595,'Линии фрезеровать по центру; DXF не назначает глубину автоматически.',small)
    text(40,630,'Автооценка остатка 15% — настройка для пробника. Можно задать остаток вручную.',small)
    text(40,680,'«Дно в пазы» выбирается отдельно на вкладке «Параметры», вместе с отступом дна.',small)
    output=Path('development/kerf_depth.png');canvas.save(output);print(output.resolve())


if __name__=='__main__':main()
