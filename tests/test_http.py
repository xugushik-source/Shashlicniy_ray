import unittest,subprocess,tempfile,os,socket,time,json,urllib.request,urllib.error
class HTTPTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory()
  with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  cls.base=f'http://127.0.0.1:{port}'
  cls.proc=subprocess.Popen(['python3','server.py'],env=dict(os.environ,PORT=str(port),DATABASE_PATH=cls.tmp.name+'/test.sqlite',ADMIN_TOKEN='test-only-token'),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  for _ in range(100):
   try:urllib.request.urlopen(cls.base+'/api/catalog');return
   except OSError:time.sleep(.03)
  raise RuntimeError('server failed to start')
 @classmethod
 def tearDownClass(cls):cls.proc.terminate();cls.proc.wait();cls.proc.stderr.close();cls.tmp.cleanup()
 def request(self,path,data=None,token=None):
  headers={'Content-Type':'application/json'}
  if token:headers['Authorization']='Bearer '+token
  req=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data else None,headers=headers)
  try:
   with urllib.request.urlopen(req) as r:return r.status,json.load(r)
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def test_admin_auth(self):self.assertEqual(self.request('/api/admin/report')[0],403)
 def test_no_cost_disclosure(self):
  p={'id':'public-test','names':{'ru':'Тест','ka':'ტესტი','hy':'Թեստ'},'category':'pork','price':100,'cost':40,'grams':100,'active':1}
  self.assertEqual(self.request('/api/admin/product',p,'test-only-token')[0],200)
  code,result=self.request('/api/catalog');self.assertNotIn('cost',result['products'][0])
 def test_tracking_requires_token(self):self.assertEqual(self.request('/api/order')[0],404)
 def test_path_traversal(self):self.assertEqual(self.request('/../server.py')[0],404)

 def test_storefront_and_order_flow(self):
  with urllib.request.urlopen(self.base+'/') as r:
   html=r.read().decode();self.assertEqual(r.status,200);self.assertIn('productDialog',html);self.assertIn('trackingResult',html);self.assertIn('Content-Security-Policy',r.headers)
  p={'id':'flow-test','names':{'ru':'Тест','ka':'ტესტი','hy':'Թեստ'},'category':'pork','price':100,'cost':40,'grams':350,'active':1,'details':{'description':{'ru':'Описание'},'allergens':{'ru':'Нет'}}}
  self.assertEqual(self.request('/api/admin/product',p,'test-only-token')[0],200)
  self.assertEqual(self.request('/api/admin/receive',{'id':'flow-test','quantity':5,'unit_cost':40},'test-only-token')[0],200)
  code,q=self.request('/api/quote',{'items':[{'id':'flow-test','quantity':2}]});self.assertEqual(q['total'],200);self.assertNotIn('cost',q['lines'][0])
  body={'items':[{'id':'flow-test','quantity':2}],'phone':'123456789','address':'Test address','confirmed_total':q['total']}
  req=urllib.request.Request(self.base+'/api/orders',data=json.dumps(body).encode(),headers={'Content-Type':'application/json','Idempotency-Key':'http-flow-test-key'})
  with urllib.request.urlopen(req) as r:o=json.load(r)
  self.assertEqual(self.request('/api/order',token=o['token'])[1]['status'],'new')
  for status in ['confirmed','preparing','ready','delivering','delivered']:
   self.assertEqual(self.request('/api/admin/transition',{'id':o['id'],'status':status},'test-only-token')[0],200)
  self.assertEqual(self.request('/api/order',token=o['token'])[1]['status'],'delivered')
