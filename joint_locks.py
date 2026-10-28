"""Rounded sacrificial ribs, designed from an accessible cutter-centre region."""
from math import pi, sin, cos
from shapely.geometry import box, LineString, Point
from shapely.ops import unary_union
from cutter_checks import CutterFitError


def locked_cut(x0,y0,x1,y1,cutter,gap,interference,*,closed=True):
    # Y follows the mating finger. Crowns touch it at nominal end +/- natyg.
    radius=max(cutter/2,0.005)
    lo,hi=y0+gap+interference,y1-gap-interference
    if hi-lo < 2*radius+0.2:
        raise CutterFitError(['Для замков не хватает длины паза: уменьшите натяг или количество шипов.'])
    if closed and x1-x0 < 2*radius+0.1-1e-6:
        raise CutterFitError(['Замки: ширина паза должна превышать диаметр фрезы минимум на 0.10 мм.'])
    middle=(x0+x1)/2
    rib_radius=max(0.5,2*interference)
    stroke=0.025
    centers=box(x0+radius if closed else x0-2*radius-1,lo-radius,
                x1-radius,hi+radius)
    for cy,sign in ((lo-rib_radius,1),(hi+rib_radius,-1)):
        stem=(box(middle-rib_radius,lo-4*radius-10,middle+rib_radius,cy)
              if sign==1 else box(middle-rib_radius,cy,middle+rib_radius,hi+4*radius+10))
        rib=stem.union(Point(middle,cy).buffer(rib_radius,quad_segs=96))
        centers=centers.difference(rib.buffer(radius,quad_segs=96))
    paths=[centers]
    for cy,sign in ((lo-rib_radius,1),(hi+rib_radius,-1)):
        # The swept disc defines the reliefs and keeps each rib attached.
        orbit=radius+rib_radius+stroke
        arc=LineString([(middle+orbit*cos(pi*j/192),
                         cy+sign*orbit*sin(pi*j/192)) for j in range(193)])
        paths.append(arc.buffer(stroke,quad_segs=96))
    centers=unary_union(paths)
    cut=centers.buffer(radius,quad_segs=96)
    if cut.geom_type!='Polygon' or cut.interiors:
        raise CutterFitError(['Не удалось построить связные разгрузки замков. Измените размеры паза или диаметр фрезы.'])
    return cut.simplify(0.00001,preserve_topology=True)
