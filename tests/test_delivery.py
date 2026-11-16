import unittest,tempfile
from pathlib import Path
from core import delivery_settings,resolve_delivery_city,BusinessError
from run_demo import prepare
class DeliveryTest(unittest.TestCase):
 def test_only_launch_city_is_active(self):
  s=delivery_settings();self.assertEqual(s['default_city_id'],'akhalkalaki');self.assertEqual([c['id'] for c in s['cities'] if c['active']],['akhalkalaki'])
  self.assertEqual(resolve_delivery_city()['id'],'akhalkalaki')
  for id in ('tbilisi','batumi','ninotsminda','unknown',''):
   with self.assertRaisesRegex(BusinessError,'CITY_UNAVAILABLE'):resolve_delivery_city(id)
 def test_closed_city_cannot_create_local_order(self):
  with tempfile.TemporaryDirectory() as temp:
   s=prepare(Path(temp)/'orders.sqlite')
   with self.assertRaisesRegex(BusinessError,'CITY_UNAVAILABLE'):s.create_order({'city_id':'tbilisi'},'closed-city-test')
   self.assertEqual(s.report()['orders'],0)
