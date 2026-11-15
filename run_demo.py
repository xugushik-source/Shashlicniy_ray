"""Run the isolated demo. Does not enable payments or send Telegram messages."""
import json,os
from pathlib import Path
from core import Store
ROOT=Path(__file__).parent

def prepare(path):
    store=Store(path)
    with store.db() as c:
        if c.execute('SELECT COUNT(*) FROM products').fetchone()[0]:return store
        for p in json.loads((ROOT/'demo/catalog.json').read_text())['products']:
            c.execute('INSERT INTO products(id,names,category,price,cost,grams,stock,active,details) VALUES(?,?,?,?,?,?,?,?,?)',(p['id'],json.dumps(p['names'],ensure_ascii=False),p['category'],p['price'],0,p['grams'],p['stock'],1,json.dumps(p['details'],ensure_ascii=False)))
    return store
if __name__=='__main__':
    data=ROOT/'data';data.mkdir(exist_ok=True,mode=0o700)
    path=str(data/'demo.sqlite');prepare(path)
    os.environ['DATABASE_PATH']=path;os.environ['DEMO_MODE']='1'
    from server import run
    print('ДЕМО: http://127.0.0.1:'+os.environ.get('PORT','8000'),flush=True)
    run()
