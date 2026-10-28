const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const names = ['Простой','Простой с перегородками','С дном в пазы','С дном в пазы с перегородками','Шип-паз под крышку','Книжка с прорезями','Прямоугольник с прорезями','Дно и крышка в пазы','Изогнутая крышка'];
for (const mount of [0,1,2]) for (const bottom of [false,true]) for (let mode = 0; mode < names.length; mode++) {
  const fields = {};
  const document = {
    readyState: 'loading', addEventListener() {},
    getElementById(id) { return fields[id] ||= {value:'', checked:false, style:{}}; }
  };
  Object.assign(document.getElementById('mode'), {
    value: String(mode), selectedIndex:mode, options:names.map(text=>({text}))
  });
  Object.assign(document.getElementById('roof_mount'), {value:String(mount),selectedIndex:mount,options:[{text:'С отступом в закрытые пазы торцов'},{text:'Накладная с фиксаторами'},{text:'Несквозные пропилы (как на фото)'}]});
  for (const [id,value] of Object.entries({dlinna:200,shirina:100,visota:100,dMaterial:4,DMaterialDna:4,RoofRadius:50,RoofThickness:4,BendFactor:0.5,RoofInset:8,RoofOverhang:8,dFreza:4,KerfRemaining:0.6,KerfTolerance:0.2,KerfMinWeb:1}))
    document.getElementById(id).value=String(value);
  document.getElementById('bottom_in_grooves').checked=bottom;
  const context = vm.createContext({document,window:{setInterval(){}}});
  vm.runInContext(fs.readFileSync('preview.js','utf8'), context);
  context.updateDimensions();
  assert.ok(fields.assemblyPreview.innerHTML.includes('aria-label="'+names[mode]+'"'));
  assert.ok(!/NaN|Infinity/.test(fields.assemblyPreview.innerHTML));
  if(mode===8){assert.ok(fields.roofSummary.textContent.includes((mount===1?216:200)+' × '));assert.ok(fields.previewCaption.textContent.includes(mount===2?'Несквозные':mount===1?'Накладная':'С отступом'));}
  assert.equal(fields.radiusRow.style.display, mode===8?'':'none');
  assert.equal(fields.bottomGrooveRow.style.display,mode===8?'':'none');
  assert.equal(fields.bottomOffsetRow.style.display,([2,3,7].includes(mode)||(mode===8&&bottom))?'':'none');
  if(mode===8&&mount===2){assert.ok(fields.kerfSummary.textContent.includes('3.400'));assert.ok(fields.kerfDiagram.innerHTML.includes('остаток 0.600'));}
  if(mode===8){
    for(const pattern of [2,1,0,2]){
      const originalMount=fields.roof_mount.selectedIndex;
      assert.equal(context.chooseCutPattern(pattern),true);
      assert.equal(fields.roof_mount.selectedIndex,originalMount,'Cut choice must not change fastening');
      assert.equal(fields.roof_cut_type.value,String(pattern));
      assert.equal(fields.roof_hinge.checked,pattern===1);
      assert.ok(fields[['CutNone','CutThrough','CutBlind'][pattern]].className.includes('chosen'));
      assert.equal(fields.kerfSettings.style.display,pattern===2?'block':'none');
      assert.equal(fields.hingeCommonSettings.style.display,pattern===1?'block':'none');
    }
  }else assert.equal(context.chooseCutPattern(2),false);
}
console.log('Preview: all nine modes, three roof variants and bottom checkbox passed (numeric Aspire option values).');
