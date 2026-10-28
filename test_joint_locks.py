"""Round-tool envelopes and interference against actual generated mating fingers."""
import unittest
from types import SimpleNamespace
from shapely.geometry import box, LineString, Polygon
import migrated_geometry as geom
from geometry_worker import Layer, Selection, build
from joint_locks import locked_cut


class JointLockTests(unittest.TestCase):
    def test_swept_tool_leaves_only_two_local_contacts(self):
        for stock in (4,6,9):
            for cutter in (2,3,4):
                for gap in (.05,.2):
                    for press in (.05,.1,.2):
                        with self.subTest(stock=stock,cutter=cutter,gap=gap,press=press):
                            w=stock+2*gap
                            cut=locked_cut(0,-gap,w,20+gap,cutter,gap,press)
                            contact=box(gap,0,w-gap,20).difference(cut)
                            self.assertEqual(contact.geom_type,'MultiPolygon')
                            self.assertEqual(len(contact.geoms),2)
                            ends=sorted(contact.geoms,key=lambda p:p.centroid.y)
                            self.assertAlmostEqual(ends[0].bounds[3],press,delta=.001)
                            self.assertAlmostEqual(20-ends[1].bounds[1],press,delta=.001)
                            self.assertLess(box(gap,press+.001,w-gap,20-press-.001).difference(cut).area,1e-6)
                            swept=cut.buffer(-cutter/2,quad_segs=96).buffer(cutter/2,quad_segs=96)
                            self.assertLess(cut.symmetric_difference(swept).area,.015)
                            self.assertFalse(cut.interiors)

    def test_actual_finger_pitch_and_mortises_assemble_without_drift(self):
        for count in (3,6,9):
            for enabled in (False,True):
                layer=Layer();geom.ActiveLayer=layer
                geom.ActiveDocument=SimpleNamespace(Selection=Selection(layer))
                geom.F=SimpleNamespace(Zazor=.2,joint_locks=enabled,LockInterference=.1)
                geom.DelatProrezi=False;geom.DnoVPaz=True
                height=170;pitch=height/(2*count+1)
                layer.CreateRectangle(0,0,40,height)
                geom.ВставитьВырезСОднойСтороны(pitch,4,4,0,0,False,count=count)
                # Near the finger tip, away from the root reliefs.
                fingers=layer.selected.geometry.intersection(LineString([(.1,0),(.1,height)]))
                lengths=sorted(fingers.geoms,key=lambda line:line.bounds[1])
                self.assertEqual(len(lengths),count)
                receiver=Layer();receiver.cutter=4;geom.ActiveLayer=receiver
                geom.ActiveDocument=SimpleNamespace(Selection=Selection(receiver))
                receiver.CreateRectangle(0,0,40,height)
                geom.ВставитьШипСОднойСтороны(pitch,4,4,0,0,8,False,count=count)
                slots=sorted([Polygon(r) for r in receiver.selected.geometry.interiors],key=lambda p:p.centroid.y)
                self.assertEqual(len(slots),count)
                for i,line in enumerate(lengths):
                    lo,hi=line.bounds[1],line.bounds[3]
                    self.assertAlmostEqual(lo,pitch*(2*i+1),places=6)
                    self.assertAlmostEqual(hi,pitch*(2*i+2),places=6)
                    cut=slots[i]
                    overlap=box(8,lo,12,hi).difference(cut)
                    self.assertGreater(overlap.area,0) if enabled else self.assertEqual(overlap.area,0)
                    if enabled:
                        self.assertEqual(len(overlap.geoms),2)
                        self.assertLess(box(8,lo+.101,12,hi-.101).difference(cut).area,1e-6)

    def test_enabled_and_disabled_in_every_mode(self):
        for mode in range(9):
            for enabled in (False,True):
                result=build(dict(mode=mode,dMaterial=4,joint_locks=enabled))
                self.assertEqual(result['joint_lock_count']>0,enabled and mode!=6)

    def test_oversized_locks_and_reliefs_are_rejected(self):
        with self.assertRaises(ValueError):build(dict(LockInterference=1))
        with self.assertRaises(ValueError):
            build(dict(mode=2,dMaterial=4,SmeshenieDno=1,joint_locks=True))

    def test_divider_height_preserves_the_nominal_joint_span(self):
        # Fit clearance belongs on the receiving hole, never in the pitch span.
        for gap in (.05,.2,.5):
            result=build(dict(mode=3,visota=170,dMaterial=4,Zazor=gap,
                count_mode=1,KolPoVisote=6,KolPeregorodokPoDline=1,
                KolPeregorodokPoShirine=1,joint_locks=False))
            dividers=[p for p in result['parts'] if p['role']=='divider']
            widths=sorted(round(max(x for c in p['contours'] for x,y in c['points'])-
                                min(x for c in p['contours'] for x,y in c['points']),5) for p in dividers)
            self.assertEqual(widths,[158,162])


if __name__=='__main__':unittest.main()
