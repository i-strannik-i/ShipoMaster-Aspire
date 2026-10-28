"""Repeatable geometry audit; writes machine-readable results for every case."""
import json
from itertools import product, combinations
from pathlib import Path
from shapely.geometry import Polygon, LineString
from geometry_worker import build
from cutter_checks import CutterFitError


def verify(result):
    shapes = []
    for part in result['parts']:
        outer = [c for c in part['contours'] if c['closed'] and not c['hole']]
        assert len(outer) == 1
        shape = Polygon(outer[0]['points'],
                        [c['points'] for c in part['contours'] if c['hole']])
        assert shape.is_valid and shape.area > 0
        assert abs(shape.area-part['area']) < 0.01
        x0,y0,x1,y1 = shape.bounds
        assert x0 >= 9.999 and y0 >= 9.999
        assert x1 <= result['width']-9.999 and y1 <= result['height']-9.999
        for c in part['contours']:
            if c['closed']:
                assert c['points'][0] == c['points'][-1]
            else:
                assert shape.buffer(0.00001).covers(LineString(c['points']))
        shapes.append(shape)
    for a,b in combinations(shapes,2):
        assert a.intersection(b).area < 0.001, 'Overlapping parts'


def main():
    cases=[]
    combinations_to_run=list(product(range(8),range(2),(4,6,9),(0,2,3,4,6),(0,),(False,)))
    combinations_to_run+=list(product((8,),range(2),(4,6,9),(0,2,3,4,6),range(3),(False,True)))
    for mode,count_mode,material,cutter,mount,bottom in combinations_to_run:
        if mount==2 and cutter==0:continue  # A real kerf width is mandatory.
        options=dict(mode=mode,roof_mount=mount,bottom_in_grooves=bottom,count_mode=count_mode,dMaterial=material,dFreza=cutter,
                     shirina=180,dlinna=320,visota=140,
                     KolPeregorodokPoDline=2,KolPeregorodokPoShirine=1)
        case=dict(options=options)
        try:
            result=build(options)
            verify(result)
            case.update(status='ok',parts=len(result['parts']))
        except CutterFitError as error:
            case.update(status='rejected',reason=str(error),alternatives=error.alternatives)
        except Exception as error:
            case.update(status='FAILED',reason=repr(error))
        cases.append(case)
        if len(cases)%30==0: print(f'{len(cases)}/408',flush=True)
    output=Path('development/verification_matrix.json')
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
    counts={s:sum(c['status']==s for c in cases) for s in ('ok','rejected','FAILED')}
    print(counts,flush=True)
    for c in cases:
        if c['status']=='FAILED':print(c,flush=True)
    assert not counts['FAILED']


if __name__=='__main__':main()
