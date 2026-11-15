import os,json,secrets,hmac,sqlite3
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from core import Store,BusinessError
ROOT=Path(__file__).parent

def run():
    data=ROOT/'data'; data.mkdir(exist_ok=True,mode=0o700)
    store=Store(os.environ.get('DATABASE_PATH',str(data/'store.sqlite')))
    admin=os.environ.get('ADMIN_TOKEN','')
    demo=os.environ.get('DEMO_MODE')=='1'
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass # do not log customer tokens / PII
        def send(self,status,obj):
            b=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(b)
        def privileged(self):
            if not admin or not hmac.compare_digest(self.headers.get('Authorization',''),'Bearer '+admin): raise PermissionError()
        def do_GET(self):
            path=urlparse(self.path).path
            try:
                if path=='/api/settings':
                    settings=json.loads((ROOT/'demo/settings.json').read_text()) if demo else {'demo':False}
                    return self.send(200,settings)
                if path.startswith('/media/'):
                    name=path.removeprefix('/media/')
                    if not name or '/' in name or '..' in name or Path(name).suffix.lower() not in ('.jpg','.jpeg','.png','.webp'):return self.send(404,{'error':'NOT_FOUND'})
                    file=ROOT/'static/media'/name
                    if not file.is_file():return self.send(404,{'error':'NOT_FOUND'})
                    content=file.read_bytes();self.send_response(200);self.send_header('Content-Type','image/'+('jpeg' if file.suffix.lower() in ('.jpg','.jpeg') else file.suffix[1:]));self.send_header('Cache-Control','public, max-age=86400');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(content);return
                if path=='/api/catalog': return self.send(200,{'products':[{k:v for k,v in p.items() if k!='cost'} for p in store.catalog()]})
                if path.startswith('/api/admin/'):
                    self.privileged()
                    if path.endswith('/catalog'): return self.send(200,store.catalog(True))
                    if path.endswith('/report'): return self.send(200,store.report())
                    if path.endswith('/orders'):
                        with store.db() as c:return self.send(200,[dict(r) for r in c.execute('SELECT id,phone,address,status,total,created FROM orders ORDER BY created DESC LIMIT 200')])
                if path=='/api/order':
                    token=self.headers.get('Authorization','').removeprefix('Bearer ')
                    with store.db() as c:
                        r=c.execute('SELECT id,status,total,created FROM orders WHERE token=?',(token,)).fetchone()
                    return self.send(200,dict(r)) if r else self.send(404,{'error':'NOT_FOUND'})
                files={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}
                if path not in files:return self.send(404,{'error':'NOT_FOUND'})
                b=(ROOT/'static'/files[path]).read_bytes(); self.send_response(200);self.send_header('Content-Type',{'html':'text/html; charset=utf-8','js':'text/javascript; charset=utf-8','css':'text/css'}[files[path].split('.')[-1]]);self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; img-src 'self' https:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'");self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(b)
            except PermissionError:self.send(403,{'error':'FORBIDDEN'})
        def do_POST(self):
            try:
                # Browser mutations must be same-origin; bearer-only admin has no ambient credentials.
                if self.headers.get('Sec-Fetch-Site')=='cross-site':raise PermissionError()
                if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send(415,{'error':'JSON_REQUIRED'})
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=65536:return self.send(413,{'error':'BODY_LIMIT'})
                p=json.loads(self.rfile.read(length)); path=urlparse(self.path).path
                if not isinstance(p,dict):raise BusinessError('INVALID_BODY')
                if path=='/api/quote':
                    q=store.quote(p.get('items'));q['lines']=[{k:v for k,v in l.items() if k!='cost'} for l in q['lines']];return self.send(200,q)
                if path=='/api/feast':
                    q=store.feast(p);q['lines']=[{k:v for k,v in l.items() if k!='cost'} for l in q['lines']];return self.send(200,q)
                if path=='/api/orders':
                    if demo:
                        q=store.quote(p.get('items'))
                        if p.get('confirmed_total')!=q['total']:raise BusinessError('PRICE_CHANGED')
                        return self.send(200,{'demo':True,'id':'DEMO-'+secrets.token_hex(4).upper(),'total':q['total'],'payment':'not_charged'})
                    return self.send(201,store.create_order(p,self.headers.get('Idempotency-Key')))
                if path.startswith('/api/admin/'):
                    self.privileged()
                    if demo:return self.send(403,{'error':'DEMO_READ_ONLY'})
                    if path.endswith('/product'):return self.send(200,store.product(p))
                    if path.endswith('/receive'):return self.send(200,store.receive(p))
                    if path.endswith('/transition'):return self.send(200,store.transition(p.get('id'),p.get('status')))
                self.send(404,{'error':'NOT_FOUND'})
            except PermissionError:self.send(403,{'error':'FORBIDDEN'})
            except (BusinessError,ValueError,TypeError,KeyError,AttributeError) as e:self.send(400,{'error':str(e) if isinstance(e,BusinessError) else 'INVALID_BODY'})
            except sqlite3.Error:self.send(409,{'error':'DATABASE_CONFLICT'})
    ThreadingHTTPServer(('127.0.0.1',int(os.environ.get('PORT','8000'))),Handler).serve_forever()
if __name__=='__main__':run()
