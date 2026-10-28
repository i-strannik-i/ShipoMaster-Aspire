import json
from pathlib import Path
import tempfile
import unittest
from math import hypot
from shapely.geometry import Polygon, box
from cage_geometry import CAGE_DEFAULTS, build_cage
from cage_export import export_cage
from geometry_worker import build
import test_project_settings


class CageGeometryTests(unittest.TestCase):
    def test_pdf_paper_sizes_single_file_and_complete_parts(self):
        from pypdf import PdfReader
        for width,height in ((210,297),(420,297),(240,320),(148,210),(210,148)):
            with self.subTest(paper=(width,height)),tempfile.TemporaryDirectory() as temp:
                r=build_cage({'CagePdfWidth':width,'CagePdfHeight':height,'cage_pdf_only':True})
                folder=Path(export_cage(r,temp))
                self.assertEqual([p.name for p in folder.iterdir()],['cage_drawings.pdf'])
                pdf=PdfReader(folder/'cage_drawings.pdf')
                for p in pdf.pages:
                    self.assertAlmostEqual(float(p.mediabox.width),width*72/25.4,places=3)
                    self.assertAlmostEqual(float(p.mediabox.height),height*72/25.4,places=3)
                text='\n'.join(p.extract_text() for p in pdf.pages)
                for word in ('Сборка','Узел X','Узел Y','Ведомость листовых деталей','Передняя панель без двери'):
                    self.assertIn(word,text)
                for p in r['parts']:self.assertIn(p['name'].split('_')[0],text)
                self.assertFalse(any(p['role']=='door' for p in r['parts']))
                self.assertEqual(sum(p['role']=='front' for p in r['parts']),1)
    def test_control_dimensions_lengths_and_saw(self):
        r=build({'task':'cage'});c=r['cage']
        self.assertEqual(len(c['members']),20)
        self.assertEqual([(t['length'],t['quantity']) for t in c['tubes']],[(1000,1)]*4+[(560,4),(560,4),(440,4),(440,4)])
        self.assertEqual(c['net_tube_length'],12000)
        self.assertEqual(c['saw_allowance'],60)
        self.assertEqual(c['tube_with_saw'],12060)
        self.assertEqual(c['finished_size'],[628,528,1003])
        top=next(p for p in r['parts'] if p['role']=='top')
        self.assertEqual(top['origin'][2],1000)
        self.assertEqual(c['tray']['width'],531)
        self.assertEqual(c['tray']['depth'],436)
        self.assertEqual(len(c['plates']),32)

    def test_no_tube_intersections_except_touching_butt_ends(self):
        for opts in ({},{'CageWidth':300,'CageDepth':300,'CageHeight':800},
                     {'CageTubeA':30,'CageTubeB':30,'CageShelves':3,'CageHeight':1400}):
            members=build_cage(opts)['cage']['members']
            for i,a in enumerate(members):
                for b in members[i+1:]:
                    overlaps=[min(a['origin'][k]+a['size'][k],b['origin'][k]+b['size'][k])-max(a['origin'][k],b['origin'][k]) for k in range(3)]
                    self.assertFalse(all(v>1e-7 for v in overlaps),(a,b))

    def test_lot_tray_clearances_and_nonintersecting_plates(self):
        r=build_cage({});o=r['options'];c=r['cage'];tray=c['tray'];g=o['CageClearance']
        self.assertAlmostEqual((o['CageWidth']-2*o['CageTubeA']-tray['width'])/2,o['CageGuide']+g)
        self.assertAlmostEqual(tray['origin'][2]+tray['height']+g,c['ring_tops'][1]-o['CageTubeB'])
        self.assertGreater(c['shelf_levels'][0]-o['CageTubeB'],c['ring_tops'][1]+o['CageShelfT'])
        from cage_geometry import panel_offset
        self.assertAlmostEqual(panel_offset(o)-(o['CagePlateT']+o['CageInsertHead']+o['CageFastenerHeadHeight']),g)
        for p in r['parts']:
            poly=Polygon(p['contours'][0]['points'],[c['points'] for c in p['contours'][1:]])
            self.assertTrue(poly.is_valid,p['name']);self.assertGreater(poly.area,0)
        # All sheet blanks are disjoint and lie completely within the resulting sheet.
        blanks=[box(*Polygon(p['contours'][0]['points']).bounds) for p in r['parts']]
        for i,a in enumerate(blanks):
            self.assertTrue(box(0,0,r['width'],r['height']).covers(a))
            for b in blanks[i+1:]:self.assertLess(a.intersection(b).area,1e-5)

    def test_dividers_split_shelves_without_intersections(self):
        for n in (1,2,3):
            r=build_cage({'CagePartitions':n,'CageShelves':2,'CagePassage':0,'CageDividerT':9,'CageShelfT':12})
            self.assertEqual(len([p for p in r['parts'] if p['role']=='shelf']),2*(n+1))
            divs=[p for p in r['parts'] if p['role']=='divider']
            for shelf in (p for p in r['parts'] if p['role']=='shelf'):
                self.assertEqual(shelf['thickness'],12)
                left=shelf['origin'][0];right=left+shelf['panel_width']
                for div in divs:
                    dx=div['origin'][0]
                    self.assertTrue(right<=dx-2+1e-6 or left>=dx+div['thickness']+2-1e-6)

    def test_shelves_actually_rest_on_rings_and_clear_posts(self):
        r=build_cage({'CagePartitions':2,'CagePassage':0})
        posts=[m for m in r['cage']['members'] if m['role']=='post']
        for part in (p for p in r['parts'] if p['role'] in ('shelf','floor')):
            outline=Polygon(part['contours'][0]['points'])
            minx,miny,_,_=outline.bounds
            from shapely import affinity
            footprint=affinity.translate(outline,part['origin'][0]-minx,part['origin'][1]-miny)
            support=0
            for m in r['cage']['members']:
                x,y,z=m['origin'];sx,sy,sz=m['size']
                xy=box(x,y,x+sx,y+sy)
                if m['role']=='post':self.assertLess(footprint.intersection(xy).area,1e-6)
                elif abs(z+sz-part['origin'][2])<1e-6:support+=footprint.intersection(xy).area
            self.assertGreater(support,100)

    def test_all_connector_holes_fit_and_bolts_do_not_cross(self):
        for raw in ({},{'cage_self_tap':True}):
            c=build_cage(raw)['cage'];o=c['options'];members={m['id']:m for m in c['members']}
            for m in members.values():
                for hole in m['holes']:
                    r=hole['diameter']/2
                    self.assertGreaterEqual(hole['along']-r,2)
                    self.assertLessEqual(hole['along']+r,m['length']-2)
                    width=o['CageTubeA'] if hole['faces'][0] in ('F1','F3') else o['CageTubeB']
                    self.assertGreaterEqual(hole['across']-r,2)
                    self.assertLessEqual(hole['across']+r,width-2)
                    self.assertEqual(len(hole['faces']),1)
                    self.assertFalse(hole['through'])
            post=next(m for m in members.values() if m['role']=='post')
            for a,b in zip(post['holes'][::2],post['holes'][1::2]):
                self.assertGreater(abs(a['along']-b['along']),a['diameter'])
            for p in c['plates']:
                m=members[p['member']];at=o['CageHoleEnd'] if p['end']==0 else m['length']-o['CageHoleEnd']
                h=next(h for h in m['holes'] if abs(h['along']-at)<1e-6)
                self.assertAlmostEqual(p['rail_hole_z'],m['origin'][2]+h['across'])
                self.assertTrue(any(abs(h['along']-p['post_hole_z'])<1e-6 for h in post['holes']))

    def test_bad_settings_rejected(self):
        for raw in ({'CageTubeWall':10},{'CageBoltStagger':2},{'CageTubeB':10},
                    {'CageHeight':150},{'CageShelves':1,'CageShelfLevels':'50'},
                    {'CageShelves':2,'CageShelfLevels':'500;400'},
                    {'CageWidth':float('nan')},{'CagePassage':1000},
                    {'CageWidth':70},{'CagePdfWidth':90},{'CageBoltHole':5},
                    {'CageVentDiameter':20,'CageVentPitch':20},
                    {'cage_self_tap':True,'CageScrewPilot':4}):
            with self.subTest(raw=raw),self.assertRaises(ValueError):build_cage(raw)

    def test_fractional_dimensions_manual_heights_and_ventilation(self):
        r=build_cage({'CageWidth':'650,5','CageHeight':1100,'CageShelves':2,
                      'CageShelfLevels':'400;750,5','CageVentDiameter':8,'CageVentPitch':50})
        self.assertEqual(r['cage']['shelf_levels'],[400,750.5])
        self.assertEqual(next(t for t in r['cage']['tubes'] if t['role']=='rail_x')['length'],610.5)
        self.assertTrue(all(len(p['contours'])>1 for p in r['parts'] if p['role']=='side'))

    def test_dxf_documents_pdf_and_manifest(self):
        import ezdxf
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as temp:
            r=build_cage({});folder=Path(export_cage(r,temp));folder2=Path(export_cage(r,temp))
            self.assertNotEqual(folder,folder2)
            for path in folder.glob('*.dxf'):
                doc=ezdxf.readfile(path);self.assertFalse(doc.audit().has_errors,path)
                self.assertEqual(doc.units,4)
            pdf=PdfReader(folder/'cage_drawings.pdf')
            self.assertGreater(len(pdf.pages),len(r['cage']['tubes'])+len(r['parts'])//3)
            self.assertIn('Разборная клетка',pdf.pages[0].extract_text())
            model=json.loads((folder/'cage_model.json').read_text(encoding='utf-8'))
            self.assertEqual(model['cage']['net_tube_length'],12000)
            tube=ezdxf.readfile(folder/'T01_tube.dxf')
            self.assertEqual(len(list(tube.modelspace().query('CIRCLE'))),8)
            panel=ezdxf.readfile(next(folder.glob('C001_side*.dxf')))
            coords=list(next(iter(panel.modelspace())).get_points())
            self.assertEqual(min(p[0] for p in coords),0)
            self.assertEqual(min(p[1] for p in coords),0)


class CageLuaTests(unittest.TestCase):
    def runtime(self):
        l=test_project_settings.ProjectSettingsTests().runtime();l.globals().main('unused');return l

    def test_registration_matches_engine_and_ignores_box_settings(self):
        l=self.runtime()
        for key,default in CAGE_DEFAULTS.items():self.assertEqual(str(l.globals().fields[key]),str(4 if key in ('CagePanelT','CageTrayT') else default))
        self.assertFalse(l.globals().checks.cage_self_tap)
        l.execute("checks.auto_joints=true;fields.shirina='invalid';fields.cage_export_dir='unused';os.execute=function() end;loadfile=function() return function() return {ok=false,error='CAGE_ENGINE_REACHED'} end end")
        self.assertTrue(l.globals().OnLuaButton_CageExport(l.globals().dialog))
        self.assertEqual(l.globals().last_message,'CAGE_ENGINE_REACHED')

    def test_creation_resizes_and_reports_visible_status(self):
        from geometry_worker import lua
        l=test_project_settings.ProjectSettingsTests().resize_runtime(1000,1000)
        r=build_cage({})
        l.execute('engine_result='+lua(r))
        self.assertTrue(l.globals().OnLuaButton_CageCreate(l.globals().dialog))
        self.assertIn('44 листовых деталей; 20 труб',l.globals().labels.status)
        self.assertEqual(l.globals().labels.cage_status,l.globals().labels.status)
        self.assertAlmostEqual(l.globals().sheet_width,r['width'])
        self.assertAlmostEqual(l.globals().sheet_height,r['height'])

    def test_wall_and_tray_thickness_follow_current_job_in_mm_and_inches(self):
        for value,metric,expected in ((6,True,6),(.25,False,6.35)):
            l=test_project_settings.ProjectSettingsTests().runtime(value,metric)
            l.globals().main('unused')
            self.assertAlmostEqual(float(l.globals().fields.CagePanelT),expected)
            self.assertAlmostEqual(float(l.globals().fields.CageTrayT),expected)
            self.assertEqual(float(l.globals().fields.CageShelfT),6)
            self.assertEqual(float(l.globals().fields.CageDividerT),4)
            l.globals().stock=value*2
            l.execute("os.execute=function() end;loadfile=function() return function() return {ok=false,error='test'} end end")
            l.globals().OnLuaButton_CageCreate(l.globals().dialog)
            self.assertAlmostEqual(float(l.globals().fields.CagePanelT),expected*2)
            self.assertAlmostEqual(float(l.globals().fields.CageTrayT),expected*2)

    def test_successful_export_reports_path_without_modal(self):
        l=self.runtime()
        l.execute("fields.cage_export_dir='folder';os.execute=function() end;loadfile=function() return function() return {ok=true,export_path='folder/Cage_control'} end end;last_message=nil")
        self.assertTrue(l.globals().OnLuaButton_CageExport(l.globals().dialog))
        self.assertIn('folder/Cage_control',l.globals().labels.status)
        self.assertIsNone(l.globals().last_message)


if __name__=='__main__':unittest.main()
