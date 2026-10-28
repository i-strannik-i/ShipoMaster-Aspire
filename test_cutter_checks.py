import unittest
from shapely.geometry import Polygon, LineString
from geometry_worker import build
from cutter_checks import CutterFitError

class CutterChecksTests(unittest.TestCase):
    def rejection(self,options,expected):
        with self.assertRaises(CutterFitError) as caught:build(options)
        err=caught.exception
        self.assertEqual(err.alternatives,expected)
        for d in err.alternatives:build(options|{'dFreza':d})
        return str(err)

    def test_6mm_merges_5mm_flex_spacing_recommend_primary_4(self):
        message=self.rejection({'mode':6,'dFreza':6},[2,3,4])
        self.assertIn('5.00 мм',message)
        self.assertIn('Рекомендуется 4 мм',message)

    def test_narrower_spacing_requires_smaller_tool(self):
        message=self.rejection({'mode':6,'dFreza':4,'ProrMezduParal':3.5},[2,3])
        self.assertIn('Рекомендуется 3 мм',message)

    def test_no_candidate_preserves_zero_width_bridge(self):
        message=self.rejection({'mode':6,'dFreza':4,'ProrMezduParal':2},[])
        self.assertIn('подходящей фрезы нет',message)

    def test_closed_mortise_width_does_not_admit_6mm_tool(self):
        for mode in (2,3,7):
            with self.subTest(mode=mode):
                message=self.rejection({'mode':mode,'dMaterial':4,'dFreza':6},[2,3,4])
                self.assertIn('внутреннего паза 4.40',message)

    def test_equal_width_closed_slot_rejected_with_explanation(self):
        message=self.rejection({'mode':2,'dMaterial':4,'dFreza':4,'Zazor':0},[2,3])
        self.assertIn('не уже 4.10 мм',message)

    def test_roof_mounts_require_profile_clearance_too(self):
        for mount in (0,1):
            with self.subTest(mount=mount):
                with self.assertRaises(CutterFitError):
                    build(dict(mode=8,roof_mount=mount,dMaterial=4,dFreza=4,Zazor=0))

    def test_4mm_cutter_has_connected_passage_in_4_1mm_mortises(self):
        for mode in (2,3,7):
            with self.subTest(mode=mode):
                result=build(dict(mode=mode,dMaterial=4,dFreza=4,Zazor=.05,
                    KolPeregorodokPoDline=1,KolPeregorodokPoShirine=1))
                holes=[Polygon(c['points']) for p in result['parts']
                       for c in p['contours'] if c.get('hole')]
                self.assertTrue(holes)
                for hole in holes:
                    x0,y0,x1,y1=hole.bounds
                    x,y=(x0+x1)/2,(y0+y1)/2
                    section=(LineString([(x0-1,y),(x1+1,y)]) if x1-x0<y1-y0
                             else LineString([(x,y0-1),(x,y1+1)]))
                    self.assertAlmostEqual(hole.intersection(section).length,4.1,places=5)
                    centers=hole.buffer(-2)
                    self.assertEqual(centers.geom_type,'Polygon')
                    self.assertGreater(centers.area,0)

    def test_profile_tool_can_exceed_sheet_thickness(self):
        result=build({'mode':0,'dMaterial':4,'dFreza':6})
        self.assertEqual(len(result['parts']),5)

    def test_curved_lid_checks_flex_swept_width(self):
        self.rejection({'mode':8,'dMaterial':4,'dFreza':6},[2,3,4])

    def test_primary_4mm_valid_for_all_default_modes(self):
        for mode in range(9):
            with self.subTest(mode=mode):
                result=build({'mode':mode,'dMaterial':4,'dFreza':4})
                self.assertTrue(result['ok'])

if __name__=='__main__':unittest.main()
