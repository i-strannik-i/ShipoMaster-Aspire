"""Geometry and packaging checks for the migrated box generator."""
import unittest
import tempfile
from pathlib import Path
from itertools import combinations
from shapely.geometry import Polygon
from lupa import LuaRuntime
from geometry_worker import build, lua, write_dxf

def part_polygon(part):
    outer=next(c for c in part['contours'] if c['closed'] and not c['hole'])
    return Polygon(outer['points'],[c['points'] for c in part['contours'] if c['closed'] and c['hole']])

class GeometryTests(unittest.TestCase):
    def test_seven_modes_valid_closed_nonoverlapping_and_in_sheet(self):
        for mode in range(9):
            for count_mode in range(2):
                for cutter in (0,3):
                    with self.subTest(mode=mode,count_mode=count_mode,cutter=cutter):
                        r=build(dict(mode=mode,count_mode=count_mode,dFreza=cutter,
                            KolPeregorodokPoDline=2,KolPeregorodokPoShirine=1))
                        expected=8 if mode in (1,3) else 6 if mode in (4,7,8) else 1 if mode==6 else 5
                        self.assertEqual(len(r['parts']),expected)
                        shapes=[]
                        for p in r['parts']:
                            g=part_polygon(p);shapes.append(g)
                            self.assertTrue(g.is_valid)
                            self.assertGreater(g.area,1)
                            self.assertAlmostEqual(g.area,p['area'],places=3)
                            self.assertGreaterEqual(g.bounds[0],9.999)
                            self.assertGreaterEqual(g.bounds[1],9.999)
                            self.assertLessEqual(g.bounds[2],r['width']-9.999)
                            self.assertLessEqual(g.bounds[3],r['height']-9.999)
                            for c in p['contours']:
                                if c['closed']:self.assertEqual(c['points'][0],c['points'][-1])
                                else:self.assertEqual(len(c['points']),2)
                        for a,b in combinations(shapes,2):
                            self.assertLess(a.intersection(b).area,0.001)

    def test_units_dimensions_and_lid(self):
        r=build(dict(mode=4,dlinna=350,shirina=180,visota=120))
        bottom=next(p for p in r['parts'] if p['role']=='bottom')
        lid=next(p for p in r['parts'] if p['role']=='lid')
        self.assertAlmostEqual(bottom['area'],lid['area'])
        self.assertEqual(bottom['thickness'],9)
        self.assertEqual(lid['thickness'],9)
        a=part_polygon(bottom);b=part_polygon(lid)
        self.assertAlmostEqual(a.bounds[2]-a.bounds[0],350)
        self.assertAlmostEqual(b.bounds[3]-b.bounds[1],180)

    def test_bad_dimensions_rejected_before_any_output(self):
        for bad in ({'shirina':-1},{'Zazor':2},{'dFreza':12},
                    {'KolPoVisote':0},{'mode':9},{'mode':6,'RazmerPror':500},
                    {'mode':3,'KolPeregorodokPoDline':20,'dlinna':100}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):build(bad)

    def test_lua_data_and_native_script_parse(self):
        runtime=LuaRuntime(unpack_returned_tuples=True)
        result=build({})
        table=runtime.execute('return '+lua(result))
        self.assertTrue(table.ok)
        self.assertEqual(len(table.parts),5)
        script=Path(__file__).with_name('ShipoMaster_Aspire.lua')
        if not script.exists():script=Path(__file__).parent.parent/'ShipoMaster_Aspire.lua'
        runtime.execute(script.read_text(encoding='utf-8'))
        self.assertIsNotNone(runtime.globals().main)

    def test_dxf_mm_closed_flags_and_open_hinges(self):
        r=build({'mode':6})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.dxf';write_dxf(path,r['parts']);s=path.read_text()
            self.assertIn('$INSUNITS\n70\n4\n',s)
            self.assertIn('70\n1\n',s)
            self.assertIn('70\n0\n',s)
            self.assertTrue(s.endswith('0\nEOF\n'))

    def test_lid_mortises_mirror_bottom_mortises_in_all_four_walls(self):
        bottom_only=build({'mode':2})
        both=build({'mode':7})
        for lower,upper in zip(bottom_only['parts'],both['parts']):
            if lower['role']!='wall':continue
            old_holes=[c for c in lower['contours'] if c['hole']]
            new_holes=[c for c in upper['contours'] if c['hole']]
            self.assertEqual(len(new_holes),2*len(old_holes))
            g=part_polygon(upper)
            from shapely import affinity
            axis='x' if lower['name'].startswith(('001','005')) else 'y'
            center=((g.bounds[0]+g.bounds[2])/2,(g.bounds[1]+g.bounds[3])/2)
            holes=[Polygon(c['points']) for c in new_holes]
            for hole in holes:
                mirror=affinity.scale(hole,xfact=-1 if axis=='x' else 1,yfact=-1 if axis=='y' else 1,origin=center)
                self.assertLess(min(mirror.symmetric_difference(other).area for other in holes),0.001)
        self.assertEqual(sum(p['role']=='lid' for p in both['parts']),1)

    def test_curved_roof_radius_neutral_axis_and_flex_direction(self):
        from math import pi,asin,sqrt
        semi=build(dict(mode=8,dMaterial=4))
        self.assertAlmostEqual(semi['roof']['rise'],50)
        self.assertAlmostEqual(semi['roof']['developed_length'],52*pi)
        self.assertAlmostEqual(semi['roof']['roof_top_height'],154)
        self.assertAlmostEqual(semi['roof']['total_height'],162)
        lid=next(p for p in semi['parts'] if p['role']=='lid')
        g=part_polygon(lid)
        self.assertAlmostEqual(g.bounds[2]-g.bounds[0],200)
        self.assertAlmostEqual(g.bounds[3]-g.bounds[1],52*pi,places=5)
        cuts=[c for c in lid['contours'] if not c['closed']]
        self.assertGreater(len(cuts),10)
        for c in cuts:
            self.assertEqual(c['points'][0][1],c['points'][1][1])
            from shapely.geometry import LineString
            self.assertTrue(g.buffer(0.00001).covers(LineString(c['points'])))
        flat=build(dict(mode=8,dMaterial=4,radius_auto=False,RoofRadius=100))
        self.assertAlmostEqual(flat['roof']['rise'],100-sqrt(100**2-50**2))
        self.assertAlmostEqual(flat['roof']['developed_length'],102*2*asin(0.5))
        self.assertLess(flat['roof']['rise'],semi['roof']['rise'])
        solid=build(dict(mode=8,dMaterial=4,roof_hinge=False,roof_same=False,RoofThickness=2,dFreza=2))
        self.assertFalse(any(not c['closed'] for p in solid['parts'] for c in p['contours']))
        self.assertEqual(next(p['thickness'] for p in solid['parts'] if p['role']=='lid'),2)
        with self.assertRaises(ValueError):build(dict(mode=8,radius_auto=False,RoofRadius=49))

if __name__=='__main__':unittest.main()
