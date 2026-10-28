from math import pi
from pathlib import Path
from itertools import product
import re
import tempfile
import unittest
import json
import shutil
import subprocess
from geometry_worker import build,normalize,write_dxf,machining_instructions
from kerf_bending import plan_kerfs
from cutter_checks import CutterFitError
from verify_all_modes import verify


class BlindKerfTests(unittest.TestCase):
    def test_depth_is_based_on_roof_stock_and_remaining_skin(self):
        for thickness,remaining in ((4,0.6),(9,1.35),(18,2.7)):
            result=build(dict(mode=8,roof_mount=2,roof_same=False,
                              RoofThickness=thickness,dMaterial=4))
            plan=result['roof']['kerf']
            self.assertAlmostEqual(plan['remaining'],remaining)
            self.assertAlmostEqual(plan['depth'],thickness-remaining)
            self.assertAlmostEqual(plan['neutral_radius'],50+thickness-remaining/2)

    def test_manual_remaining_skin_overrides_suggestion(self):
        result=build(dict(mode=8,roof_mount=2,dMaterial=9,
                          kerf_auto_remaining=False,KerfRemaining=1.1))
        self.assertAlmostEqual(result['roof']['kerf']['depth'],7.9)
        self.assertAlmostEqual(result['roof']['kerf']['remaining'],1.1)

    def test_geometry_constraints_for_thickness_radius_and_tool_matrix(self):
        for thickness,radius,cutter in product((4,9,18),(50,85,150),(0.5,2,3,4,6)):
            with self.subTest(thickness=thickness,radius=radius,cutter=cutter):
                plan=plan_kerfs(radius,pi,thickness,cutter,0.15*thickness,0.2,1,0.5)
                self.assertLessEqual(plan['closure'],cutter+1e-9)
                self.assertLessEqual(plan['facet_error'],0.2+1e-9)
                self.assertGreaterEqual(plan['rib'],1-1e-9)
                self.assertAlmostEqual(plan['pitch']*plan['count'],plan['developed_length'])
                self.assertGreater(plan['end_margin'],0)

    def test_blind_paths_carry_depth_and_never_become_through_hinges(self):
        result=build(dict(mode=8,roof_mount=2,dMaterial=9,roof_hinge=False))
        verify(result)
        plan=result['roof']['kerf']
        lid=next(p for p in result['parts'] if p['role']=='lid')
        cuts=[c for c in lid['contours'] if not c['closed']]
        self.assertEqual(len(cuts),plan['count'])
        ys=sorted(c['points'][0][1] for c in cuts)
        for a,b in zip(ys,ys[1:]):self.assertAlmostEqual(b-a,plan['pitch'],places=5)
        for c in cuts:
            self.assertEqual(c['operation'],'blind_kerf')
            self.assertEqual(c['side'],'inside')
            self.assertAlmostEqual(c['depth'],7.65)
            self.assertEqual(c['points'][0][1],c['points'][1][1])
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'roof.dxf';write_dxf(path,[lid]);text=path.read_text()
            self.assertIn('KERF_INSIDE_DEPTH_7.6500mm_REMAIN_1.3500mm',text)
            self.assertNotIn('HINGE_CUTS',text)
        notes=machining_instructions(result)
        self.assertIn('7.6500',notes);self.assertIn('1.3500',notes)
        self.assertIn('ВНУТРЕННЮЮ',notes)

    def test_bottom_groove_checkbox_is_independent_of_all_three_roofs(self):
        base=build(dict(mode=2,dMaterial=4,count_mode=1))
        for mount in range(3):
            plain=build(dict(mode=8,roof_mount=mount,dMaterial=4,count_mode=1))
            grooved=build(dict(mode=8,roof_mount=mount,dMaterial=4,count_mode=1,bottom_in_grooves=True))
            verify(grooved)
            def holes(p):return sum(c['hole'] for c in p['contours'])
            for old,new,reference in zip(plain['parts'][:5],grooved['parts'][:5],base['parts']):
                if reference['role']=='bottom':continue
                self.assertEqual(holes(new)-holes(old),holes(reference))
            bottom=next(p for p in grooved['parts'] if p['role']=='bottom')
            self.assertAlmostEqual(bottom['area'],next(p for p in base['parts'] if p['role']=='bottom')['area'])
        with self.assertRaises(ValueError):
            build(dict(mode=8,bottom_in_grooves=True,SmeshenieDno=0))

    def test_invalid_remaining_and_overlapping_grooves_are_rejected(self):
        for options in ({'dFreza':0},{'kerf_auto_remaining':False,'KerfRemaining':0},
                        {'kerf_auto_remaining':False,'KerfRemaining':9},{'KerfTolerance':0}):
            with self.assertRaises(ValueError):build(dict(mode=8,roof_mount=2)|options)
        with self.assertRaises(CutterFitError):
            plan_kerfs(50,pi,9,4,1.35,0.001,1,0.5)

    def test_dialog_has_one_bottom_checkbox_and_one_offset_field(self):
        html=Path('ShipoMaster_Aspire.html').read_text(encoding='utf-8')
        ids=re.findall(r'\bid="([^"]+)"',html)
        self.assertEqual(len(ids),len(set(ids)))
        for name in ('bottom_in_grooves','SmeshenieDno','KerfRemaining','kerfSummary','kerfDiagram'):
            self.assertEqual(ids.count(name),1)
        roof_tab=html.split('<div id="roof"')[1].split('<div id="export"')[0]
        cuts_tab=html.split('<div id="hinges"')[1].split('<div id="roof"')[0]
        self.assertNotIn('id="kerfSettings"',roof_tab)
        for name in ('CutNone','CutThrough','CutBlind','kerfSettings','KerfRemaining','roof_cut_type'):
            self.assertIn('id="'+name+'"',cuts_tab)

    def test_cut_pattern_and_fastening_are_independent(self):
        for mount,cut,bottom in product(range(2),range(3),(False,True)):
            result=build(dict(mode=8,roof_mount=mount,roof_cut_type=cut,
                              bottom_in_grooves=bottom,dMaterial=4))
            verify(result)
            self.assertEqual(result['roof']['mount'],'overlay' if mount else 'inset')
            self.assertEqual(result['roof']['cut_pattern'],('none','through','blind_kerf')[cut])
            strokes=[c for p in result['parts'] for c in p['contours'] if not c['closed']]
            self.assertEqual(bool(strokes),cut!=0)

    @unittest.skipUnless(shutil.which('node'),'Node.js is required for preview parity')
    def test_live_preview_matches_engine_depth_pitch_and_development(self):
        inputs=[[r,pi,t,d,0.15*t,0.2,1,0.5]
                for t,r,d in product((4,9,18),(50,85),(0.5,2,4))]
        script="""
          const fs=require('fs'),vm=require('vm');
          const c=vm.createContext({document:{readyState:'loading',addEventListener(){}},window:{setInterval(){}}});
          vm.runInContext(fs.readFileSync('preview.js','utf8'),c);
          let data='';process.stdin.on('data',s=>data+=s);
          process.stdin.on('end',()=>console.log(JSON.stringify(JSON.parse(data).map(a=>c.calculateBlindKerf(...a)))));
        """
        run=subprocess.run(['node','-e',script],input=json.dumps(inputs),
                           text=True,capture_output=True,check=True)
        for args,preview in zip(inputs,json.loads(run.stdout)):
            actual=plan_kerfs(*args)
            for name in ('depth','remaining','thickness','cutter','count','pitch','rib','developed_length'):
                self.assertAlmostEqual(preview[name],actual[name],places=8)


if __name__=='__main__':unittest.main()
