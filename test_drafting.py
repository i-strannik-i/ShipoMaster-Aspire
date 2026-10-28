import io,tempfile,unittest
from pathlib import Path
try:import pymupdf
except ImportError:pymupdf=None
from cage_geometry import build_cage
from cage_drafting import Paper,sheet_groups,specification_rows,select_scale,scale_name,write_cage_pdf

class DrawingTests(unittest.TestCase):
 def test_scales_are_fixed_not_arbitrary_and_fit(self):
  for w,h,bw,bh in [(1000,30,150,14),(600,1000,70,110),(20,30,27,30),(2000,5000,160,180)]:
   s=select_scale(w,h,bw,bh);self.assertLessEqual(w*s,bw+.0001);self.assertLessEqual(h*s,bh+.0001)
   self.assertNotIn('1.11',scale_name(s))
 def test_specification_covers_every_model_mark(self):
  r=build_cage({});p=Paper(io.BytesIO(),r);p.pos={};groups=sheet_groups(r['parts']);rows=specification_rows(p,r,groups)
  for part in r['parts']:self.assertIn(part['name'].split('_')[0],p.pos)
  for tube in r['cage']['tubes']:self.assertIn(tube['id'],p.pos)
  self.assertIn('M5_bolt',p.pos);self.assertIn('M5_rivet_nut',p.pos)
  self.assertEqual(len({row[0] for row in rows}),len(rows))
 @unittest.skipUnless(pymupdf,'Optional PDF renderer: pip install pymupdf')
 def test_titles_hole_data_and_text_inside_frames(self):
  for options in ({},{'cage_self_tap':True},{'CageVentDiameter':8,'CageVentPitch':50},{'CagePdfWidth':420,'CagePdfHeight':297}):
   r=build_cage(options)
   with tempfile.TemporaryDirectory() as temp:
    path=Path(temp)/'drawings.pdf';write_cage_pdf(path,r);doc=pymupdf.open(path)
    alltext='\n'.join(p.get_text() for p in doc)
    self.assertIn('Спецификация сборочной единицы',alltext);self.assertIn('Рабочий чертёж',alltext)
    for page in doc:
     for block in page.get_text('dict')['blocks']:
      for line in block.get('lines',[]):
       for span in line['spans']:
        self.assertTrue(page.rect.contains(pymupdf.Rect(span['bbox'])),(page.number,span['text'],span['bbox']))
    for t in r['cage']['tubes']:
     page=next(p for p in doc if p.get_text().startswith(t['id']+' - труба'))
     text=page.get_text()
     for h in t['holes']:
      from cage_drafting import number
      self.assertIn(number(h['along']),text);self.assertIn(number(h['across']),text)
    doc.close()

if __name__=='__main__':unittest.main()
