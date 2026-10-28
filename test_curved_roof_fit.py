"""Assembly checks for both retained roof mountings, independent of the preview."""
from math import asin, cos, sin, sqrt
import unittest
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from curved_roof import add_curved_roof
from geometry_worker import Layer, Shape, normalize, build
from cutter_checks import CutterFitError


class CurvedRoofFitTests(unittest.TestCase):
    def fixture(self, **options):
        opts=normalize(dict(mode=8,dMaterial=6,roof_same=False,RoofThickness=4,
                            roof_hinge=False,radius_auto=False,count_mode=1)|options)
        layer=Layer()
        for i in range(5):layer.CreateRectangle(i*300,0,i*300+100,100)
        info=add_curved_roof(layer,opts,Shape)
        return opts,layer,info

    def test_round_tool_does_not_block_either_mount_and_inset_resists_lift(self):
        for mount in (0,1):
            for radius in (50,100):
                for cutter in (2,3,4):
                    for factor in (0,0.5,1):
                        with self.subTest(mount=mount,radius=radius,cutter=cutter,factor=factor):
                            opts,layer,info=self.fixture(roof_mount=mount,
                                RoofRadius=radius,dFreza=cutter,BendFactor=factor)
                            alpha=asin(50/radius);offset=sqrt(radius**2-50**2)
                            count=opts['KolPoShirine'];step=2*alpha/(2*count+1)
                            agap=opts['Zazor']/(radius+factor*4)
                            for index,sign,spring in ((0,-1,0),(4,1,1300)):
                                def point(phi,r):
                                    return (spring+sign*(r*cos(phi)-offset),50+r*sin(phi))
                                def sector(a,b,lift=0):
                                    angles=[a+(b-a)*j/100 for j in range(101)]
                                    return Polygon([point(a,radius+4+lift) for a in angles]+
                                        [point(a,radius+0.002+lift) for a in reversed(angles)])
                                intervals=[(-alpha+step*(2*j+1),-alpha+step*(2*j+2))
                                           for j in range(count)] if mount==0 else [
                                    (-alpha+2*j*step+(agap if j else 0),
                                     -alpha+(2*j+1)*step-(agap if j<count else 0))
                                    for j in range(count+1)]
                                material=unary_union([sector(a,b) for a,b in intervals])
                                end=layer.shapes[index].geometry
                                machined=end.buffer(cutter/2,quad_segs=96).buffer(
                                    -cutter/2,quad_segs=96)
                                self.assertLess(machined.intersection(material).area,0.003)
                                self.assertEqual(end.geom_type,'Polygon')
                                self.assertEqual(len(end.interiors),count)
                                if mount==0:
                                    lifted=unary_union([sector(a,b,2) for a,b in intervals])
                                    self.assertGreater(end.intersection(lifted).area,1)
                                else:
                                    # Keepers sit above the roof and overlap it
                                    # when the roof tries to move radially out.
                                    phi=-alpha+1.5*step
                                    kw=info['lock_width'];kr=radius+4+opts['Zazor']
                                    def local(x,y):
                                        px,py=point(phi,kr)
                                        return (px-x*sign*sin(phi)+y*sign*cos(phi),
                                                py+x*cos(phi)+y*sin(phi))
                                    keeper=Polygon([local(-kw/2,0),local(kw/2,0),
                                                    local(kw/2,6),local(-kw/2,6)])
                                    lifted=sector(phi-step/4,phi+step/4,2)
                                    self.assertGreater(keeper.intersection(lifted).area,1)

    def test_inset_tongues_and_overlay_closed_mortises_match_arc_bands(self):
        for mount in (0,1):
            opts,layer,info=self.fixture(RoofRadius=100,dFreza=4,roof_mount=mount)
            panel=next(s.geometry for s in layer.shapes if s.Name=='ROOF')
            x0,y0,x1,y1=panel.bounds
            pitch=info['developed_length']/(2*info['tab_count']+1)
            depth=opts['dMaterial']+opts['Zazor']
            for j in range(2*info['tab_count']+1):
                y=y0+(j+0.5)*pitch
                for x in (x0+info['overhang']+depth/2,x1-info['overhang']-depth/2):
                    self.assertEqual(panel.covers(Point(x,y)),j%2==(1 if mount==0 else 0))
                self.assertTrue(panel.covers(Point((x0+x1)/2,y)))
            self.assertEqual(len(panel.interiors),2*info['tab_count'] if mount else 0)
            self.assertAlmostEqual(x1-x0,info['panel_length'])
            self.assertAlmostEqual(y1-y0,info['developed_length'])
            self.assertEqual(sum(s.Name=='ROOF_LOCK' for s in layer.shapes),info['lock_count'])

    def test_both_mounts_export_identified_parts_and_materials(self):
        for mount in (0,1):
            result=build(dict(mode=8,dMaterial=4,roof_mount=mount))
            self.assertEqual(sum(p['role']=='arch_end' for p in result['parts']),2)
            locks=[p for p in result['parts'] if p['role']=='roof_lock']
            self.assertEqual(len(locks),result['roof']['lock_count'])
            self.assertTrue(all(p['thickness']==4 for p in locks))

    def test_tool_must_fit_captive_groove_or_keeper_hole(self):
        for mount in (0,1):
            with self.assertRaises(CutterFitError):
                build(dict(mode=8,dMaterial=4,dFreza=6,roof_mount=mount,roof_hinge=False))
        for options in ({'RoofInset':1},{'roof_mount':1,'RoofOverhang':1},{'roof_mount':3}):
            with self.assertRaises(ValueError):build(dict(mode=8)|options)


if __name__=='__main__':unittest.main()
