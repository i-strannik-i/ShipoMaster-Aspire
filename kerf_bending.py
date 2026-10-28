"""Geometric layout for blind, flat-ended kerfs; material strength is not inferred."""
from math import atan, acos, ceil, cos, tan
from cutter_checks import CutterFitError


def plan_kerfs(radius, angle, thickness, diameter, remaining, tolerance, min_web, factor):
    if diameter <= 0:
        raise ValueError('Для несквозных пропилов задайте реальный диаметр прямой пазовой фрезы больше нуля.')
    if not 0 < remaining < thickness:
        raise ValueError('Остаточный наружный слой должен быть больше нуля и меньше толщины крыши.')
    if tolerance <= 0 or min_web <= 0:
        raise ValueError('Допуск огранки и минимальная ширина ребра должны быть положительными.')
    depth = thickness - remaining
    # Only the uncut outer skin bends continuously. K applies to that skin,
    # rather than to the whole thickness interrupted by the grooves.
    neutral = radius + depth + factor * remaining
    developed = neutral * angle
    lever = neutral - radius
    max_rotation = 2 * atan(diameter / (2 * lever))
    facet_rotation = 2 * acos(max(-1, min(1, 1 - tolerance / neutral)))
    if facet_rotation <= 0:
        raise ValueError('Слишком мал допуск огранки для выбранного радиуса.')
    count = max(1, ceil(angle / min(max_rotation, facet_rotation)))
    if count > 1000:
        raise ValueError('Более 1000 несквозных пропилов: увеличьте допуск огранки.')
    pitch = developed / count
    rib = pitch - diameter
    if rib < min_web - 1e-6:
        raise CutterFitError([f'Между несквозными пропилами остаётся {rib:.2f} мм при минимуме {min_web:g} мм. Уменьшите фрезу или увеличьте допуск огранки.'])
    rotation = angle / count
    closure = 2 * lever * tan(rotation / 2)
    return dict(kind='blind_kerf', side='inside', depth=depth, remaining=remaining,
                thickness=thickness, cutter=diameter, neutral_radius=neutral,
                developed_length=developed, count=count, pitch=pitch, rib=rib,
                end_margin=rib/2, closure=closure, gap_after_bend=diameter-closure,
                facet_error=neutral*(1-cos(rotation/2)), tolerance=tolerance,
                layer=f'KERF_INSIDE_DEPTH_{depth:.4f}mm_REMAIN_{remaining:.4f}mm',
                depth_reference='from_inner_face', tool='flat_end_mill')
