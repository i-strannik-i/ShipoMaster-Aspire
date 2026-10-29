-- VECTRIC LUA SCRIPT
-- ShipoMaster Aspire 1.5.6 / Aspire 12.5
-- Geometry provenance is documented in README_RU.txt and the engine sources.

local VERSION = '1.5.6'
local TITLE = 'ШипоМастер Aspire ' .. VERSION
local script_dir = ''
local number_defaults = {
  shirina=100, dlinna=200, visota=100, dFreza=4, dMaterial=9,
  DMaterialDna=9, Zazor=0.2, LockInterference=0.1, DlinaShipa=20, KolPoVisote=3,
  KolPoShirine=3, KolPoDlinne=3, KolPeregorodokPoDline=0,
  KolPeregorodokPoShirine=0, TolshinaPeregorodok=9,
  VisotaPeregorodok=100, SmeshenieDno=8, SmeshenieKr=3,
  RazmerPror=100, ProrKolPoShirine=3, ProrMezduLin=10,
  ProrMezduParal=5, ProrRasstOtKraya=50, RoofRadius=50, RoofThickness=4, BendFactor=0.5, RoofInset=8, RoofOverhang=8, KerfRemaining=1, KerfTolerance=0.2, KerfMinWeb=1, roof_cut_type=-1
}
local cage_defaults = {
  CageWidth=600,
  CageDepth=500,
  CageHeight=1000,
  CageTubeA=20,
  CageTubeB=30,
  CageTubeWall=1,
  CageSaw=3,
  CagePanelT=3,
  CageShelfT=6,
  CageDividerT=4,
  CageShelves=1,
  CagePartitions=0,
  CagePassage=80,
  CageTrayT=3,
  CageTrayHeight=40,
  CageGuide=12.5,
  CageClearance=2,
  CageShelfLevels='',
  CageBoltHole=5.5,
  CageScrewPilot=2.5,
  CageScrewDiameter=3.5,
  CageHoleEnd=20,
  CageBoltStagger=10,
  CagePlateT=3,
  CageVentDiameter=0,
  CageVentPitch=25,
  CageLayoutWidth=1500,
  CageInsertHole=7,
  CageInsertEnvelope=9,
  CageInsertDepth=10,
  CageInsertHead=1,
  CageInsertGripMin=0.5,
  CageInsertGripMax=3,
  CageFastenerHeadHeight=5,
  CagePdfWidth=210,
  CagePdfHeight=297,
}
local bool_defaults = {bottom_same=true, divider_same=true, height_same=true, centered=true, auto_joints=true, radius_auto=true,roof_same=true,roof_hinge=true,kerf_auto_remaining=true,bottom_in_grooves=false,joint_locks=true}
local modes = {
  'Простой', 'Простой с перегородками', 'С дном в пазы',
  'С дном в пазы с перегородками', 'Шип-паз под крышку',
  'Книжка с прорезями', 'Прямоугольник с прорезями', 'Дно и крышка в пазы', 'Изогнутая крышка'
}
local roof_mounts = {'С отступом в закрытые пазы торцов', 'Накладная с фиксаторами'}
local joints = {'По длине паза', 'По количеству пазов'}

local function project_thickness()
  if not VectricJob().Exists then
    MessageBox('Сначала создайте или откройте проект Aspire и задайте Thickness (Z) в Job Setup.')
    return nil
  end
  local material = MaterialBlock()
  local thickness = material.Thickness * (material.InMM and 1 or 25.4)
  if thickness <= 0 then MessageBox('Задайте положительную толщину материала в Job Setup.');return nil end
  return thickness
end

local function smart_joints(dialog,o)
  local function number(key)
    local n = tonumber((tostring(o[key]):gsub(',','.')))
    if not n or n ~= n or n <= 0 or n > 10000 then return nil end
    return n
  end
  local t = o.dMaterial
  local cutter = tonumber((tostring(o.dFreza):gsub(',','.')))
  local gap = tonumber((tostring(o.Zazor):gsub(',','.')))
  if not cutter or cutter < 0 or not gap or gap < 0 or gap > 1 then
    MessageBox('Проверьте диаметр фрезы и зазор.');return false
  end
  local minimum = math.max(t,2*cutter+2*gap)
  local target = math.max(2*t,3*cutter+2*gap)
  local bottom = o.bottom_same and t or number('DMaterialDna')
  if not bottom then MessageBox('Проверьте толщину дна.');return false end
  local widths = {}
  for _,axis in ipairs({{'visota','KolPoVisote'},{'dlinna','KolPoDlinne'},{'shirina','KolPoShirine'}}) do
    local span = number(axis[1])
    if not span then MessageBox('Задайте положительные размеры ящика.');return false end
    if axis[1] == 'visota' then
      if o.mode == 0 or o.mode == 1 or (o.mode == 8 and not o.bottom_in_grooves) then span = span-bottom end
      if o.mode == 4 then span = span-2*bottom end
    end
    local limit = math.min(100,math.floor((span/minimum-1)/2))
    if limit < 1 then MessageBox('Для этих размеров не помещается соединение: увеличьте габарит или уменьшите фрезу.');return false end
    local best,score = 1,math.huge
    for count=1,limit do
      local width = span/(2*count+1)
      local delta = math.abs(width-target)
      if delta < score then best,score = count,delta end
    end
    o[axis[2]] = best
    widths[#widths+1] = span/(2*best+1)
    dialog:UpdateTextField(axis[2],tostring(best))
  end
  o.count_mode = 1
  dialog:UpdateDropDownListValue('count_mode',joints[2])
  dialog:UpdateLabelField('joint_summary',string.format('Подбор: высота %d, длина %d, ширина %d. Ориентир ширины: %.1f / %.1f / %.1f мм.',o.KolPoVisote,o.KolPoDlinne,o.KolPoShirine,widths[1],widths[2],widths[3]))
  return true
end

local function read_fields(dialog,force_auto)
  local thickness = project_thickness()
  if not thickness then return nil end
  local o = {}
  for k,_ in pairs(number_defaults) do o[k] = dialog:GetTextField(k) end
  o.dMaterial = thickness
  dialog:UpdateTextField('dMaterial',tostring(thickness))
  for k,_ in pairs(bool_defaults) do o[k] = dialog:GetCheckBox(k) end
  o.mode = 2
  local selected = dialog:GetDropDownListValue('mode')
  for i,value in ipairs(modes) do if value == selected then o.mode = i-1 end end
  o.count_mode = dialog:GetDropDownListValue('count_mode') == joints[2] and 1 or 0
  o.roof_mount = 0
  for i,value in ipairs(roof_mounts) do if dialog:GetDropDownListValue('roof_mount')==value then o.roof_mount=i-1 end end
  if o.mode==8 then
    if o.radius_auto then
      local width=tonumber((tostring(o.shirina):gsub(',','.')))
      if width then o.RoofRadius=width/2;dialog:UpdateTextField('RoofRadius',tostring(o.RoofRadius)) end
    end
    if o.roof_same then o.RoofThickness=thickness;dialog:UpdateTextField('RoofThickness',tostring(thickness)) end
  end
  if o.auto_joints or force_auto then
    if not smart_joints(dialog,o) then return nil end
  else
    dialog:UpdateLabelField('joint_summary','Ручные значения пазов. Кнопка «Подобрать» предложит новый расчёт.')
  end
  return o
end

function OnLuaButton_SuggestJoints(dialog)
  return read_fields(dialog,true) ~= nil
end

local function save_fields(o)
  local reg = Registry('ShipoMasterAspire_1')
  for k,_ in pairs(number_defaults) do if k ~= 'dMaterial' then reg:SetString(k,tostring(o[k])) end end
  for k,_ in pairs(bool_defaults) do reg:SetBool(k,o[k]) end
  reg:SetInt('mode',o.mode)
  reg:SetInt('count_mode',o.count_mode)
  reg:SetInt('roof_mount',o.roof_mount)
end

local function calculate(o, export_dir, dialog)
  -- All numeric inputs are in a data file; none is interpolated into a command.
  if o.task~='update_check' and o.task~='update_download' then
    local job=VectricJob()
    if job.Exists and job.Width and job.Height then
      local unit=job.InMM and 1 or 25.4
      o.info_sheet_width=job.Width*unit;o.info_sheet_height=job.Height*unit
    end
  end
  local request = os.tmpname()
  local output = request .. '.lua'
  local file,err = io.open(request,'w')
  if not file then MessageBox('Не удалось записать параметры: '..tostring(err));return nil end
  for k,v in pairs(o) do file:write(k,'=',tostring(v):gsub('[\r\n]',''), '\n') end
  if export_dir then file:write('export_dir=',export_dir:gsub('[\r\n]',''),'\n') end
  file:close()
  local exe = script_dir .. '\\__runtime\\ShipoMasterEngine.exe'
  os.execute('""' .. exe .. '" "' .. request .. '" "' .. output .. '""')
  local loader,load_error = loadfile(output)
  if not loader then
    MessageBox('Расчёт не завершён. Проверьте наличие ShipoMasterEngine.exe рядом с гаджетом.\n'..tostring(load_error))
    return nil
  end
  local success,result = pcall(loader)
  os.remove(request)
  os.remove(output)
  os.remove(request .. '.json')
  if not success or not result.ok then
    if dialog and success then dialog:UpdateLabelField('tool_status',result.error) end
    MessageBox(success and result.error or tostring(result))
    return nil
  end
  if dialog then
    local d=tonumber((tostring(o.dFreza):gsub(',','.')))
    dialog:UpdateLabelField('tool_status',d==0 and 'Диаметр 0: геометрия без проверки доступности фрезой.' or string.format('Фреза %g мм: проверка ширины пазов и сохранения перемычек пройдена.',d))
  end
  os.remove(request .. '.log')
  return result
end

function OnLuaButton_CheckCutter(dialog)
  local o=read_fields(dialog)
  if o then calculate(o,nil,dialog) end
  return true
end

local function choose_cutter(dialog,diameter)
  dialog:UpdateTextField('dFreza',tostring(diameter))
  OnLuaButton_CheckCutter(dialog)
  return true
end
function OnLuaButton_Tool2(dialog) return choose_cutter(dialog,2) end
function OnLuaButton_Tool3(dialog) return choose_cutter(dialog,3) end
function OnLuaButton_Tool4(dialog) return choose_cutter(dialog,4) end
function OnLuaButton_Tool6(dialog) return choose_cutter(dialog,6) end

-- Native Aspire layers describe the machining side, not the part name.
local function machining_layer(outline, thickness, stock)
  local name
  if outline.operation == 'blind_kerf' then
    return 'On_' .. outline.layer
  elseif outline.operation == 'drill' then
    name = 'DRILL'
  elseif not outline.closed then
    name = 'On'
  elseif outline.hole then
    name = 'In'
  else
    name = 'out'
  end
  if thickness and math.abs(thickness-stock) > 0.001 then
    name = name .. '_T_' .. string.format('%.4g',thickness) .. 'mm'
  end
  return name
end

local function add_vectors(result)
  local job = VectricJob()
  local resized = nil
  if not job.Exists then
    local bounds = Box2D()
    bounds:Merge(Point2D(0,0))
    bounds:Merge(Point2D(result.width,result.height))
    if not CreateNewJob('ShipoMaster Aspire '..VERSION,bounds,result.thickness,true,true) then
      MessageBox('Не удалось создать документ Aspire.');return false
    end
    job = VectricJob()
  else
    local scale = job.InMM and 1 or 1/25.4
    if job.Width+0.001 < result.width*scale or job.Height+0.001 < result.height*scale then
      local width = math.max(job.Width,result.width*scale)
      local height = math.max(job.Height,result.height*scale)
      local sheets = job.SheetManager
      -- SDK V12: resize only the active sheet; false preserves object sizes.
      -- Use the actual sheet thickness, not the thickest generated component.
      sheets:ResizeSheet(sheets.ActiveSheetId,width,height,MaterialBlock().Thickness,false)
      job = VectricJob()
      if job.Width+0.001 < width or job.Height+0.001 < height then
        MessageBox('Aspire не применил новый размер листа. Детали не добавлены.');return false
      end
      resized = string.format(' Лист увеличен до %.1f × %.1f мм.',job.Width/scale,job.Height/scale)
    end
  end
  local scale = job.InMM and 1 or 1/25.4
  local stock = MaterialBlock().Thickness / scale
  local pending = {}
  -- Create all native vectors before attaching them to the job.
  for _,part in ipairs(result.parts) do
    for _,outline in ipairs(part.contours) do
      local points = outline.points
      local contour = Contour(0.0)
      contour:AppendPoint(Point2D(job.MinX+points[1][1]*scale, job.MinY+points[1][2]*scale))
      for i=2,#points do
        contour:LineTo(Point2D(job.MinX+points[i][1]*scale, job.MinY+points[i][2]*scale))
      end
      local layer_name = machining_layer(outline,part.thickness,stock)
      pending[#pending+1] = {object=CreateCadContour(contour), layer=layer_name}
    end
  end
  if result.info then
    for _,outline in ipairs(result.info.contours) do
      local contour=Contour(0.0)
      contour:AppendPoint(Point2D(job.MinX+outline.points[1][1]*scale,job.MinY+outline.points[1][2]*scale))
      for i=2,#outline.points do contour:LineTo(Point2D(job.MinX+outline.points[i][1]*scale,job.MinY+outline.points[i][2]*scale)) end
      pending[#pending+1]={object=CreateCadContour(contour),layer='INFO',info=true}
    end
  end
  job.Selection:Clear()
  for _,entry in ipairs(pending) do
    local layer = job.LayerManager:GetLayerWithName(entry.layer)
    layer:AddObject(entry.object,true)
    if not entry.info then job.Selection:Add(entry.object,true,false) end
  end
  job:Refresh2DView()
  return true,resized
end

local function box_signature(o)
  local keys={};for k,_ in pairs(number_defaults) do keys[#keys+1]=k end
  for k,_ in pairs(bool_defaults) do keys[#keys+1]=k end
  for _,k in ipairs({'mode','count_mode','roof_mount'}) do keys[#keys+1]=k end
  table.sort(keys);local values={}
  for _,k in ipairs(keys) do
    local v=o[k];local n=tonumber((tostring(v):gsub(',','.')))
    values[#values+1]=k..'='..(n and string.format('%.8g',n) or tostring(v))
  end
  return table.concat(values,'|')
end
local function remember_box_layout(result,o)
  local job=VectricJob();if not job.SheetManager then return end
  local reg=Registry('ShipoMasterAssembly_1')
  reg:SetString('sheet',tostring(job.SheetManager.ActiveSheetId))
  reg:SetString('signature',box_signature(o))
  for k,v in pairs({x=job.MinX,y=job.MinY,width=result.width,height=result.height}) do reg:SetString(k,tostring(v)) end
end
function OnLuaButton_BoxAssembly(dialog)
  local o=read_fields(dialog);if not o then return true end
  local job=VectricJob();local reg=Registry('ShipoMasterAssembly_1')
  local same_sheet=reg:GetString('sheet','')==tostring(job.SheetManager.ActiveSheetId)
  if same_sheet and reg:GetString('signature','')~=box_signature(o) then
    MessageBox('Параметры изменены после создания деталей. Сначала создайте новую раскладку, затем сборочный чертёж.');return true
  end
  o.task='box_assembly';local result=calculate(o,nil,nil);if not result then return true end
  local scale=job.InMM and 1 or 1/25.4;local gap=20*scale
  local oldMinX,oldMinY,oldMaxX,oldMaxY=job.MinX,job.MinY,job.MinX+job.Width,job.MinY+job.Height
  local baseX=same_sheet and tonumber(reg:GetString('x','')) or nil
  local baseY=same_sheet and tonumber(reg:GetString('y','')) or nil
  local right=baseX and baseX+(tonumber(reg:GetString('width','0')) or 0)*scale or oldMaxX
  local dx=right+gap;local dy=baseY or oldMinY
  if math.abs(oldMaxX)<.001 then dx=(baseX or oldMinX)-gap-result.width*scale end
  if math.abs(oldMaxY)<.001 then dy=math.min(dy,-result.height*scale) end
  local width=job.Width+2*math.max(0,dx+result.width*scale-oldMaxX,oldMinX-dx)
  local height=job.Height+2*math.max(0,dy+result.height*scale-oldMaxY,oldMinY-dy)
  if width>job.Width+.001 or height>job.Height+.001 then
    job.SheetManager:ResizeSheet(job.SheetManager.ActiveSheetId,width,height,MaterialBlock().Thickness,false);job=VectricJob()
    if job.Width+.001<width or job.Height+.001<height then MessageBox('Aspire не увеличил лист. Сборочный чертёж не добавлен.');return true end
    if dx+result.width*scale>job.MinX+job.Width+.001 and math.abs(job.MinX+job.Width-oldMaxX)<.001 then dx=job.MinX+gap end
    if dy+result.height*scale>job.MinY+job.Height+.001 and math.abs(job.MinY+job.Height-oldMaxY)<.001 then dy=job.MinY+gap end
  end
  if dx<job.MinX-.001 or dy<job.MinY-.001 or dx+result.width*scale>job.MinX+job.Width+.001 or dy+result.height*scale>job.MinY+job.Height+.001 then
    MessageBox('Не удалось выделить место для сборочного чертежа на листе.');return true
  end
  local pending={}
  for _,outline in ipairs(result.info.contours) do
    local contour=Contour(0.0);contour:AppendPoint(Point2D(dx+outline.points[1][1]*scale,dy+outline.points[1][2]*scale))
    for i=2,#outline.points do contour:LineTo(Point2D(dx+outline.points[i][1]*scale,dy+outline.points[i][2]*scale)) end
    pending[#pending+1]=CreateCadContour(contour)
  end
  local layer=job.LayerManager:GetLayerWithName('INFO')
  for _,object in ipairs(pending) do layer:AddObject(object,true) end
  job:Refresh2DView()
  dialog:UpdateLabelField('status','Сборочный чертёж добавлен рядом с раскладкой на слой INFO. Детали не дублируются; INFO не фрезеровать.')
  return true
end

function OnLuaButton_Create(dialog)
  local o = read_fields(dialog)
  if not o then return true end
  local result = calculate(o,nil,dialog)
  if not result then return true end
  local success,created,resized = pcall(add_vectors,result)
  if not success then MessageBox('Ошибка добавления в Aspire: '..tostring(created));return true end
  if not created then return true end
  save_fields(o)
  remember_box_layout(result,o)
  local status=string.format('Готово: %d деталей. Раскладка %.1f × %.1f мм.',#result.parts,result.width,result.height)
  if resized then status=status..resized end
  if result.joint_lock_count and result.joint_lock_count>0 then status=status..string.format(' Замки: %d; натяг %.2f мм.',result.joint_lock_count,tonumber((tostring(o.LockInterference):gsub(',','.'))) or 0.1) end
  if result.roof and result.roof.kerf then
    local c=result.roof.kerf
    status=status..string.format(' НЕСКВОЗНО с внутренней стороны: глубина %.3f мм, остаток %.3f мм; %d пропилов, шаг %.3f мм.',c.depth,c.remaining,c.count,c.pitch)
  end
  if result.info then status=status..' Подписи и таблица: слой INFO (не фрезеровать).' end
  if result.roof then status=status..string.format(' Крышка: %.1f × %.1f мм; подъём %.1f мм.',result.roof.panel_length,result.roof.developed_length,result.roof.rise) end
  dialog:UpdateLabelField('status',status)
  return true
end

local function read_cage(dialog)
  local o={task='cage'}
  for k,_ in pairs(cage_defaults) do o[k]=dialog:GetTextField(k) end
  local thickness=project_thickness()
  if not thickness then return nil end
  o.CagePanelT=thickness;o.CageTrayT=thickness
  dialog:UpdateTextField('CagePanelT',tostring(thickness))
  dialog:UpdateTextField('CageTrayT',tostring(thickness))
  o.cage_self_tap=dialog:GetCheckBox('cage_self_tap')
  o.cage_pdf_only=dialog:GetCheckBox('cage_pdf_only')
  return o
end
local function save_cage(o)
  local reg=Registry('ShipoMasterCage_1')
  for k,_ in pairs(cage_defaults) do reg:SetString(k,tostring(o[k])) end
  reg:SetBool('cage_self_tap',o.cage_self_tap)
  reg:SetBool('cage_pdf_only',o.cage_pdf_only)
end
function OnLuaButton_CageCreate(dialog)
  local o=read_cage(dialog)
  if not o then return true end
  local result=calculate(o,nil,nil)
  if not result then return true end
  local success,created,resized=pcall(add_vectors,result)
  if not success then MessageBox('Ошибка добавления клетки: '..tostring(created));return true end
  if not created then return true end
  save_cage(o)
  local status=string.format('Готово: %d листовых деталей; %d труб. Чистый расход профиля %.1f мм.',#result.parts,#result.cage.members,result.cage.net_tube_length)..(resized or '')..' Подписи: слой INFO (не фрезеровать).'
  dialog:UpdateLabelField('cage_status',status)
  dialog:UpdateLabelField('status',status)
  return true
end
function OnLuaButton_CageExport(dialog)
  local folder=dialog:GetTextField('cage_export_dir')
  if not folder or folder:match('^%s*$') then MessageBox('Выберите папку для чертежей клетки.');return true end
  local o=read_cage(dialog)
  if not o then return true end
  o.cage_export_dir=folder
  local result=calculate(o,nil,nil)
  if not result then return true end
  save_cage(o)
  dialog:UpdateLabelField('cage_status','Чертежи сохранены: '..(result.pdf_path or result.export_path))
  dialog:UpdateLabelField('status','Чертежи клетки сохранены: '..(result.pdf_path or result.export_path))
  return true
end

function OnLuaButton_CheckUpdate(dialog)
  local result=calculate({task='update_check'},nil,nil)
  if result then
    dialog:UpdateLabelField('about_update_status',result.message)
    dialog:UpdateTextField('update_available',result.available and '1' or '0')
  end
  return true
end
function OnLuaButton_InstallUpdate(dialog)
  local result=calculate({task='update_download'},nil,nil)
  if result then
    dialog:UpdateLabelField('about_update_status',result.message)
    dialog:UpdateTextField('update_available','0')
  end
  return true
end

function OnLuaButton_Export(dialog)
  MessageBox('Экспорт DXF временно отключён. Используйте «Создать в Aspire».')
  return true
end

function main(path)
  script_dir = path
  if GetAppVersion() < 12 then MessageBox('Для этой версии гаджета нужен Aspire 12 или новее.');return false end
  local thickness = project_thickness()
  if not thickness then return false end
  local reg = Registry('ShipoMasterAspire_1')
  if not reg:GetBool('UserCutterSet_2_3_4_6',false) then
    reg:SetString('dFreza','4')
    reg:SetBool('UserCutterSet_2_3_4_6',true)
  end
  local dialog = HTML_Dialog(false,'file:'..path..'\\ShipoMaster_Aspire.html',900,790,TITLE)
  for k,v in pairs(number_defaults) do
    local value = k == 'dMaterial' and thickness or reg:GetString(k,tostring(v))
    if (k == 'DMaterialDna' and reg:GetBool('bottom_same',true)) or
       (k == 'TolshinaPeregorodok' and reg:GetBool('divider_same',true)) or
       (k == 'RoofThickness' and reg:GetBool('roof_same',true)) then value = thickness end
    dialog:AddTextField(k,tostring(value))
  end
  for k,v in pairs(bool_defaults) do dialog:AddCheckBox(k,reg:GetBool(k,v)) end
  local m = math.max(0,math.min(8,reg:GetInt('mode',2)))
  dialog:AddDropDownList('mode',modes[m+1])
  for _,value in ipairs(modes) do dialog:AddDropDownListValue('mode',value) end
  local j = math.max(0,math.min(1,reg:GetInt('count_mode',0)))
  dialog:AddDropDownList('count_mode',joints[j+1])
  for _,value in ipairs(joints) do dialog:AddDropDownListValue('count_mode',value) end
  local old_mount=reg:GetInt('roof_mount',0)
  local rm = math.max(0,math.min(1,old_mount))
  if old_mount==2 then rm=0 end
  local cut=tonumber(reg:GetString('roof_cut_type','-1')) or -1
  if cut<0 then cut=old_mount==2 and 2 or reg:GetBool('roof_hinge',true) and 1 or 0 end
  dialog:UpdateTextField('roof_cut_type',tostring(math.max(0,math.min(2,cut))))
  dialog:AddDropDownList('roof_mount',roof_mounts[rm+1])
  for _,value in ipairs(roof_mounts) do dialog:AddDropDownListValue('roof_mount',value) end
  local cage_reg=Registry('ShipoMasterCage_1')
  for k,v in pairs(cage_defaults) do dialog:AddTextField(k,(k=='CagePanelT' or k=='CageTrayT') and tostring(thickness) or cage_reg:GetString(k,tostring(v))) end
  dialog:AddCheckBox('cage_self_tap',cage_reg:GetBool('cage_self_tap',false))
  dialog:AddCheckBox('cage_pdf_only',cage_reg:GetBool('cage_pdf_only',true))
  dialog:AddTextField('cage_export_dir','')
  dialog:AddDirectoryPicker('ChooseCageExport','cage_export_dir',true)
  dialog:AddLabelField('cage_status','Задайте параметры клетки. Крепление: наружные плоские угловые накладки.')
  dialog:AddTextField('update_available','0')
  dialog:AddLabelField('about_update_status','При открытии About автоматически проверяется новая версия.')
  dialog:AddTextField('export_dir','')
  dialog:AddDirectoryPicker('ChooseExport','export_dir',true)
  dialog:AddLabelField('status','Задайте размеры и нажмите «Создать в Aspire». Все размеры — в мм.')
  dialog:AddLabelField('joint_summary','Автоматический подбор учитывает толщину материала, фрезу и габариты.')
  dialog:AddLabelField('tool_status','Ваши фрезы: 2, 3, 4, 6 мм. Основная — 4 мм. Перед созданием выполняется проверка.')
  read_fields(dialog)
  dialog:ShowDialog()
  return true
end
