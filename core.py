import sqlite3, json, uuid, secrets, hashlib, math
from pathlib import Path

class BusinessError(Exception): pass

def delivery_settings():
    config=json.loads((Path(__file__).parent/'config/delivery.json').read_text())
    city=next((city for city in config['cities'] if city['id']==config['default_city_id']),None)
    return dict(config,city=city['names'] if city else {})
def resolve_delivery_city(city_id=None):
    config=delivery_settings()
    if city_id is None:city_id=config['default_city_id']
    city=next((city for city in config['cities'] if city['id']==city_id),None)
    if not isinstance(city_id,str) or not city or city['active'] is not True:raise BusinessError('CITY_UNAVAILABLE')
    return city

def integer(x, low=0, high=100000000):
    if type(x) is not int or not low <= x <= high: raise BusinessError('INVALID_NUMBER')
    return x

class Store:
    def __init__(self, path):
        self.path = str(path)
        with self.db() as c:
            c.executescript((Path(__file__).parent/'migrations/001.sql').read_text())
            if 'price_approved' not in {row[1] for row in c.execute('PRAGMA table_info(products)')}:c.execute('ALTER TABLE products ADD COLUMN price_approved INTEGER NOT NULL DEFAULT 0 CHECK(price_approved IN (0,1))')
            if 'customer_name' not in {row[1] for row in c.execute('PRAGMA table_info(orders)')}:c.execute("ALTER TABLE orders ADD COLUMN customer_name TEXT NOT NULL DEFAULT ''")
    def db(self):
        c=sqlite3.connect(self.path, timeout=15); c.row_factory=sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON'); return c
    def catalog(self, admin=False):
        with self.db() as c:
            return [dict(r, names=json.loads(r['names']), details=json.loads(r['details']),pricing_status='approved' if r['price_approved'] else 'pending',cost_confirmed=bool(r['price_approved']),cost_minor=r['cost'] if r['price_approved'] else None) for r in c.execute('SELECT * FROM products'+('' if admin else ' WHERE active=1'))]
    def product(self,p):
        pid=p.get('id') or str(uuid.uuid4())
        names=p.get('names',{})
        if not all(isinstance(names.get(k),str) and 1<=len(names[k])<=200 for k in ('ru','ka','hy')): raise BusinessError('TRANSLATIONS_REQUIRED')
        category=p.get('category')
        if category not in ('pork','lamb','beef','poultry','fish','tandoor','lula','vegetables','salads','pickles','cheese','herbs','sides','bread','sauces','drinks','desserts','supplies','combo','snacks','alcohol','khinkali','khachapuri','soups','hot'): raise BusinessError('INVALID_CATEGORY')
        details=p.get('details',{})
        if not isinstance(details,dict): raise BusinessError('INVALID_DETAILS')
        if details.get('price_source','').startswith('forel-') and p.get('price')!=((integer(p.get('cost'))*120+9999)//10000)*100:raise BusinessError('INVALID_MARKUP')
        # Stock changes have their own journaled operation.
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            c.execute('INSERT INTO products(id,names,category,price,cost,grams,active,details) VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET names=excluded.names,category=excluded.category,price=excluded.price,cost=excluded.cost,grams=excluded.grams,active=excluded.active,details=excluded.details',(pid,json.dumps(names),category,integer(p.get('price'),1),integer(p.get('cost')),integer(p.get('grams') or 1,1),integer(p.get('active',0),0,1),json.dumps(details)))
            c.execute('UPDATE products SET price_approved=? WHERE id=?',(0 if details.get('identity_pending') else 1,pid))
            c.execute('INSERT INTO audit(actor,action,entity) VALUES(?,?,?)',('owner','product.save',pid))
        return {'id':pid}
    def receive(self,p):
        qty=integer(p.get('quantity'),1,100000); cost=integer(p.get('unit_cost'))
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            if not c.execute('UPDATE products SET stock=stock+? WHERE id=?',(qty,p.get('id'))).rowcount: raise BusinessError('NOT_FOUND')
            c.execute('INSERT INTO movements(product_id,quantity,kind) VALUES(?,?,?)',(p['id'],qty,'receipt'))
            # Inventory acquisition and payable; no P&L expense on acquisition.
            c.executemany('INSERT INTO journal(account,amount) VALUES(?,?)',[('inventory_acquired',qty*cost),('payable',qty*cost)])
            c.execute('INSERT INTO audit(actor,action,entity) VALUES(?,?,?)',('owner','stock.receive',p['id']))
        return {'ok':True}
    def quote(self, items, c=None):
        if not isinstance(items,list) or not 1<=len(items)<=100: raise BusinessError('EMPTY_CART')
        if c is None:
            with self.db() as conn: return self.quote(items,conn)
        lines=[]; seen=set()
        for item in items:
            pid=item.get('id'); q=integer(item.get('quantity'),1,1000)
            if pid in seen: raise BusinessError('DUPLICATE_LINE')
            seen.add(pid); p=c.execute('SELECT * FROM products WHERE id=? AND active=1',(pid,)).fetchone()
            if not p or p['stock']<q: raise BusinessError('OUT_OF_STOCK')
            if not p['price_approved']:raise BusinessError('PRICE_UNAPPROVED')
            lines.append({'id':pid,'quantity':q,'price':p['price'],'names':json.loads(p['names']),'cost':p['cost'],'grams':0 if json.loads(p['details']).get('weight_unknown') else p['grams']})
        return {'lines':lines,'total':sum(l['price']*l['quantity'] for l in lines),'grams':sum(l['grams']*l['quantity'] for l in lines)}
    def feast(self,p):
        # Share the exact hosted planner, rather than maintaining two divergent rulesets.
        import subprocess
        try:
            completed=subprocess.run(['node',str(Path(__file__).parent/'worker/feast-cli.mjs')],input=json.dumps({'catalog':self.catalog(True),'request':dict(p,categories=p.get('categories',['pork','lamb','beef','poultry','lula']),children=p.get('children',0))}),text=True,capture_output=True,timeout=10)
            result=json.loads(completed.stdout)
        except (OSError,subprocess.TimeoutExpired,ValueError):
            raise BusinessError('FEAST_RUNTIME_UNAVAILABLE') from None
        if 'error' in result: raise BusinessError(result['error'])
        return result['result']
    def create_order(self,p,key):
        city=resolve_delivery_city(p.get('city_id'))
        customer_name=p.get('customer_name','')
        if not isinstance(customer_name,str) or len(customer_name.strip())>100 or any(ord(c)<32 or ord(c)==127 for c in customer_name):raise BusinessError('INVALID_NAME')
        if not isinstance(key,str) or not 8<=len(key)<=100: raise BusinessError('IDEMPOTENCY_REQUIRED')
        phone=p.get('phone',''); address=p.get('address','')
        if not isinstance(phone,str) or not 8<=len(phone)<=30 or not isinstance(address,str) or not 5<=len(address)<=500: raise BusinessError('CONTACT_REQUIRED')
        fingerprint=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
        address=address.strip() if address.strip().startswith(city['names']['ru']+',') else city['names']['ru']+', '+address.strip()
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE')
            old=c.execute('SELECT * FROM orders WHERE key=?',(key,)).fetchone()
            if old:
                if old['fingerprint']!=fingerprint: raise BusinessError('IDEMPOTENCY_CONFLICT')
                return {'id':old['id'],'token':old['token'],'total':old['total']}
            quote=self.quote(p.get('items'),c)
            if p.get('confirmed_total')!=quote['total']: raise BusinessError('PRICE_CHANGED')
            oid=str(uuid.uuid4()); token=secrets.token_urlsafe(32); cost=sum(l['cost']*l['quantity'] for l in quote['lines'])
            c.execute('INSERT INTO orders(id,key,fingerprint,token,customer_name,phone,address,status,total,cost) VALUES(?,?,?,?,?,?,?,?,?,?)',(oid,key,fingerprint,token,customer_name.strip(),phone,address,'new',quote['total'],cost))
            for l in quote['lines']:
                c.execute('INSERT INTO lines VALUES(?,?,?,?,?,?)',(oid,l['id'],l['quantity'],l['price'],l['cost'],l['grams']))
                c.execute('UPDATE products SET stock=stock-? WHERE id=?',(l['quantity'],l['id']))
                c.execute('INSERT INTO movements(product_id,order_id,quantity,kind) VALUES(?,?,?,?)',(l['id'],oid,-l['quantity'],'reserve'))
            c.execute('INSERT INTO outbox(event,entity,payload) VALUES(?,?,?)',('order.created',oid,json.dumps({'order_id':oid})))
            c.execute('INSERT INTO audit(actor,action,entity) VALUES(?,?,?)',('guest','order.create',oid))
        return {'id':oid,'token':token,'total':quote['total']}
    def transition(self,oid,status):
        allowed={'new':['confirmed','cancelled'],'confirmed':['preparing','cancelled'],'preparing':['ready','cancelled'],'ready':['delivering','cancelled'],'delivering':['delivered'],'delivered':['refunded']}
        with self.db() as c:
            c.execute('BEGIN IMMEDIATE'); o=c.execute('SELECT * FROM orders WHERE id=?',(oid,)).fetchone()
            if not o: raise BusinessError('NOT_FOUND')
            if status==o['status']: return {'ok':True}
            if status not in allowed.get(o['status'],[]): raise BusinessError('INVALID_TRANSITION')
            if status=='cancelled' and o['status'] in ('new','confirmed'):
                for l in c.execute('SELECT * FROM lines WHERE order_id=?',(oid,)).fetchall():
                    c.execute('UPDATE products SET stock=stock+? WHERE id=?',(l['quantity'],l['product_id']))
                    c.execute('INSERT INTO movements(product_id,order_id,quantity,kind) VALUES(?,?,?,?)',(l['product_id'],oid,l['quantity'],'release'))
            elif status=='cancelled':
                c.execute('INSERT INTO journal(order_id,account,amount) VALUES(?,?,?)',(oid,'waste',o['cost']))
            if status=='delivered':
                c.executemany('INSERT INTO journal(order_id,account,amount) VALUES(?,?,?)',[(oid,'revenue',o['total']),(oid,'cogs',o['cost']),(oid,'receivable',o['total'])])
            if status=='refunded':
                # Prepared food is not returned to sellable inventory; COGS remains.
                c.executemany('INSERT INTO journal(order_id,account,amount) VALUES(?,?,?)',[(oid,'revenue',-o['total']),(oid,'receivable',-o['total'])])
            c.execute('UPDATE orders SET status=? WHERE id=?',(status,oid))
            c.execute('INSERT INTO outbox(event,entity,payload) VALUES(?,?,?)',('order.'+status,oid,'{}'))
            c.execute('INSERT INTO audit(actor,action,entity) VALUES(?,?,?)',('owner','order.'+status,oid))
        return {'ok':True}
    def report(self):
        with self.db() as c:
            sums={r['account']:r['amount'] for r in c.execute('SELECT account,SUM(amount) amount FROM journal GROUP BY account')}
            orders=c.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
        return dict(sums,orders=orders,gross_profit=sums.get('revenue',0)-sums.get('cogs',0),operating_profit_before_tax=sums.get('revenue',0)-sums.get('cogs',0)-sums.get('expense',0)-sums.get('waste',0),currency='GEL')
