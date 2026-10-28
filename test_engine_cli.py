"""Integration tests against the built executable, including per-part DXF export."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from lupa import LuaRuntime
from verify_all_modes import verify
from version import VERSION

ENGINE = Path(__file__).parent / 'bin' / 'ShipoMasterEngine.exe'


@unittest.skipUnless(ENGINE.exists(), 'Build the engine EXE first')
class EngineCliTests(unittest.TestCase):
    def run_engine(self, folder, text):
        request = folder / 'request.txt'
        output = folder / 'result.lua'
        request.write_text(text, encoding='utf-8-sig')
        subprocess.run([str(ENGINE.resolve()), str(request), str(output)],
                       check=True, timeout=60)
        result = json.loads(output.with_suffix('.json').read_text(encoding='utf-8'))
        native = LuaRuntime().execute(output.read_text(encoding='utf-8'))
        self.assertEqual(result['ok'], native.ok)
        return result

    def test_all_nine_modes_export_with_lua_response(self):
        with tempfile.TemporaryDirectory(prefix='ShipoMaster проверка ') as temp:
            for mode,mount,cut in [(m,0,-1) for m in range(9)]+[(8,1,1),(8,0,2),(8,1,2)]:
                with self.subTest(mode=mode,mount=mount,cut=cut):
                    folder = Path(temp) / f'{mode}_{mount}_{cut}'
                    folder.mkdir()
                    result = self.run_engine(folder,
                        f'mode={mode}\nroof_mount={mount}\nroof_cut_type={cut}\nbottom_in_grooves={str(cut==2).lower()}\ndMaterial=4\ndFreza=4\ncount_mode=1\n'
                        'KolPeregorodokPoDline=2\nKolPeregorodokPoShirine=1\n'
                        f'export_dir={folder}\n')
                    self.assertTrue(result['ok'], result)
                    self.assertEqual(result['version'], VERSION)
                    verify(result)
                    if cut==2:
                        notes=list(folder.glob('*KERF_DEPTH.txt'))
                        self.assertEqual(len(notes),1)
                        self.assertIn('3.4000',notes[0].read_text(encoding='utf-8-sig'))
                        self.assertEqual(result['roof']['cut_pattern'],'blind_kerf')
                    files = list(folder.glob('*.dxf'))
                    self.assertEqual(len(files), len(result['parts']))
                    for path in files:
                        text = path.read_text(encoding='ascii')
                        self.assertIn('$INSUNITS\n70\n4\n', text)
                        self.assertTrue(text.endswith('0\nEOF\n'))

    def test_invalid_input_writes_error_without_dxf(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            result = self.run_engine(folder, f'shirina=nan\nexport_dir={folder}\n')
            self.assertFalse(result['ok'])
            self.assertIn('shirina', result['error'])
            self.assertFalse(list(folder.glob('*.dxf')))

    def test_closed_mortise_clearance_in_built_engine(self):
        from shapely.geometry import Polygon
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            result=self.run_engine(folder,'mode=2\ndMaterial=4\ndFreza=4\nZazor=0.05\n')
            self.assertTrue(result['ok'],result)
            self.assertGreater(result['joint_lock_count'],0)
            holes=[Polygon(c['points']) for p in result['parts']
                   for c in p['contours'] if c.get('hole')]
            self.assertTrue(holes)
            for hole in holes:
                centers=hole.buffer(-2)
                self.assertEqual(centers.geom_type,'Polygon')
                self.assertGreater(centers.area,0)
            result=self.run_engine(folder,'mode=2\ndMaterial=4\ndFreza=4\nZazor=0\n')
            self.assertFalse(result['ok'])
            self.assertIn('4.10',result['error'])


if __name__ == '__main__':
    unittest.main()
