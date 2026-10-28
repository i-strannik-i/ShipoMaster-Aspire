import hashlib,io,json,unittest
from pathlib import Path
from unittest.mock import patch
import gadget_updates as u

class UpdateTests(unittest.TestCase):
 def manifest(self,content=b'package',version='1.5.3'):
  return dict(version=version,url=f'https://github.com/{u.REPO}/releases/download/v{version}/ShipoMaster_Aspire_{version}.vgadget',sha256=hashlib.sha256(content).hexdigest())
 def test_manifest_is_public_and_needs_no_authentication(self):
  body=json.dumps(self.manifest()).encode()
  with patch.object(u.urllib.request,'urlopen',return_value=io.BytesIO(body)) as request:
   self.assertEqual(u.read_manifest()['version'],'1.5.3')
   req=request.call_args.args[0]
   self.assertTrue(req.full_url.startswith('https://raw.githubusercontent.com/'))
   self.assertNotIn('Authorization',req.headers);self.assertNotIn('Cookie',req.headers)
 def test_version_comparison_and_no_downgrade(self):
  self.assertGreater(u.version_tuple('1.10.0'),u.version_tuple('1.9.9'))
  for version in ['1.5.2','1.5.1']:
   with patch.object(u,'read_manifest',return_value=self.manifest(version=version)):
    self.assertFalse(u.check_update('1.5.2')['available'])
    self.assertFalse(u.download_update('1.5.2',False)['available'])
 def test_new_release_and_offline_retry(self):
  with patch.object(u,'read_manifest',return_value=self.manifest()):self.assertTrue(u.check_update('1.5.2')['available'])
  with patch.object(u,'read_manifest',side_effect=OSError('offline')):
   result=u.check_update('1.5.2');self.assertTrue(result['ok']);self.assertFalse(result['available']);self.assertIn('Не удалось',result['message'])
 def test_url_and_checksum_validation(self):
  for changes in [{'url':'https://example.com/file'},{'sha256':'bad'},{'version':'../bad'}]:
   with self.assertRaises(ValueError):u.validated_manifest(dict(self.manifest(),**changes))
 def test_download_hash_and_failed_file_cleanup(self):
  for valid in [True,False]:
   data=b'package';manifest=self.manifest(data if valid else b'other')
   with patch.object(u,'read_manifest',return_value=manifest),patch.object(u.urllib.request,'urlopen',return_value=io.BytesIO(data)):
    if valid:
     result=u.download_update('1.5.2',False);self.assertEqual(Path(result['path']).read_bytes(),data)
    else:
     with self.assertRaisesRegex(ValueError,'сумма'):u.download_update('1.5.2',False)
 def test_lua_update_callbacks_keep_inputs(self):
  from test_project_settings import ProjectSettingsTests
  l=ProjectSettingsTests().runtime();l.globals().main('unused')
  l.execute("os.execute=function() end;loadfile=function() return function() return {ok=true,available=true,message='New release'} end end")
  before=l.globals().fields.CageWidth
  l.globals().OnLuaButton_CheckUpdate(l.globals().dialog)
  self.assertEqual(l.globals().labels.about_update_status,'New release');self.assertEqual(l.globals().fields.update_available,'1')
  l.globals().OnLuaButton_InstallUpdate(l.globals().dialog)
  self.assertEqual(l.globals().fields.update_available,'0');self.assertEqual(l.globals().fields.CageWidth,before)

if __name__=='__main__':unittest.main()
