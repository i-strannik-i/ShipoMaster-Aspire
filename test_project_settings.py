import unittest
from pathlib import Path
from lupa import LuaRuntime
from geometry_worker import build, lua

class ProjectSettingsTests(unittest.TestCase):
    def resize_runtime(self,width,height,in_mm=True,fail=False):
        l=self.runtime(thickness=6 if in_mm else .25,in_mm=in_mm)
        l.globals().main('unused')
        l.globals().sheet_width=width;l.globals().sheet_height=height
        l.globals().fail_resize=fail
        l.execute('''
        resize_calls=0;added=0;points={};existing={x=123,y=456,size=17}
        raw_sheet=setmetatable({value='active-sheet'},{__tostring=function() error('No such operator defined') end})
        sheets={ActiveSheetId=raw_sheet,ResizeSheet=function(self,id,w,h,t,scale)
          resize_calls=resize_calls+1
          resize_args={id=id,width=w,height=h,thickness=t,scale=scale}
          if not fail_resize then sheet_width=w;sheet_height=h end
        end}
        function VectricJob() return {Exists=true,InMM=metric,Width=sheet_width,Height=sheet_height,
          MinX=-sheet_width/2,MinY=-sheet_height/2,SheetManager=sheets,
          LayerManager={GetLayerWithName=function() return {AddObject=function() added=added+1 end} end},
          Selection={Clear=function() end,Add=function() end},Refresh2DView=function() end} end
        function Point2D(x,y) table.insert(points,{x=x,y=y});return {x=x,y=y} end
        function Contour() return {AppendPoint=function() end,LineTo=function() end} end
        function CreateCadContour(c) return c end
        engine_result={ok=true,width=6050,height=3540,thickness=12,parts={
          {name='test',thickness=6,contours={{closed=true,points={{10,10},{20,10},{20,20},{10,10}}}}}}}
        os.execute=function() end
        loadfile=function() return function() return engine_result end end
        ''')
        return l

    def test_current_sheet_grows_to_layout_without_scaling_or_changing_thickness(self):
        for metric in (True,False):
            scale=1 if metric else 1/25.4
            l=self.resize_runtime(2050*scale,3050*scale,in_mm=metric)
            l.globals().OnLuaButton_Create(l.globals().dialog)
            args=l.globals().resize_args
            self.assertEqual(args.id.value,'active-sheet')
            self.assertAlmostEqual(args.width,6050*scale)
            self.assertAlmostEqual(args.height,3540*scale)
            self.assertEqual(args.thickness,6 if metric else .25)
            self.assertFalse(args.scale)
            self.assertEqual(l.globals().existing.size,17)
            self.assertEqual(l.globals().existing.x,123)
            self.assertEqual(l.globals().existing.y,456)
            self.assertEqual(l.globals().added,1)
            self.assertAlmostEqual(l.globals().points[1].x,(-6050/2+10)*scale)
            self.assertIn('Лист увеличен до 6050.0 × 3540.0',l.globals().labels.status)

    def test_sheet_only_grows_insufficient_dimension_and_never_shrinks(self):
        for w,h,expected in ((7000,3050,(7000,3540)),(2050,4000,(6050,4000)),(7000,4000,(7000,4000))):
            l=self.resize_runtime(w,h);l.globals().OnLuaButton_Create(l.globals().dialog)
            self.assertEqual((l.globals().sheet_width,l.globals().sheet_height),expected)
            self.assertEqual(l.globals().resize_calls,0 if (w,h)==expected else 1)

    def test_failed_resize_does_not_attach_vectors(self):
        l=self.resize_runtime(2050,3050,fail=True)
        l.globals().OnLuaButton_Create(l.globals().dialog)
        self.assertEqual(l.globals().added,0)
        self.assertIn('не применил',l.globals().last_message)

    def test_lock_fields_are_registered_and_passed_to_engine(self):
        l=self.runtime();l.globals().main('unused')
        self.assertTrue(l.globals().checks.joint_locks)
        self.assertAlmostEqual(float(l.globals().fields.LockInterference),.1)
        l.execute("checks.auto_joints=false;fields.export_dir='unused';fields.LockInterference='0.15';os.execute=function() end;loadfile=function() return function() return {ok=true,parts={}} end end")
        self.assertTrue(l.globals().OnLuaButton_CheckCutter(l.globals().dialog))

    def runtime(self,thickness=4,in_mm=True):
        lua=LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
        fields={};checks={};labels={};lists={};has_job=true
        function VectricJob() return {Exists=has_job} end
        function MaterialBlock() return {Thickness=stock,InMM=metric} end
        function luaUUID() return {
          SetId=function(self,id) self.value=id.value end,
          AsString=function(self) return self.value end} end
        function GetAppVersion() return 12.504 end
        function MessageBox(s) last_message=s end
        function Registry() return {
          GetString=function(self,k,d) if k=='dMaterial' then return '99' else return d end end,
          GetBool=function(self,k,d) return d end,
          GetInt=function(self,k,d) return d end,
          SetString=function() end,SetInt=function() end,SetBool=function() end} end
        function HTML_Dialog() return {
          AddTextField=function(self,k,v) fields[k]=v end,
          GetTextField=function(self,k) return fields[k] end,
          UpdateTextField=function(self,k,v) fields[k]=v end,
          AddCheckBox=function(self,k,v) checks[k]=v end,
          GetCheckBox=function(self,k) return checks[k] end,
          AddDropDownList=function(self,k,v) lists[k]=v end,
          AddDropDownListValue=function() end,
          GetDropDownListValue=function(self,k) return lists[k] end,
          UpdateDropDownListValue=function(self,k,v) lists[k]=v end,
          AddDirectoryPicker=function() end,
          AddLabelField=function(self,k,v) labels[k]=v end,
          UpdateLabelField=function(self,k,v) labels[k]=v end,
          ShowDialog=function(self) dialog=self;return true end} end
        ''')
        lua.globals().stock=thickness;lua.globals().metric=in_mm
        script=Path(__file__).with_name('ShipoMaster_Aspire.lua')
        if not script.exists():script=script.parent.parent/script.name
        lua.execute(script.read_text(encoding='utf-8'))
        return lua

    def test_stock_overrides_saved_thickness_and_same_material_fields(self):
        for thickness,metric,expected in [(4,True,4),(0.25,False,6.35)]:
            l=self.runtime(thickness,metric);self.assertTrue(l.globals().main('unused'))
            for field in ['dMaterial','DMaterialDna','TolshinaPeregorodok']:
                self.assertAlmostEqual(float(l.globals().fields[field]),expected)

    def test_current_stock_is_read_again_and_manual_quantities_preserved(self):
        l=self.runtime();l.globals().main('unused')
        l.execute("stock=6;checks.auto_joints=false;fields.KolPoVisote='2';fields.KolPoDlinne='4';fields.KolPoShirine='2';fields.export_dir='unused';os.execute=function() end;loadfile=function() return function() return {ok=true,parts={}} end end")
        self.assertTrue(l.globals().OnLuaButton_CheckCutter(l.globals().dialog))
        self.assertEqual(float(l.globals().fields.dMaterial),6)
        self.assertEqual(l.globals().fields.KolPoDlinne,'4')

    def test_suggestions_produce_valid_boxes_with_project_material(self):
        for t in (4,6,9):
            l=self.runtime(t);l.globals().main('unused')
            f=l.globals().fields
            for mode in range(5):
                r=build(dict(mode=mode,count_mode=1,dMaterial=t,dFreza=3,
                    KolPoVisote=int(f.KolPoVisote),KolPoDlinne=int(f.KolPoDlinne),
                    KolPoShirine=int(f.KolPoShirine)))
                self.assertGreaterEqual(len(r['parts']),5)
            self.assertIn('Подбор:',l.globals().labels.joint_summary)

    def test_cut_pattern_is_independent_of_mount_and_passed_to_engine(self):
        for selected,mount in [('С отступом в закрытые пазы торцов',0),('Накладная с фиксаторами',1)]:
            for cut in range(3):
                l=self.runtime();l.globals().main('unused')
                l.globals().lists.mode='Изогнутая крышка';l.globals().lists.roof_mount=selected
                l.globals().fields.roof_cut_type=str(cut)
                l.globals().checks.bottom_in_grooves=True
                l.execute("captured='';saved_mount=nil;saved_cut=nil;fields.export_dir='unused';io.open=function() return {write=function(self,...) for _,v in ipairs({...}) do captured=captured..tostring(v) end end,close=function() end} end;os.execute=function() end;loadfile=function() return function() return {ok=true,parts={}} end end;Registry=function() return {SetString=function(self,k,v) if k=='roof_cut_type' then saved_cut=v end end,SetBool=function() end,SetInt=function(self,k,v) if k=='roof_mount' then saved_mount=v end end} end")
                l.execute("function VectricJob() return {Exists=true,InMM=true,Width=5000,Height=5000,MinX=0,MinY=0,Selection={Clear=function() end},Refresh2DView=function() end} end; loadfile=function() return function() return {ok=true,parts={},width=1,height=1} end end")
                l.globals().OnLuaButton_Create(l.globals().dialog)
                self.assertIn('roof_mount='+str(mount)+'\n',l.globals().captured)
                self.assertIn('roof_cut_type='+str(cut)+'\n',l.globals().captured)
                self.assertIn('bottom_in_grooves=true\n',l.globals().captured)
                self.assertEqual(l.globals().saved_mount,mount)
                self.assertEqual(l.globals().saved_cut,str(cut))

    def test_export_is_disabled_without_running_engine(self):
        l=self.runtime();l.globals().main('unused')
        l.execute("os.execute=function() error('export must not run') end")
        self.assertTrue(l.globals().OnLuaButton_Export(l.globals().dialog))
        self.assertIn('временно отключён',l.globals().last_message)

    def test_native_blind_paths_have_separate_depth_layer_and_status(self):
        l=self.runtime();l.globals().main('unused')
        l.globals().engine_result=l.execute('return '+lua(build(dict(mode=8,roof_mount=2,dMaterial=4))))
        l.execute("""
          native_layers={}
          os.execute=function() end
          loadfile=function() return function() return engine_result end end
          function Contour() return {AppendPoint=function() end,LineTo=function() end} end
          function Point2D(x,y) return {x=x,y=y} end
          function CreateCadContour(c) return c end
          function VectricJob() return {Exists=true,InMM=true,Width=5000,Height=5000,MinX=0,MinY=0,
            LayerManager={GetLayerWithName=function(self,name) table.insert(native_layers,name);return {AddObject=function() end} end},
            Selection={Clear=function() end,Add=function() end},Refresh2DView=function() end} end
        """)
        l.globals().OnLuaButton_Create(l.globals().dialog)
        layers=list(l.globals().native_layers.values())
        self.assertTrue(any('KERF_INSIDE_DEPTH_3.4000mm_REMAIN_0.6000mm' in name for name in layers))
        self.assertFalse(any('HINGE_CUTS' in name for name in layers))
        self.assertIn('глубина 3.400',l.globals().labels.status)

    def capture_layers(self,result,in_mm=True):
        l=self.resize_runtime(5000,5000,in_mm=in_mm)
        l.globals().engine_result=l.execute('return '+lua(result))
        l.execute('''
          native_layers={};selected=0
          function VectricJob() return {Exists=true,InMM=metric,Width=5000,Height=5000,MinX=0,MinY=0,
            LayerManager={GetLayerWithName=function(self,name)
              table.insert(native_layers,name);return {AddObject=function() end} end},
            Selection={Clear=function() end,Add=function() selected=selected+1 end},Refresh2DView=function() end} end
        ''')
        l.globals().OnLuaButton_Create(l.globals().dialog)
        return list(l.globals().native_layers.values()),l.globals().selected

    def test_native_layers_route_all_box_modes_by_machining_side(self):
        for mode in range(9):
            with self.subTest(mode=mode):
                result=build(dict(mode=mode,dMaterial=6,dFreza=4))
                actual,selected=self.capture_layers(result)
                expected=[]
                for part in result['parts']:
                    for c in part['contours']:
                        name='On' if not c['closed'] else 'In' if c['hole'] else 'out'
                        if abs(part['thickness']-6)>.001:name+=f"_T_{part['thickness']:.4g}mm"
                        expected.append(name)
                self.assertEqual(actual,expected)
                self.assertEqual(selected,len(expected))
                self.assertIn('out',actual)

    def test_native_layers_keep_depth_drilling_and_other_thickness_separate(self):
        points=[[0,0],[10,0],[10,10],[0,0]]
        result=dict(ok=True,width=100,height=100,thickness=6,parts=[
            dict(name='a',thickness=6,contours=[
                dict(closed=True,hole=False,points=points),
                dict(closed=True,hole=True,points=points),
                dict(closed=False,points=points),
                dict(closed=True,hole=True,operation='drill',layer='CAGE_DRILL',points=points),
                dict(closed=False,operation='blind_kerf',layer='KERF_INSIDE_DEPTH_5.0000mm_REMAIN_1.0000mm',points=points)]),
            dict(name='b',thickness=3,contours=[dict(closed=True,hole=False,points=points)])],
            info=dict(contours=[dict(points=points)]))
        layers,selected=self.capture_layers(result)
        self.assertEqual(layers,['out','In','On','DRILL',
            'On_KERF_INSIDE_DEPTH_5.0000mm_REMAIN_1.0000mm','out_T_3mm','INFO'])
        self.assertEqual(selected,6)
        # Stock is .25 inches = 6.35 mm; base layers must use the actual stock units.
        result['parts'][0]['thickness']=6.35
        layers,_=self.capture_layers(result,in_mm=False)
        self.assertEqual(layers[:4],['out','In','On','DRILL'])

    def test_native_cage_drilling_is_not_merged_into_profile_holes(self):
        result=build(dict(task='cage',dMaterial=6))
        actual,selected=self.capture_layers(result)
        expected=[]
        for part in result['parts']:
            for c in part['contours']:
                name='DRILL' if c.get('operation')=='drill' else 'In' if c['hole'] else 'out'
                if abs(part['thickness']-6)>.001:name+=f"_T_{part['thickness']:.4g}mm"
                expected.append(name)
        self.assertTrue(any(name.startswith('DRILL') for name in expected))
        self.assertEqual(actual,expected)
        self.assertEqual(selected,len(expected))

    def test_missing_job_requires_setup(self):
        l=self.runtime();l.execute('has_job=false')
        self.assertFalse(l.globals().main('unused'))
        self.assertIn('Thickness',l.globals().last_message)

    def test_cutter_failure_is_shown_and_blocks_native_creation(self):
        l=self.runtime();l.globals().main('unused')
        l.execute("fields.dFreza='6';os.execute=function() end;loadfile=function() return function() return {ok=false,kind='cutter',error='Фреза 6 мм не проходит. Подойдут 2, 3, 4 мм.'} end end;CreateCadContour=function() error('must not add vectors') end")
        self.assertTrue(l.globals().OnLuaButton_Create(l.globals().dialog))
        self.assertIn('Подойдут 2, 3, 4',l.globals().last_message)
        self.assertIn('Подойдут 2, 3, 4',l.globals().labels.tool_status)
        l.globals().OnLuaButton_Tool4(l.globals().dialog)
        self.assertEqual(l.globals().fields.dFreza,'4')

if __name__=='__main__':unittest.main()
