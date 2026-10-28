import unittest
from types import SimpleNamespace
from math import pi

import migrated_geometry as geom
from geometry_worker import Layer, Selection, build


class CalculationRegressions(unittest.TestCase):
    def test_requested_mortise_count_survives_fractional_pitch(self):
        # Test the primitive separately so corner joints cannot hide a lost slot.
        for count in (1, 3, 7, 20, 100):
            layer = Layer()
            geom.DelatProrezi = False
            geom.ActiveLayer = layer
            geom.ActiveDocument = SimpleNamespace(Selection=Selection(layer))
            geom.F = SimpleNamespace(Zazor=0,joint_locks=False)
            layer.CreateRectangle(0, 0, 200, 100)
            geom.ВставитьШипСОднойСтороны(
                100 / (2 * count + 1), 0, 4, 0, 0, 8, False, count=count)
            self.assertEqual(len(layer.selected.geometry.interiors), count)

    def test_length_mode_preserves_fractional_pitch(self):
        layer = Layer()
        geom.ActiveLayer = layer
        geom.ActiveDocument = SimpleNamespace(Selection=Selection(layer))
        geom.F = SimpleNamespace(Zazor=0,joint_locks=False)
        layer.CreateRectangle(0, 0, 200, 100)
        geom.ВставитьШипСОднойСтороны(16.7, 0, 4, 0, 0, 8, False)
        self.assertEqual(len(layer.selected.geometry.interiors), 2)

    def test_noninteger_flex_pitch_reaches_both_region_edges(self):
        result = build(dict(mode=6, RazmerPror=103, ProrMezduParal=6,
                            dFreza=0))
        strokes = [c for c in result['parts'][0]['contours'] if not c['closed']]
        xs = sorted(set(c['points'][0][0] for c in strokes))
        self.assertAlmostEqual(xs[-1] - xs[0], 103, places=5)
        self.assertLessEqual(max(b-a for a,b in zip(xs,xs[1:])), 6)

    def test_book_development_uses_full_pi(self):
        result = build(dict(mode=5, dFreza=0))
        bottom = next(p for p in result['parts'] if p['role']=='bottom')
        xs = [x for c in bottom['contours'] for x,y in c['points']]
        self.assertAlmostEqual(max(xs)-min(xs), 2*(200+3)+pi*(100-9)/2, places=5)

    def test_sheet_thickness_uses_only_generated_parts(self):
        result = build(dict(mode=6, dMaterial=4, divider_same=False,
                            TolshinaPeregorodok=80))
        self.assertEqual(result['thickness'], 4)


if __name__ == '__main__':
    unittest.main()
