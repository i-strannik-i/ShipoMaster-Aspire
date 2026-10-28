"""Package the already-built engine, native gadget, sources and license notices."""
from pathlib import Path
import shutil
import sys
import zipfile
import importlib.metadata

ROOT=Path(__file__).resolve().parent
from version import VERSION
NAME='ShipoMaster Aspire'
for label_file in ('ShipoMaster_Aspire.lua','ShipoMaster_Aspire.html','README_RU.txt'):
    if VERSION not in (ROOT/label_file).read_text(encoding='utf-8'):
        raise RuntimeError('Version label mismatch: '+label_file)
folder=ROOT/'package'/NAME
folder.mkdir(parents=True,exist_ok=True)
for name in ('ShipoMaster_Aspire.lua','ShipoMaster_Aspire.html','preview.js','cage_ui.js','dialog_ui.js','README_RU.txt','VERIFICATION_RU.txt'):
    shutil.copy2(ROOT/name,folder/name)
shutil.copytree(ROOT/'assets',folder/'assets',dirs_exist_ok=True)
if (ROOT/'development/roof_mounts.png').exists():
    shutil.copy2(ROOT/'development/roof_mounts.png',folder/'ROOF_MOUNTS.png')
if (ROOT/'development/kerf_depth.png').exists():
    shutil.copy2(ROOT/'development/kerf_depth.png',folder/'KERF_DEPTH.png')
if (ROOT/'development/cut_cards.png').exists():
    shutil.copy2(ROOT/'development/cut_cards.png',folder/'CUT_CARDS.png')
runtime=folder/'__runtime';runtime.mkdir(exist_ok=True)
shutil.copy2(ROOT/'bin/ShipoMasterEngine.exe',runtime/'ShipoMasterEngine.exe')
if (folder/'ShipoMasterEngine.exe').exists():
    (folder/'ShipoMasterEngine.exe').replace(runtime/'ShipoMasterEngine.exe')
sources=folder/'sources';sources.mkdir(exist_ok=True)
for name in ('requirements.txt','gadget_updates.py','layout_info.py','test_layout_info.py','dialog_ui.js','test_gadget_updates.py','test_dialog_ui.js','cage_geometry.py','cage_export.py','cage_pdf.py','cage_drafting.py','test_drafting.py','cage_ui.js','test_cage.py','test_cage_ui.js','version.py','bump_version.py','geometry_worker.py','migrated_geometry.py','joint_locks.py','curved_roof.py','kerf_bending.py','cutter_checks.py','test_geometry.py','test_project_settings.py','test_cutter_checks.py','test_regressions.py','test_joint_locks.py','test_blind_kerf.py','test_engine_cli.py','test_curved_roof_fit.py','test_preview.js','render_roof_mounts.py','render_kerf_depth.py','preview.js','ShipoMaster_Aspire.html','verify_all_modes.py','package_gadget.py'):
    shutil.copy2(ROOT/name,sources/name)
(sources/'BUILD.txt').write_text('Python 3.11 x64\npip install shapely pyinstaller lupa ezdxf reportlab pypdf\npython -m unittest discover -s . -p test_*.py\npython -m PyInstaller --onefile --noconsole --name ShipoMasterEngine geometry_worker.py\nCopy dist/ShipoMasterEngine.exe to the gadget __runtime folder.\n',encoding='utf-8')
licenses=folder/'LICENSES';licenses.mkdir(exist_ok=True)
for package in ('shapely','numpy','pyinstaller','ezdxf','reportlab','pillow','fonttools','pyparsing','typing_extensions','charset_normalizer'):
    dist=importlib.metadata.distribution(package)
    for item in dist.files or []:
        if ('license' in str(item).lower() or 'copying' in str(item).lower()) and str(item).endswith(('.txt','.rst','.md','LICENSE','COPYING')):
            src=dist.locate_file(item)
            if src.is_file():shutil.copy2(src,licenses/(package+'_'+src.name))
python_license=Path(sys.base_prefix)/'LICENSE.txt'
if python_license.is_file():shutil.copy2(python_license,licenses/'Python_LICENSE.txt')
archive=ROOT/f'ShipoMaster_Aspire_{VERSION}.vgadget'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for path in folder.rglob('*'):
        if path.is_file():z.write(path,path.relative_to(folder.parent))
print(archive)
print('Size:',archive.stat().st_size)
if '--install' in sys.argv:
    target=Path(r'C:\Users\Public\Documents\Vectric Files\Gadgets\Aspire V12.5')/NAME
    shutil.copytree(folder,target,dirs_exist_ok=True)
    if (target/'ShipoMasterEngine.exe').exists():
        (target/'ShipoMasterEngine.exe').replace(target/'__runtime/ShipoMasterEngine.exe')
    print('Installed:',target)
