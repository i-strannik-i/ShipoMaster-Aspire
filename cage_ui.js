/* ES5 live assembly illustration for Aspire's HTML dialog. */
function chooseCagePdfPaper(preset){
  var sizes={A4:[210,297],A3:[297,420],A2:[420,594],A1:[594,841]};
  if(sizes[preset]){document.getElementById('CagePdfWidth').value=sizes[preset][0];document.getElementById('CagePdfHeight').value=sizes[preset][1];}
}
function rotateCagePdfPaper(){var a=document.getElementById('CagePdfWidth'),b=document.getElementById('CagePdfHeight'),v=a.value;a.value=b.value;b.value=v;}
function updateCagePreview(){
  var host=document.getElementById('cagePreview');if(!host)return;
  function n(id,fallback){var el=document.getElementById(id),v=el?parseFloat(el.value.replace(',','.')):NaN;return isFinite(v)?v:fallback;}
  var w=n('CageWidth',0),d=n('CageDepth',0),h=n('CageHeight',0),a=n('CageTubeA',20),b=n('CageTubeB',30);
  if(!(w>2*a&&d>2*b&&h>0)){host.innerHTML='Задайте габариты и сечение трубы.';return;}
  var s=Math.min(355/(w+.52*d),240/(h+.3*d)),scene=[];
  function p(x,y,z){return [65+s*(x+.52*y),300-s*(z+.30*y)];}
  function poly(vertices,color,opacity){var pts=[],i;for(i=0;i<vertices.length;i++)pts.push(p(vertices[i][0],vertices[i][1],vertices[i][2]).join(','));scene.push('<polygon points="'+pts.join(' ')+'" fill="'+color+'" fill-opacity="'+(opacity||1)+'" stroke="#587285" stroke-width="1.1"/>');}
  function cuboid(x,y,z,sx,sy,sz,color){poly([[x,y,z+sz],[x+sx,y,z+sz],[x+sx,y+sy,z+sz],[x,y+sy,z+sz]],color);poly([[x,y,z],[x+sx,y,z],[x+sx,y,z+sz],[x,y,z+sz]],color);poly([[x+sx,y,z],[x+sx,y+sy,z],[x+sx,y+sy,z+sz],[x+sx,y,z+sz]],color);}
  function line(u,v,color){scene.push('<line x1="'+u[0]+'" y1="'+u[1]+'" x2="'+v[0]+'" y2="'+v[1]+'" stroke="'+(color||'#177ca2')+'" stroke-width="1.2"/>');}
  function text(x,y,label,angle){scene.push('<text x="'+x+'" y="'+y+'" text-anchor="middle" font-family="Segoe UI,Arial" font-size="16" fill="#175d7c"'+(angle?' transform="rotate('+angle+' '+x+' '+y+')"':'')+'>'+label+'</text>');}
  var gap=n('CageClearance',2),tray=n('CageTrayHeight',40),st=n('CageShelfT',6),floor=2*b+2*gap+tray;
  // Transparent rear and side walls leave the current interior visible.
  poly([[0,d,0],[w,d,0],[w,d,h],[0,d,h]],'#b6dce9',.35);
  poly([[0,0,0],[0,d,0],[0,d,h],[0,0,h]],'#cbe7ef',.35);
  var tops=[b,floor,h],num=n('CageShelves',0),manual=document.getElementById('CageShelfLevels').value;
  if(manual.replace(/\s/g,'')){var ent=manual.split(';');for(var i=0;i<ent.length;i++){var lev=parseFloat(ent[i].replace(',','.'));if(isFinite(lev))tops.push(lev);}}
  else for(var i=1;i<=num;i++)tops.push(floor+st+(h-b-floor-st)*i/(num+1));
  for(var i=1;i<tops.length;i++)if(tops[i]!==h)cuboid(gap,gap,tops[i],w-2*gap,d-2*gap,st,'#e1c69b');
  var count=n('CagePartitions',0);var radius=n('CagePassage',0)/2;if(radius>0){for(var j=3;j<tops.length;j++){var ring=[];var centerX=count>0?a+(w-2*a)/(count+1)/2:w/2;for(var k=0;k<=40;k++){var angle=k*Math.PI/20;ring.push([centerX+radius*Math.cos(angle),d/2+radius*Math.sin(angle),tops[j]+st+.1]);}poly(ring,'#7894a5');}}
  for(var i=1;i<=count;i++)cuboid(a+(w-2*a)*i/(count+1),b+gap,floor+st,n('CageDividerT',4),d-2*b-2*gap,h-b-floor-st,'#e5d0ab');
  for(var i=0;i<tops.length;i++){
    var z=tops[i]-b;cuboid(a,0,z,w-2*a,a,b,'#a8b9c4');cuboid(a,d-a,z,w-2*a,a,b,'#a8b9c4');cuboid(0,b,z,a,d-2*b,b,'#afbec7');cuboid(w-a,b,z,a,d-2*b,b,'#afbec7');
  }
  for(var x=0;x<=1;x++)for(var y=0;y<=1;y++)cuboid(x*(w-a),y*(d-b),0,a,b,h,'#b3c1ca');
  poly([[0,0,h],[w,0,h],[w,d,h],[0,d,h]],'#c5e2ed',.20);
  // Front panel is shown translucent; there are no doors in this version.
  poly([[0,0,floor],[w,0,floor],[w,0,h],[0,0,h]],'#c8e4f0',.13);
  var head=n('CageFastenerHeadHeight',5),off=n('CagePlateT',3)+head+gap+(document.getElementById('cage_self_tap').checked?0:n('CageInsertHead',1)),pt=n('CagePanelT',3);
  var tw=w-2*a-2*(gap+n('CageGuide',12.5)),td=d-2*b-2*gap,tt=n('CageTrayT',3),tx=(w-tw)/2,ty=b+gap-d*.35,tz=b+gap;
  cuboid(tx,ty,tz,tw,td,tt,'#427d99');cuboid(tx,ty,tz+tt,tw,tt,tray-tt,'#3c7390');cuboid(tx,ty+td-tt,tz+tt,tw,tt,tray-tt,'#6594ab');
  cuboid(tx,ty+tt,tz+tt,tt,td-2*tt,tray-tt,'#5c8da5');cuboid(tx+tw-tt,ty+tt,tz+tt,tt,td-2*tt,tray-tt,'#5c8da5');
  var u=p(0,0,0),v=p(w,0,0);line(u,[u[0],u[1]+32]);line(v,[v[0],v[1]+32]);line([u[0],u[1]+28],[v[0],v[1]+28]);text((u[0]+v[0])/2,u[1]+46,'Ширина X: '+w+' мм');
  u=p(0,0,0);v=p(0,0,h);line(u,[32,u[1]]);line(v,[32,v[1]]);line([36,u[1]],[36,v[1]]);text(22,(u[1]+v[1])/2,'Высота Z: '+h+' мм',-90);
  u=p(w,0,0);v=p(w,d,0);line(u,[u[0]+22,u[1]+10]);line(v,[v[0]+22,v[1]+10]);line([u[0]+18,u[1]+8],[v[0]+18,v[1]+8]);text((u[0]+v[0])/2+48,(u[1]+v[1])/2+10,'Длина Y: '+d+' мм',-30);
  host.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '+Math.ceil(65+s*(w+.52*d)+110)+' 370" width="100%" height="240" role="img" aria-label="Клетка: ширина '+w+', длина '+d+', высота '+h+' мм">'+scene.join('')+'</svg>';
  document.getElementById('cagePreviewNote').textContent='Каркас '+w+' × '+d+' × '+h+' мм. Проём между стойками: '+(w-2*a)+' × '+(d-2*b)+' мм. Снаружи с панелями: '+(w+2*(off+pt))+' × '+(d+2*(off+pt))+' × '+(h+pt)+' мм. Передняя панель показана прозрачной для видимости полок.';
  var preset=document.getElementById('cagePdfPreset');if(preset){var pw=n('CagePdfWidth',210),ph=n('CagePdfHeight',297),lo=Math.min(pw,ph),hi=Math.max(pw,ph);preset.value=lo===210&&hi===297?'A4':lo===297&&hi===420?'A3':lo===420&&hi===594?'A2':lo===594&&hi===841?'A1':'custom';}
}
if(document.addEventListener)document.addEventListener('DOMContentLoaded',updateCagePreview,false);
window.setInterval(updateCagePreview,500);

