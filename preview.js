/* ES5 / SVG preview for Aspire's embedded HTML dialog. Schematic assembly view. */
function calculateBlindKerf(radius,angle,thickness,diameter,remaining,tolerance,minWeb,factor){
  if(!(diameter>0))throw new Error('Укажите диаметр прямой пазовой фрезы больше нуля.');
  if(!(remaining>0&&remaining<thickness))throw new Error('Остаточный слой должен быть больше нуля и меньше толщины крыши.');
  if(!(tolerance>0&&minWeb>0))throw new Error('Допуск огранки и ребро должны быть положительными.');
  var depth=thickness-remaining,neutral=radius+depth+factor*remaining;
  var maxRotation=2*Math.atan(diameter/(2*(neutral-radius)));
  var facetRotation=2*Math.acos(Math.max(-1,Math.min(1,1-tolerance/neutral)));
  if(!(facetRotation>0))throw new Error('Слишком мал допуск огранки.');
  var count=Math.max(1,Math.ceil(angle/Math.min(maxRotation,facetRotation)));
  if(count>1000)throw new Error('Более 1000 пропилов: увеличьте допуск огранки.');
  var developed=neutral*angle,pitch=developed/count,rib=pitch-diameter;
  if(rib<minWeb-0.000001)throw new Error('Ребро '+rib.toFixed(3)+' мм меньше минимума '+minWeb+' мм. Уменьшите фрезу или увеличьте допуск огранки.');
  return {depth:depth,remaining:remaining,thickness:thickness,cutter:diameter,count:count,pitch:pitch,rib:rib,developed_length:developed};
}
function blindKerfDiagram(plan){
  var depthHeight=120*plan.depth/plan.thickness,cutWidth=70*plan.cutter/plan.pitch;
  var svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 230" width="100%" role="img" aria-label="Сечение несквозных пропилов: глубина '+plan.depth.toFixed(3)+' мм, остаток '+plan.remaining.toFixed(3)+' мм">';
  svg+='<text x="20" y="25" font-family="Segoe UI,Arial" font-size="16" fill="#254a61">Внутренняя сторона — фрезеровать отсюда ↓</text>';
  svg+='<rect x="20" y="50" width="420" height="120" fill="#dbb775" stroke="#725630" stroke-width="2"/>';
  for(var j=0;j<6;j++)svg+='<rect x="'+(20+(j+0.5)*70-cutWidth/2)+'" y="49" width="'+cutWidth+'" height="'+(depthHeight+1)+'" fill="#e2f0f7" stroke="#397a9b"/>';
  svg+='<line x1="465" x2="465" y1="50" y2="'+(50+depthHeight)+'" stroke="#397a9b" stroke-width="2"/>';
  svg+='<text x="480" y="95" font-family="Segoe UI,Arial" font-size="17" fill="#225d78">Глубина '+plan.depth.toFixed(3)+' мм</text>';
  svg+='<text x="480" y="155" font-family="Segoe UI,Arial" font-size="17" fill="#8b551e">Остаток '+plan.remaining.toFixed(3)+' мм</text>';
  svg+='<text x="20" y="195" font-family="Segoe UI,Arial" font-size="16" fill="#725630">Наружная сторона — сохранить целой</text>';
  return svg+'<text x="20" y="225" font-family="Segoe UI,Arial" font-size="15" fill="#254a61">Фреза Ø'+plan.cutter+' мм · шаг '+plan.pitch.toFixed(3)+' мм · толщина '+plan.thickness+' мм</text></svg>';
}
function selectedLabel(field){
  return field && field.options && field.selectedIndex>=0 ? field.options[field.selectedIndex].text : field?field.value:'';
}
function chooseCutPattern(pattern){
  var mode=selectedLabel(document.getElementById('mode'));
  if(mode!=='Изогнутая крышка')return false;
  document.getElementById('roof_cut_type').value=String(pattern);
  document.getElementById('roof_hinge').checked=pattern===1;
  updateDimensions();
  return true;
}
function updateCutCards(mode,blind,hinge){
  var ids=['CutNone','CutThrough','CutBlind'];
  var current=mode===8?(blind?2:hinge?1:0):(mode===5||mode===6?1:-1);
  for(var i=0;i<ids.length;i++){
    var card=document.getElementById(ids[i]);
    if(!card)continue;
    card.disabled=mode!==8;
    card.className='cut-card'+(i===current?' chosen':'');
    if(card.setAttribute)card.setAttribute('aria-pressed',i===current?'true':'false');
    document.getElementById('cutPicked'+i).textContent=i===current?'● Выбрано':'○ Выбрать';
  }
  var message=mode===8?(current===2?'Выбраны несквозные пропилы. Ниже — глубина, остаток и схема сечения. Крепление выбирается отдельно на вкладке «Крышка».':current===1?'Выбраны сквозные шахматные прорези. Ниже — настройка перемычек и шага.':'Крыша без прорезей: используйте уже согнутую заготовку.'):
    mode===5||mode===6?'Для книжки и прямоугольника используется сквозной шахматный рисунок. Три варианта выбора доступны в режиме «Изогнутая крышка».':'Выберите «Изогнутая крышка» на вкладке «Параметры», чтобы выбирать все три рисунка.';
  document.getElementById('cutPatternSummary').textContent=message;
  document.getElementById('hingeCommonSettings').style.display=current===1?'block':'none';
  var legacyRows=['hingeAreaRow','hingeOffsetRow','hingeCenteredRow','hingeAllowanceRow'];
  for(var row=0;row<legacyRows.length;row++)document.getElementById(legacyRows[row]).style.display=mode===8?'none':'';
}
var previewState = '';
function updateDimensions() {
  var names = ['Простой','Простой с перегородками','С дном в пазы','С дном в пазы с перегородками','Шип-паз под крышку','Книжка с прорезями','Прямоугольник с прорезями','Дно и крышка в пазы','Изогнутая крышка'];
  var select = document.getElementById('mode'), host = document.getElementById('assemblyPreview');
  if (!select || !host) return;
  var mode = 0, i, values = {}, keys = ['dlinna','shirina','visota','dMaterial','DMaterialDna','SmeshenieDno','KolPeregorodokPoDline','KolPeregorodokPoShirine','VisotaPeregorodok','RazmerPror','ProrRasstOtKraya','ProrMezduParal','RoofRadius','RoofThickness','BendFactor','RoofInset','RoofOverhang','dFreza','KerfRemaining','KerfTolerance','KerfMinWeb'];
  // Aspire may use numeric option values while Lua reads the visible label.
  var selected=select.options && select.selectedIndex>=0 ? select.options[select.selectedIndex].text : select.value;
  for (i=0;i<names.length;i++) if (selected === names[i] || select.value === names[i]) mode=i;
  function read(id, fallback) { var field=document.getElementById(id), value=field?parseFloat(field.value.replace(',','.')):NaN;return isFinite(value)&&value>=0?value:fallback; }
  for(i=0;i<keys.length;i++) values[keys[i]]=read(keys[i],0);
  var same=document.getElementById('bottom_same'), centered=document.getElementById('centered');
  var ra=document.getElementById('radius_auto'),rs=document.getElementById('roof_same'),rh=document.getElementById('roof_hinge');
  document.getElementById('radiusRow').style.display=mode===8?'':'none';
  document.getElementById('radiusAutoRow').style.display=mode===8?'':'none';
  document.getElementById('heightLabel').textContent=mode===8?'Высота прямой стенки, мм':'Высота, мм';
  if(ra&&ra.checked){values.RoofRadius=(values.shirina||100)/2;document.getElementById('RoofRadius').value=values.RoofRadius;}
  if(rs&&rs.checked){values.RoofThickness=values.dMaterial||4;document.getElementById('RoofThickness').value=values.RoofThickness;}
  var mountSelect=document.getElementById('roof_mount');
  var mountText=mountSelect && mountSelect.options && mountSelect.selectedIndex>=0 ? mountSelect.options[mountSelect.selectedIndex].text : '';
  var overlay=mountText==='Накладная с фиксаторами';
  var cutField=document.getElementById('roof_cut_type'),cutType=parseInt(cutField.value,10);
  if(!(cutType>=0&&cutType<=2))cutType=mountText==='Несквозные пропилы (как на фото)'?2:rh&&rh.checked?1:0;
  var blind=cutType===2;
  if(mode===8&&rh)rh.checked=cutType===1;
  var bottomGroove=document.getElementById('bottom_in_grooves');
  document.getElementById('bottomGrooveRow').style.display=mode===8?'':'none';
  document.getElementById('bottomOffsetRow').style.display=(mode===2||mode===3||mode===7||(mode===8&&bottomGroove&&bottomGroove.checked))?'':'none';
  document.getElementById('kerfSettings').style.display=mode===8&&blind?'block':'none';
  updateCutCards(mode,blind,rh&&rh.checked);
  var ka=document.getElementById('kerf_auto_remaining');
  if(mode===8&&blind&&ka&&ka.checked){values.KerfRemaining=0.15*values.RoofThickness;document.getElementById('KerfRemaining').value=values.KerfRemaining.toFixed(4);}
  document.getElementById('roofInsetRow').style.display=overlay?'none':'';
  document.getElementById('roofOverhangRow').style.display=overlay?'':'none';
  var heightSame=document.getElementById('height_same');
  var state=mode+'|'+overlay+'|'+blind+'|'+(ka&&ka.checked)+'|'+(bottomGroove&&bottomGroove.checked)+'|'+keys.map(function(k){return values[k];}).join('|')+'|'+(same&&same.checked)+'|'+(centered&&centered.checked)+'|'+(rh&&rh.checked)+'|'+(heightSame&&heightSame.checked)+'|'+(ra&&ra.checked)+'|'+(rs&&rs.checked);
  if(state===previewState) return;
  previewState=state;
  var L=values.dlinna||200,W=values.shirina||100,H=values.visota||100,t=values.dMaterial||4;
  var bt=same&&same.checked?t:(values.DMaterialDna||t), inset=values.SmeshenieDno;
  var groove=mode===2||mode===3||mode===7||(mode===8&&bottomGroove&&bottomGroove.checked), lid=mode===4||mode===7;
  var flat=mode===6, book=mode===5, lift=lid?Math.max(H*0.26,bt*2):0;
  var maxX=book?L+H/2:L, maxZ=flat?t:H+lift+(lid?bt:0);
  var R=Math.max(W/2,values.RoofRadius||W/2),rt=values.RoofThickness||t,K=values.BendFactor;
  var alpha=Math.asin(W/(2*R)),drop=Math.sqrt(Math.max(0,R*R-W*W/4)),rise=R-drop,S=2*alpha*(R+K*rt);
  var kerf=null;
  if(mode===8&&blind){
    try{kerf=calculateBlindKerf(R,2*alpha,rt,values.dFreza,values.KerfRemaining,values.KerfTolerance,values.KerfMinWeb,K);S=kerf.developed_length;
      document.getElementById('kerfSummary').textContent='ГЛУБИНА: '+kerf.depth.toFixed(3)+' мм от внутренней поверхности.\nОСТАВИТЬ: '+kerf.remaining.toFixed(3)+' мм снаружи.\nФреза Ø'+kerf.cutter+' мм; '+kerf.count+' пропилов; шаг '+kerf.pitch.toFixed(3)+' мм; ребро '+kerf.rib.toFixed(3)+' мм.';
      document.getElementById('kerfDiagram').innerHTML=blindKerfDiagram(kerf);
    }catch(error){document.getElementById('kerfSummary').textContent='Расчёт невозможен: '+error.message;document.getElementById('kerfDiagram').innerHTML='';}
  }
  var roofExtra=overlay?2*read('Zazor',0.2)+t+Math.max(2,values.dFreza):values.RoofInset;
  var roofLength=L+(overlay?2*values.RoofOverhang:0);
  if(mode===8){maxZ=H+rise+rt+roofExtra;maxX=roofLength;}
  document.getElementById('roofSummary').textContent=mode===8?(values.RoofRadius<W/2?'Радиус слишком мал: минимум '+(W/2)+' мм.':'R = '+R.toFixed(1)+' мм; подъём '+rise.toFixed(1)+' мм; полная высота '+maxZ.toFixed(1)+' мм. Развёртка крышки: '+roofLength+' × '+S.toFixed(1)+' мм. Угол '+(2*alpha*180/Math.PI).toFixed(1)+'°. '):'Выберите режим «Изогнутая крышка» на вкладке «Параметры».';
  var scale=Math.min(245/(maxX+0.62*W),155/(0.28*maxX+0.36*W+0.82*maxZ));
  var top=30, left=60, baseline=top+scale*(0.36*W+0.82*maxZ);
  function P(x,y,z){return [left+scale*(x+0.62*y),baseline+scale*(0.28*x-0.36*y-0.82*z)];}
  function points(list){return list.map(function(p){return p[0].toFixed(2)+','+p[1].toFixed(2);}).join(' ');}
  var scene=[];
  function poly(list,fill,stroke,dash){scene.push('<polygon points="'+points(list)+'" fill="'+fill+'" stroke="'+(stroke||'#456f83')+'" stroke-width="1.35" stroke-linejoin="round"'+(dash?' stroke-dasharray="4 3"':'')+'/>');}
  function line(a,b,color,dash){scene.push('<line x1="'+a[0]+'" y1="'+a[1]+'" x2="'+b[0]+'" y2="'+b[1]+'" stroke="'+(color||'#456f83')+'" stroke-width="1"'+(dash?' stroke-dasharray="3 3"':'')+'/>');}
  function text(x,y,value,size,color){scene.push('<text x="'+x+'" y="'+y+'" text-anchor="middle" font-family="Segoe UI,Arial,sans-serif" font-size="'+(size||11)+'" fill="'+(color||'#225d78')+'">'+value+'</text>');}
  function deck(z,fill){poly([P(0,0,z),P(L,0,z),P(L,W,z),P(0,W,z)],fill);}
  function mortises(z){
    // Closed slots are visible on both external faces. Amber distinguishes inset joints.
    for(var n=0;n<3;n++){
      var a=L*(0.17+n*0.24),b=a+L*0.12;
      poly([P(a,0,z),P(b,0,z),P(b,0,z+bt),P(a,0,z+bt)],'#f6db9f','#a47a36');
      var c=W*(0.17+n*0.24),d=c+W*0.12;
      poly([P(L,c,z),P(L,d,z),P(L,d,z+bt),P(L,c,z+bt)],'#f6db9f','#a47a36');
    }
  }
  function seams(){
    for(var j=0;j<3;j++){
      var z=H*(0.16+j*0.25),h=H*0.1;
      var a=P(0,0,z),b=P(Math.min(t,L*0.05),0,z),c=P(Math.min(t,L*0.05),0,z+h),d=P(0,0,z+h);
      line(a,b);line(b,c);line(c,d);
      a=P(L,0,z);b=P(L-Math.min(t,L*0.05),0,z);c=P(L-Math.min(t,L*0.05),0,z+h);d=P(L,0,z+h);
      line(a,b);line(b,c);line(c,d);
    }
  }
  var caption=names[mode];
  if(mode===8){
    function arc(a,r){return [W/2+r*Math.sin(a),H+r*Math.cos(a)-drop];}
    function endcap(x,fill){var profile=[P(x,0,0),P(x,W,0),P(x,W,H)];for(var q=0;q<=32;q++){var v=arc(alpha-2*alpha*q/32,R);profile.push(P(x,v[0],v[1]));}profile.push(P(x,0,0));poly(profile,fill);}
    poly([P(0,W,0),P(L,W,0),P(L,W,H),P(0,W,H)],'#bed5de');
    endcap(0,'#cbdfe7');deck(groove?inset+bt:bt,'#e4eef2');
    poly([P(0,0,0),P(L,0,0),P(L,0,H),P(0,0,H)],'#dce9ed');
    for(i=0;i<24;i++){
      var v1=arc(alpha-2*alpha*i/24,R+rt),v2=arc(alpha-2*alpha*(i+1)/24,R+rt);
      poly([P(0,v1[0],v1[1]),P(L,v1[0],v1[1]),P(L,v2[0],v2[1]),P(0,v2[0],v2[1])],i%2?'#a9c9d5':'#bed8e0');
      if(((rh&&rh.checked)||blind)&&i%2===1)line(P(L*0.08,v1[0],v1[1]),P(L*0.92,v1[0],v1[1]),'#287da0',true);
    }
    endcap(L,'#b6d0db');seams();if(groove)mortises(inset);
    if(!overlay){
      for(var e=0;e<2;e++){var ex=e?L:0;for(i=0;i<24;i++){var c1=arc(alpha-2*alpha*i/24,R+rt+roofExtra),c2=arc(alpha-2*alpha*(i+1)/24,R+rt+roofExtra);line(P(ex,c1[0],c1[1]),P(ex,c2[0],c2[1]),'#8b632b');}}
    }else{
      for(var e2=0;e2<2;e2++)for(i=0;i<3;i++){var phi=alpha-2*alpha*(i+1)/4,cv=arc(phi,R+rt+2);var xx=e2?L:0;line(P(xx-t,cv[0],cv[1]),P(xx+t*2,cv[0],cv[1]),'#b56a19');}
    }
    caption=(blind?'Несквозные пропилы · глубина '+(kerf?kerf.depth.toFixed(3):'?')+' мм':overlay?'Накладная · закрытые пазы + съёмные фиксаторы':'С отступом · шипы крыши в закрытых пазах торцов')+' · R '+R.toFixed(1)+' мм';
  }else if(flat){
    deck(0,'#a9c8d5');deck(t,'#dce9ed');
    var area=Math.min(L,values.RazmerPror||L*0.45),offset=centered&&centered.checked?(L-area)/2:Math.max(0,Math.min(L-area,values.ProrRasstOtKraya));
    var rows=Math.max(4,Math.min(18,Math.round(area/(values.ProrMezduParal||5))));
    for(i=0;i<=rows;i++)for(var row=0;row<3;row++){
      var x=offset+area*i/rows,y=W*(0.07+row*0.30)+(i%2?W*0.07:0);
      line(P(x,y,t+0.1),P(x,Math.min(W*0.95,y+W*0.20),t+0.1),'#287da0');
    }
    caption='Прямоугольник с гибкими прорезями';
  }else if(book){
    var profile=[[0,0],[L,0]],radius=H/2;
    for(i=1;i<=18;i++){var angle=Math.PI*i/18;profile.push([L+radius*Math.sin(angle),radius-radius*Math.cos(angle)]);}
    profile.push([0,H]);
    poly(profile.map(function(p){return P(p[0],W,p[1]);}),'#cbdfe7');
    poly([P(0,0,0),P(L,0,0),P(L,W,0),P(0,W,0)],'#a8cad8');
    poly([P(0,0,H),P(L,0,H),P(L,W,H),P(0,W,H)],'#dce9ed');
    for(i=0;i<18;i++){
      var a1=Math.PI*i/18,a2=Math.PI*(i+1)/18;
      var x1=L+radius*Math.sin(a1),z1=radius-radius*Math.cos(a1),x2=L+radius*Math.sin(a2),z2=radius-radius*Math.cos(a2);
      poly([P(x1,0,z1),P(x1,W,z1),P(x2,W,z2),P(x2,0,z2)],i%2?'#a5c7d6':'#bad6e0');
      if(i%2===1)line(P(x1,W*0.06,z1),P(x1,W*0.94,z1),'#287da0',true);
    }
    poly(profile.map(function(p){return P(p[0],0,p[1]);}),'#e3edf1');
    caption='Книжка: гибкая обложка и боковины';
  }else{
    poly([P(0,0,0),P(0,W,0),P(0,W,H),P(0,0,H)],'#cfdee4');
    poly([P(0,W,0),P(L,W,0),P(L,W,H),P(0,W,H)],'#bed5de');
    var bottomZ=groove?inset+bt:bt;
    deck(Math.min(bottomZ,H*0.45),'#e4eef2');
    if(mode===1||mode===3){
      var nx=Math.max(0,Math.min(12,Math.round(values.KolPeregorodokPoDline))),ny=Math.max(0,Math.min(12,Math.round(values.KolPeregorodokPoShirine)));
      var ph=document.getElementById('height_same'),dh=ph&&ph.checked?H:(values.VisotaPeregorodok||H);
      var dz=Math.min(H,Math.max(bottomZ+bt,dh));
      for(i=nx;i>=1;i--){var xx=L*i/(nx+1);poly([P(xx,0,bottomZ),P(xx,W,bottomZ),P(xx,W,dz),P(xx,0,dz)],'#c5dce1');}
      for(i=ny;i>=1;i--){var yy=W*i/(ny+1);poly([P(0,yy,bottomZ),P(L,yy,bottomZ),P(L,yy,dz),P(0,yy,dz)],'#d6e7e9');}
      caption+=(nx+ny?' · '+nx+' × '+ny:' · перегородки не заданы');
    }
    poly([P(0,0,0),P(L,0,0),P(L,0,H),P(0,0,H)],'#dce9ed');
    poly([P(L,0,0),P(L,W,0),P(L,W,H),P(L,0,H)],'#98bdcc');
    seams();
    if(groove)mortises(Math.min(inset,H*0.4));
    if(mode===7)mortises(H-inset-bt);
    if(lid){
      for(i=0;i<2;i++)line(P(i?L:0,0,H-inset),P(i?L:0,0,H+lift),'#ae945b',true);
      deck(H+lift,'#e4e9db');
      for(i=0;i<3;i++){
        var u=L*(0.17+i*0.24),v=u+L*0.12;
        poly([P(u,0,H+lift),P(v,0,H+lift),P(v,-t,H+lift),P(u,-t,H+lift)],'#d8e0cc','#7a8b66');
        var w=W*(0.17+i*0.24);
        poly([P(L,w,H+lift),P(L+t,w,H+lift),P(L+t,w+W*0.12,H+lift),P(L,w+W*0.12,H+lift)],'#d8e0cc','#7a8b66');
      }
      caption=mode===7?'Дно и крышка в пазах · крышка приподнята':'Крышка на торцевых шипах · приподнята';
    }
  }
  // Dimension lines retain the same semantic axes in every assembly view.
  var p0=P(0,0,0),pL=P(L,0,0),pW=P(L,W,0),dimY=19;
  line([p0[0],p0[1]+5],[p0[0],p0[1]+dimY+5],'#277fa3');line([pL[0],pL[1]+5],[pL[0],pL[1]+dimY+5],'#277fa3');
  line([p0[0],p0[1]+dimY],[pL[0],pL[1]+dimY],'#277fa3');
  text((p0[0]+pL[0])/2,(p0[1]+pL[1])/2+dimY+15,'Длина: '+L+' мм');
  line([pL[0]+9,pL[1]+8],[pW[0]+9,pW[1]+8],'#277fa3');
  text((pL[0]+pW[0])/2+23,(pL[1]+pW[1])/2+25,'Ширина: '+W+' мм');
  var hi=P(L,W,mode===8?maxZ:flat?t:H),xDim=Math.max(pW[0]+25,325);
  line([pW[0]+4,pW[1]],[xDim+5,pW[1]],'#277fa3');line([hi[0]+4,hi[1]],[xDim+5,hi[1]],'#277fa3');line([xDim,pW[1]],[xDim,hi[1]],'#277fa3');
  text(xDim+26,(hi[1]+pW[1])/2-3,flat?'Толщина':mode===8?'Общая':'Высота');text(xDim+26,(hi[1]+pW[1])/2+12,(mode===8?maxZ.toFixed(1):flat?t:H)+' мм');
  host.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 260" width="100%" height="220" role="img" aria-label="'+names[mode]+'">'+scene.join('')+'</svg>';
  document.getElementById('previewCaption').textContent=caption;
}
// Native dialog fields are populated by Lua after the document loads. React to
// user edits immediately; polling also catches values changed by Lua callbacks.
function bindAssemblyPreview(){
  var fields=document.querySelectorAll('input,select'),i;
  for(i=0;i<fields.length;i++){
    if(fields[i].addEventListener){
      fields[i].addEventListener('change',updateDimensions,false);
      fields[i].addEventListener('input',updateDimensions,false);
    }else if(fields[i].attachEvent){
      fields[i].attachEvent('onchange',updateDimensions);
      fields[i].attachEvent('onkeyup',updateDimensions);
    }
  }
  updateDimensions();
}
if(document.readyState==='loading'){
  if(document.addEventListener)document.addEventListener('DOMContentLoaded',bindAssemblyPreview,false);
  else window.attachEvent('onload',bindAssemblyPreview);
}else bindAssemblyPreview();
window.setInterval(updateDimensions,350);
