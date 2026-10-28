"""Geometric cutter access checks; no toolpath or material-strength claims."""
from shapely.strtree import STRtree

TOOLS=(2,3,4,6)

class CutterFitError(ValueError):
    def __init__(self,issues,diameter=None,alternatives=None):
        self.issues=list(dict.fromkeys(issues));self.diameter=diameter
        self.alternatives=[] if alternatives is None else alternatives
        message='\n'.join(self.issues[:4])
        if diameter is not None:
            message=f'Фреза {diameter:g} мм не подходит при текущих параметрах.\n'+message
            if self.alternatives:
                preferred=next(d for d in (4,3,2,6) if d in self.alternatives)
                message+='\nПодойдут из вашего набора: '+', '.join(f'{d:g}' for d in self.alternatives)+' мм.'
                message+=f'\nРекомендуется {preferred:g} мм. Выберите её кнопкой под полем диаметра и повторите расчёт.'
            else:
                message+='\nИз набора 2, 3, 4, 6 мм подходящей фрезы нет. Увеличьте ширину/шаг прорезей, уменьшите число пазов или измените размеры деталей.'
        super().__init__(message)

def rectangular_cut_issue(cut,target,diameter):
    if diameter<=0:return None
    x0,y0,x1,y1=cut.bounds;a,b,c,d=target.bounds;eps=1e-5
    if cut.intersection(target).area<eps:return None
    open_x=x0<=a+eps or x1>=c-eps
    open_y=y0<=b+eps or y1>=d-eps
    if open_x and open_y:return None  # Corner profiling, no enclosed channel.
    width=y1-y0 if open_x else x1-x0 if open_y else min(x1-x0,y1-y0)
    if width<diameter-1e-4:
        return f'Ширина '+('открытого выреза' if open_x or open_y else 'внутреннего паза')+f' {width:.2f} мм меньше диаметра фрезы {diameter:g} мм.'
    if not open_x and not open_y and width < diameter + 0.1 - 1e-6:
        return (f'Ширина внутреннего паза {width:.2f} мм: для внутреннего профиля '
                f'фрезой {diameter:g} мм нужен паз не уже {diameter+0.1:.2f} мм '
                '(запас по ширине 0.10 мм). Увеличьте зазор шип / паз '
                'или выберите меньшую фрезу.')
    return None

def check_flex_cuts(layer,diameter):
    if diameter<=0:return
    for part_index,shape in enumerate(layer.shapes):
        strokes=shape.strokes
        if len(strokes)<2:continue
        tree=STRtree(strokes)
        for index,line in enumerate(strokes):
            for candidate in tree.query(line.buffer(diameter+0.0001).envelope):
                other=int(candidate)
                if other<=index:continue
                if (getattr(shape,'stroke_settings',{}).get('operation')=='blind_kerf'
                    and abs(line.bounds[1]-strokes[other].bounds[1])<1e-6
                    and abs(line.bounds[3]-strokes[other].bounds[3])<1e-6):
                    # A through mortise can split one intentional kerf pass
                    # into collinear fragments; the gap is already empty.
                    continue
                distance=line.distance(strokes[other])
                if distance<=diameter+1e-4:
                    raise CutterFitError([f'Деталь {part_index+1}: расстояние между гибкими прорезями {distance:.2f} мм; фреза {diameter:g} мм объединит прорези и уберёт перемычку.'])
