import unittest
from copy import deepcopy
from shapely.geometry import Polygon,Point
from geometry_worker import build,lua
from layout_info import add_info

class InfoTests(unittest.TestCase):
 def test_labels_for_all_modes_preserve_geometry(self):
  for mode in range(9):
   with self.subTest(mode=mode):
    r=build({'mode':mode,'dMaterial':4,'dFreza':4});before=deepcopy(r['parts']);add_info(r)
    self.assertEqual(r['parts'],before);self.assertEqual(len(r['info']['labels']),len(r['parts']))
    self.assertEqual(r['info']['layer'],'INFO');self.assertGreaterEqual(r['info']['paper_text_height'],2.5)
    for c in r['info']['contours']:
     for x,y in c['points']:self.assertTrue(0<=x<=r['width'] and 0<=y<=r['height'])
 def test_box_marks_do_not_add_a_second_table_or_grow_the_layout(self):
  for mode in range(9):
   r=build(dict(mode=mode,dMaterial=4,dFreza=3));size=(r['width'],r['height']);add_info(r)
   self.assertEqual((r['width'],r['height']),size)
   self.assertEqual([c['text'] for c in r['info']['labels']],[p['name'].split('_')[0] for p in r['parts']])
   for part,label in zip(r['parts'],r['info']['labels']):
    from layout_info import part_shape
    shape=part_shape(part)
    self.assertTrue(shape.covers(Point(label['x'],label['y'])))
 def test_existing_large_job_keeps_nominal_part_mark_size_on_a4(self):
  r=add_info(build({'mode':0,'dMaterial':4,'dFreza':4}),2050,3050)
  actual_scale=min(190/max(2050,r['width']),277/max(3050,r['height']))
  self.assertGreaterEqual(r['info']['paper_text_height']*actual_scale/r['info']['a4_scale'],2.5)
 def test_cage_legend_has_all_marks_and_dimensions(self):
  r=add_info(build({'task':'cage'}));self.assertEqual(len(r['info']['labels']),44)
  self.assertIn('БОКОВИНА',r['info']['labels'][0]['text']);self.assertIn('×',r['info']['labels'][0]['text'])
 def test_info_is_separate_and_excluded_from_machining_selection(self):
  from test_project_settings import ProjectSettingsTests
  l=ProjectSettingsTests().resize_runtime(1000,1000)
  r=add_info(build({'mode':0,'dMaterial':4,'dFreza':4}));cuts=sum(len(p['contours']) for p in r['parts'])
  l.execute('engine_result='+lua(r));l.execute('selected_count=0;old_job=VectricJob;function VectricJob() local j=old_job();j.Selection.Add=function() selected_count=selected_count+1 end;return j end')
  l.globals().OnLuaButton_Create(l.globals().dialog)
  self.assertEqual(l.globals().selected_count,cuts);self.assertGreater(l.globals().added,cuts)

if __name__=='__main__':unittest.main()
