"""One-time migration of the supplied ShipBox VBA geometry, retaining its formulas.

Original macro: ShipoYashchik V2.01, May 2015; Ulibka, Superbizon, alleks67.
Only the geometry routines are migrated; Corel UI and file export are excluded.
"""
from pathlib import Path
import re

ROOT = Path(__file__).parent
SOURCE = ROOT.parent.parent / 'Corel' / 'ShipoMaster_CorelDRAW' / 'development'
controls = '''shirina visota dlinna dFreza dMaterial DMaterialDna KolPoVisote KolPoShirine KolPoDlinne DlinaShipa Zazor TolshinaPeregorodok VisotaPeregorodok KolPeregorodokPoDline KolPeregorodokPoShirine SmeshenieDno SmeshenieKr RazmerPror ProrKolPoShirine ProrMezduLin ProrMezduParal ProrRasstOtKraya OptionButton1 OptionButton2 ButtonPoCentru ButtonOtKraya ComboBox1'''.split()
canonical = {s.lower():s for s in controls}
globals_ = 'DelatKrishku, DelatProrezi, DelatPeregorodki, DnoVPaz, Zazor_vokrug_kvadrata'
local_names = set()

def expr(s, condition=False):
    s = s.strip()
    s = re.sub(r'\b(?:frmShip\.)?ComboBox1\.ListIndex\b', 'mode', s, flags=re.I)
    s = re.sub(r'\b(?:frmShip\.)?(\w+)\.(text|Value)\b', lambda m:'F.'+canonical.get(m[1].lower(),m[1]), s, flags=re.I)
    s = re.sub(r'\bfrmShip\.(\w+)\b', lambda m:'F.'+canonical.get(m[1].lower(),m[1]), s, flags=re.I)
    s = re.sub(r'(?<![\w.])\w+\b', lambda m: 'F.'+canonical[m[0].lower()] if m[0].lower() in canonical and m[0].lower() not in local_names else m[0], s)
    for old,new in [('CDbl','float'),('CInt','vint'),('Int','floor'),('Sin','sin'),('Sqr','sqrt'),('And','and'),('Or','or'),('Not','not')]:
        s = re.sub(r'\b'+old+r'\b',new,s,flags=re.I)
    s = s.replace('<>','!=')
    s = re.sub(r',\s*,', ', None,',s)
    if condition:
        s = re.sub(r'(?<![<>!=])=(?!=)', '==',s)
    return s

def routines(text):
    return re.findall(r'(?:Public |Private )?(?:Sub|Function) (\w+)\((.*?)\)(?: As \w+)?\s*\n(.*?)\nEnd (?:Sub|Function)', text, re.S)

ship = (SOURCE/'ship_clean.txt').read_text(encoding='utf-8')
form = (SOURCE/'form_clean.txt').read_text(encoding='utf-8')
selected = [(n,p,b) for n,p,b in routines(ship) if n.startswith(('Вставить','Рисуем'))]
selected += [(n,p,b) for n,p,b in routines(form) if n in ('CommandButton2_Click','CommandButton5_Click')]
out = ['# Migrated geometry from the user-supplied ShipoYashchik V2.01.',
       'from math import floor, sin, sqrt', 'PI = 3.141',
       'def vint(x): return int(round(float(x)))',
       'def ЗаменаТчкНаЗапт(x): return float(x)', '']
for name,params,body in selected:
    paramlist = [p.strip().split(' As ')[0] for p in params.split(',') if p.strip()]
    local_names = {n.lower() for n in paramlist}
    typed = set()
    for line in body.splitlines():
        if line.strip().startswith('Dim '):
            for decl in line.strip()[4:].split(','):
                n=decl.strip().split(' As ')[0];local_names.add(n.lower())
                if ' As Integer' in decl:typed.add(n)
    out += ['def '+name+'('+', '.join(paramlist)+'):', '    global '+globals_]
    for p in params.split(','):
        if ' As Integer' in p: out.append('    '+p.strip().split(' As ')[0]+' = vint('+p.strip().split(' As ')[0]+')')
    indent = 1
    for raw in body.splitlines():
        s=raw.strip()
        if not s or s.startswith("'"): continue
        # No quoted strings in the retained arithmetic except shape names.
        s=s.split("'",1)[0].strip()
        if not s: continue
        if any(x in s for x in ['CreateArtisticText','OrderToBack','BeginCommandGroup','EndCommandGroup','CreateCurve','ClearSelection','SaveParameter','ActiveDocument.Unit','Application.CreateDocument']):
            out.append('    '*indent+'pass');continue
        if s.startswith('Dim '):
            for decl in s[4:].split(','):
                var=decl.strip().split(' As ')[0]
                if var=='Zazor_vokrug_kvadrata': continue
                out.append('    '*indent+var+' = 0')
            continue
        if s.startswith('Set '): s=s[4:]
        if s in ['End If','Wend'] or s.startswith('Next '): indent-=1;continue
        if s=='Else': indent-=1;out.append('    '*indent+'else:');indent+=1;out.append('    '*indent+'pass');continue
        if s.startswith('If ') and s.endswith(' Then'):
            out.append('    '*indent+'if '+expr(s[3:-5],True)+':');indent+=1;continue
        if s.startswith('While '):
            out.append('    '*indent+'while '+expr(s[6:],True)+':');indent+=1;continue
        if s.startswith('For '):
            m=re.match(r'For (\w+) = (.*?) To (.*)',s)
            out.append('    '*indent+f'for {m[1]} in range(vint({expr(m[2])}), vint({expr(m[3])})+1):');indent+=1;continue
        if s=='CommandButton5_Click': s+='()'
        # VBA permits a procedure call without parentheses.
        m=re.match(r'([\w.]+) (.*)',s)
        if m and not s.startswith(('If ',)) and '=' not in s and not s.startswith('pass'):
            s=m[1]+'('+m[2]+')'
        converted=expr(s)
        assign=re.match(r'^(\w+) = (.*)',converted)
        if assign and assign[1] in typed:
            converted=assign[1]+' = vint('+assign[2]+')'
        out.append('    '*indent+converted)
    if indent != 1: raise ValueError((name,indent))
    out.append('')
(ROOT/'migrated_geometry.py').write_text('\n'.join(out)+'\n',encoding='utf-8')
compile('\n'.join(out), 'migrated_geometry.py', 'exec')
print('Migrated',len(selected),'routines')
