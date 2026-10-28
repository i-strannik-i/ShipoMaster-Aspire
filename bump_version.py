"""Synchronize release labels: python bump_version.py 1.2.0."""
from pathlib import Path
import re
import sys
from version import VERSION

root = Path(__file__).resolve().parent
new = sys.argv[1] if len(sys.argv) == 2 else ''
if not re.fullmatch(r'\d+\.\d+\.\d+', new):
    raise SystemExit('Usage: python bump_version.py MAJOR.MINOR.PATCH')
for name in ['ShipoMaster_Aspire.lua', 'ShipoMaster_Aspire.html', 'README_RU.txt', 'geometry_worker.py']:
    p = root / name
    p.write_text(p.read_text(encoding='utf-8').replace(VERSION, new), encoding='utf-8')
(root / 'version.py').write_text(f'VERSION = "{new}"\n', encoding='utf-8')
print(new)
