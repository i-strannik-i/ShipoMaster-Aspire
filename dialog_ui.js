/* ES5: Aspire uses the Windows embedded HTML dialog. */
var aboutVersionChecked=false;
var settingsSaveTimer=null;
function queueSettingsSave(event){
  if(event&&event.target&&event.target.id==='SaveSettings')return;
  if(settingsSaveTimer!==null)window.clearTimeout(settingsSaveTimer);
  settingsSaveTimer=window.setTimeout(function(){
    settingsSaveTimer=null;var button=document.getElementById('SaveSettings');if(button)button.click();
  },400);
}
function resizeDialogLayout(){
  var header=document.getElementsByClassName('header')[0],body=document.getElementsByClassName('body')[0],tabs=document.getElementsByClassName('tabs')[0],dock=document.getElementById('bottomDock');
  if(!header||!body||!tabs||!dock)return;
  var viewport=document.documentElement.clientHeight||window.innerHeight||790;
  body.style.top=header.offsetHeight+'px';
  var height=Math.max(60,viewport-header.offsetHeight-18-tabs.offsetHeight-15-dock.offsetHeight-18-10);
  var pages=document.getElementsByClassName('page');for(var i=0;i<pages.length;i++)pages[i].style.height=height+'px';
}
function showUpdateChecking(){document.getElementById('about_update_status').textContent='Проверяем новую версию на GitHub…';}
function checkVersionOnAbout(){if(aboutVersionChecked)return;aboutVersionChecked=true;showUpdateChecking();window.setTimeout(function(){document.getElementById('CheckUpdate').click();},30);}
function refreshUpdateButton(){var value=document.getElementById('update_available');if(value)document.getElementById('InstallUpdate').style.display=value.value==='1'?'inline-block':'none';}
if(document.addEventListener)document.addEventListener('DOMContentLoaded',function(){resizeDialogLayout();refreshUpdateButton();},false);
if(document.addEventListener){
  document.addEventListener('input',queueSettingsSave,false);
  document.addEventListener('change',queueSettingsSave,false);
  document.addEventListener('click',queueSettingsSave,false);
}
window.onresize=resizeDialogLayout;
window.setInterval(function(){resizeDialogLayout();refreshUpdateButton();},500);
