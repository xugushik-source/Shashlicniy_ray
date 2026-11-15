import json,unittest
from pathlib import Path
from demo.set_catalog import DEFINITIONS,apply_sets
ROOT=Path(__file__).parents[1]
class SetDescriptionsTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.products=json.loads((ROOT/'demo/catalog.json').read_text())['products'];cls.by_name={p['names']['ru']:p for p in cls.products}
 def test_every_set_has_translated_composition(self):
  for p in self.products:
   if p['category']=='combo':self.assertIn('bundle',p['details'],p['names']['ru'])
  for name in DEFINITIONS:
   b=self.by_name[name]['details']['bundle'];self.assertTrue(b['components'])
   for row in b['components']:
    for lang in ('ru','ka','hy','en'):self.assertTrue(row['names'][lang])
 def test_exact_source_amounts_and_guests(self):
  b=self.by_name['Ассорти №1']['details']['bundle'];self.assertEqual((b['servings']['min'],b['servings']['max'],b['servings']['basis']),(5,7,'source'))
  self.assertEqual(next(r for r in b['components'] if r['key']=='pork')['quantity'],2)
  self.assertEqual(next(r for r in b['components'] if r['key']=='garlic')['grams'],100)
  b=self.by_name['Ассорти корпоративный']['details']['bundle'];self.assertEqual(next(r for r in b['components'] if r['key']=='potato_plain')['grams'],1250)
  self.assertEqual(next(r for r in b['components'] if r['key']=='khachapuri')['quantity'],3)
 def test_unknowns_and_estimates_are_never_source_facts(self):
  p=self.by_name['Ассорти от шефа'];self.assertEqual(p['grams'],1500);self.assertEqual(p['details']['bundle']['servings']['basis'],'estimate')
  self.assertTrue(all(r['quantity'] is None and r['grams'] is None for r in p['details']['bundle']['components']))
  b=self.by_name['Ассорти праздничный']['details']['bundle'];self.assertEqual(b['servings']['basis'],'unknown');self.assertIsNone(b['servings']['min'])
  self.assertEqual(next(r for r in b['components'] if r['key']=='khachapuri')['grams'],1000);self.assertNotIn('khachapuri_weight_ambiguous',b['notes'])
 def test_catalogue_rebuild_preserves_structured_sets(self):
  copy=json.loads(json.dumps(self.products));apply_sets(copy)
  self.assertEqual([p['details'].get('bundle') for p in copy],[p['details'].get('bundle') for p in self.products])

 def test_owner_confirms_khachapuri_weight_per_piece_and_full_set_totals(self):
  for name,count,total in [('Ассорти корпоративный',3,9450),('Ассорти праздничный',2,6250)]:
   p=self.by_name[name];b=p['details']['bundle'];r=next(x for x in b['components'] if x['key']=='khachapuri')
   self.assertEqual(r['grams_per_piece'],500);self.assertEqual(r['quantity'],count);self.assertEqual(r['grams'],count*500)
   self.assertEqual(sum(x['grams'] for x in b['components']),total);self.assertEqual(p['grams'],total);self.assertFalse(p['details']['weight_unknown'])
