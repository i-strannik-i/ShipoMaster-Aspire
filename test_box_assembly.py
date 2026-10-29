import unittest
from pathlib import Path
from geometry_worker import build,lua
from box_assembly import build_box_assembly

class BoxAssemblyTests(unittest.TestCase):
 def test_all_modes_and_mounts_generate_only_info(self):
  for mode,mount in [(m,0) for m in range(9)]+[(8,1)]:
   with self.subTest(mode=mode,mount=mount):
    original=build({'mode':mode,'roof_mount':mount,'dMaterial':4,'dFreza':4})
    r=build_box_assembly(original);self.assertEqual(r['parts'],[]);self.assertTrue(r['info']['assembly'])
    self.assertEqual(r['info']['source_parts'],[p['name'] for p in original['parts']])
    for c in r['info']['contours']:
     for x,y in c['points']:self.assertTrue(-.001<=x<=r['width']+.001 and -.001<=y<=r['height']+.001,(mode,x,y,r['width'],r['height']))
 def test_native_adds_only_info_and_preserves_existing_objects_and_selection(self):
  from test_project_settings import ProjectSettingsTests
  for metric in (True,False):
   for right_origin in (False,True):
    l=ProjectSettingsTests().resize_runtime(1000,1000,in_mm=metric)
    r=build_box_assembly(build({'mode':8,'dMaterial':4,'dFreza':4}))
    l.execute('engine_result='+lua(r))
    # Vectric datum at left or right edge. Sheet resize must not move old parts.
    l.execute('''old_job=VectricJob;selected=0;layers={};function VectricJob()
      local j=old_job();j.MinX=right_origin and -sheet_width or 0;j.MinY=0
      j.LayerManager.GetLayerWithName=function(self,name) layers[name]=true;return {AddObject=function() added=added+1 end} end
      j.Selection.Add=function() selected=selected+1 end;return j end''')
    l.globals().right_origin=right_origin
    self.assertTrue(l.globals().OnLuaButton_BoxAssembly(l.globals().dialog))
    self.assertGreater(l.globals().added,0,l.globals().last_message)
    self.assertEqual(l.globals().selected,0);self.assertEqual(l.globals().existing.x,123);self.assertTrue(l.globals().layers.INFO)
    self.assertIn('не дублируются',l.globals().labels.status)
 def test_failed_resize_cannot_place_diagram_over_existing_layout(self):
  from test_project_settings import ProjectSettingsTests
  l=ProjectSettingsTests().resize_runtime(100,100,fail=True)
  r=build_box_assembly(build({'mode':8,'dMaterial':4,'dFreza':4}));l.execute('engine_result='+lua(r))
  l.globals().OnLuaButton_BoxAssembly(l.globals().dialog)
  self.assertEqual(l.globals().added,0);self.assertIn('не добавлен',l.globals().last_message)
 def test_button_class_and_visibility(self):
  text=Path('ShipoMaster_Aspire.html').read_text('utf-8')
  self.assertIn('class="LuaButton" id="BoxAssembly"',text)
  self.assertIn("document.getElementById('BoxAssembly').style.display=id==='cage'?'none':''",text)

 def test_raw_uuid_cache_after_create_and_changed_parameters(self):
  from test_project_settings import ProjectSettingsTests
  l=ProjectSettingsTests().resize_runtime(5000,5000)
  l.execute('''
    saved={}
    function Registry(name) return {
      GetString=function(self,k,d) return saved[name..':'..k] or d end,
      SetString=function(self,k,v) saved[name..':'..k]=v end,
      SetInt=function() end,SetBool=function() end} end
  ''')
  # The fixture's raw UUID raises on tostring, just like Aspire's luabind UUID.
  original=build(dict(mode=8,dMaterial=6,dFreza=4))
  l.execute('engine_result='+lua(original))
  l.globals().OnLuaButton_Create(l.globals().dialog)
  self.assertEqual(l.globals().saved['ShipoMasterAssembly_1:sheet'],'active-sheet')
  r=build_box_assembly(original);l.execute('engine_result='+lua(r)+';added=0')
  l.globals().OnLuaButton_BoxAssembly(l.globals().dialog)
  self.assertEqual(l.globals().added,len(r['info']['contours']))
  l.execute("fields.shirina='250';added=0")
  l.globals().OnLuaButton_BoxAssembly(l.globals().dialog)
  self.assertEqual(l.globals().added,0)
  self.assertIn('Параметры изменены',l.globals().last_message)
  # A different raw UUID must not reuse a cached layout from another sheet.
  l.execute("raw_sheet.value='another-sheet';last_message=nil")
  l.globals().OnLuaButton_BoxAssembly(l.globals().dialog)
  self.assertEqual(l.globals().added,len(r['info']['contours']))

if __name__=='__main__':unittest.main()
