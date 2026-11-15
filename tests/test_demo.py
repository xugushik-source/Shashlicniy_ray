import unittest,tempfile,json
from pathlib import Path
from demo.build_catalog import convert
from run_demo import prepare
class DemoTest(unittest.TestCase):
 def test_conversion_rounds_up(self):
  self.assertEqual(convert(610,'3.154',100),2000)
  self.assertEqual(convert(1010,'3.154',100),3200)
 def test_isolation_and_photo_paths(self):
  with tempfile.TemporaryDirectory() as temp:
   s=prepare(Path(temp)/'demo.sqlite');products=s.catalog()
   self.assertEqual(len(products),186)
   self.assertTrue(all(p['category']!='alcohol' for p in products if 'свин' in p['names']['ru'].lower()))
   self.assertTrue(all(all(p['names'].get(l) for l in ('ru','ka','hy','en')) for p in products))
   for p in products:
    self.assertTrue(p['details']['demo'])
    self.assertEqual(p['price']%100,0)
    self.assertTrue((Path(__file__).parents[1]/'static'/p['details']['image'].lstrip('/')).is_file())
   self.assertEqual(s.report()['orders'],0)
   prepare(Path(temp)/'demo.sqlite');self.assertEqual(len(s.catalog()),186)
 def test_feast_excludes_unknown_weights(self):
  with tempfile.TemporaryDirectory() as temp:
   s=prepare(Path(temp)/'demo.sqlite');q=s.feast({'adults':4,'children':0});lookup={p['id']:p for p in s.catalog()}
   self.assertGreaterEqual(q['grams'],1400)
   self.assertTrue(all(not lookup[l['id']]['details']['weight_unknown'] for l in q['lines'] if l['group']=='hot'))
