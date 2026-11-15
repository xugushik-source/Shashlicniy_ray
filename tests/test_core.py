import unittest,tempfile,concurrent.futures
from pathlib import Path
from core import Store,BusinessError
class CoreTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Store(Path(self.tmp.name)/'test.sqlite')
  self.p={'id':'test','names':{'ru':'Тест','ka':'ტესტი','hy':'Թեստ'},'category':'pork','price':2000,'cost':700,'grams':350,'active':1}
  self.s.product(self.p);self.s.receive({'id':'test','quantity':10,'unit_cost':700})
 def tearDown(self):self.tmp.cleanup()
 def order(self,key='test-key-123',quantity=2):
  return self.s.create_order({'items':[{'id':'test','quantity':quantity}],'phone':'+995555555555','address':'test address','confirmed_total':quantity*2000},key)
 def test_idempotency_and_reservation(self):
  a=self.order();b=self.order();self.assertEqual(a,b);self.assertEqual(self.s.catalog()[0]['stock'],8)
 def test_concurrent_last_stock(self):
  def attempt(key):
   try:return self.order(key,7)
   except BusinessError:return None
  with concurrent.futures.ThreadPoolExecutor() as pool:r=list(pool.map(attempt,['parallel-111','parallel-222']))
  self.assertEqual(sum(x is not None for x in r),1);self.assertEqual(self.s.catalog()[0]['stock'],3)
 def test_cancellation_and_no_revenue(self):
  o=self.order();self.s.transition(o['id'],'cancelled');self.s.transition(o['id'],'cancelled');self.assertEqual(self.s.catalog()[0]['stock'],10);self.assertEqual(self.s.report()['gross_profit'],0)
 def test_delivered_refund_historical_cost(self):
  o=self.order();self.s.product(dict(self.p,cost=900))
  for status in ['confirmed','preparing','ready','delivering','delivered']:self.s.transition(o['id'],status)
  r=self.s.report();self.assertEqual(r['gross_profit'],2600);self.assertEqual(r['receivable'],4000);self.assertNotIn('cash',r)
  self.s.transition(o['id'],'refunded');self.assertEqual(self.s.report()['gross_profit'],-1400);self.assertEqual(self.s.catalog()[0]['stock'],8)
 def test_feast(self):
  q=self.s.feast({'adults':4,'children':1});self.assertGreaterEqual(q['grams'],1580)
  with self.assertRaises(BusinessError):self.s.feast({'adults':4,'budget':1})
 def test_client_price(self):
  with self.assertRaises(BusinessError):self.s.create_order({'items':[{'id':'test','quantity':2}],'phone':'123456789','address':'address','confirmed_total':1},'test-price-key')
  self.assertEqual(self.s.catalog()[0]['stock'],10)
 def test_state_machine(self):
  o=self.order()
  with self.assertRaises(BusinessError):self.s.transition(o['id'],'delivered')
 def test_waste(self):
  o=self.order()
  for x in ['confirmed','preparing','cancelled']:self.s.transition(o['id'],x)
  self.assertEqual(self.s.catalog()[0]['stock'],8);self.assertEqual(self.s.report()['waste'],1400)
if __name__=='__main__':unittest.main()
