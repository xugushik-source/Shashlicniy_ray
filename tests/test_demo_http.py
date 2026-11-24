import unittest,tempfile,subprocess,os,socket,time,json,urllib.request,urllib.error
from pathlib import Path
from run_demo import prepare
class DemoHTTPTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.db=Path(cls.tmp.name)/'demo.sqlite';cls.store=prepare(cls.db)
  with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
  cls.base=f'http://127.0.0.1:{port}';cls.proc=subprocess.Popen(['python3','server.py'],env=dict(os.environ,PORT=str(port),DATABASE_PATH=str(cls.db),DEMO_MODE='1'),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  for _ in range(100):
   try:urllib.request.urlopen(cls.base+'/api/settings');return
   except OSError:time.sleep(.03)
  raise RuntimeError('Demo server failed to start')
 @classmethod
 def tearDownClass(cls):cls.proc.terminate();cls.proc.wait();cls.proc.stderr.close();cls.tmp.cleanup()
 def get(self,path):
  with urllib.request.urlopen(self.base+path) as r:return json.load(r)
 def test_settings_links_and_catalogue(self):
  s=self.get('/api/settings');self.assertTrue(s['demo']);self.assertEqual(s['phone'],'+995591244075');self.assertEqual(s['city']['en'],'Akhalkalaki')
  self.assertEqual(s['payment_links'][1]['url'],'https://transfer.tbcbank.ge/?iban=z5odvB987WFKzWTYmygC6R7SJqhOqgpeAne2Tt+pQ1x/afoCC5+Fzsim8Iww0dhX1GI=')
  products=self.get('/api/catalog')['products'];self.assertEqual(len(products),245)
  with urllib.request.urlopen(self.base+products[0]['details']['image']) as r:self.assertTrue(r.headers['Content-Type'].startswith('image/'));self.assertGreater(len(r.read()),1000)
 def test_demo_orders_never_persist_or_reserve(self):
  p=self.get('/api/catalog')['products'][0];payload={'items':[{'id':p['id'],'quantity':1}],'confirmed_total':p['price'],'payment_method':'cash'}
  req=urllib.request.Request(self.base+'/api/orders',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
  with self.assertRaises(urllib.error.HTTPError) as caught:urllib.request.urlopen(req)
  self.assertEqual(caught.exception.code,400);self.assertEqual(json.load(caught.exception)['error'],'PRICE_UNAPPROVED');self.assertEqual(self.store.report()['orders'],0)
  self.assertEqual(next(x for x in self.store.catalog() if x['id']==p['id'])['stock'],100)
