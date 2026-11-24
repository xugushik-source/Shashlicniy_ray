"""Import owner-supplied prices into a local SQLite DB or private D1 SQL file.
Never put approved supplier prices in Git. No network or production operations.
"""
import argparse,json,sqlite3,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def selling_price(cost):
    if type(cost) is not int or not 0<=cost<=100000000:raise ValueError('INVALID_COST')
    return ((cost*120+9999)//10000)*100

def load_prices(path):
    source=Path(path).resolve()
    if source.is_relative_to(ROOT):raise ValueError('Private input must be outside repository')
    rows=json.loads(source.read_text());catalog={p['id']:p for p in json.loads((ROOT/'demo/catalog.json').read_text())['products']};seen=set()
    for r in rows:
        p=catalog.get(r['product_id'])
        if not p or r['product_id'] in seen or r['sale_minor']!=selling_price(r['cost_minor']) or p['price']!=r['sale_minor'] or p['pricing_status']!='approved' or r['unit']!=p['details']['sale_unit']:raise ValueError('INVALID_APPROVAL')
        seen.add(r['product_id'])
    return rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--sql-output');parser.add_argument('--local-db');args=parser.parse_args();rows=load_prices(args.input)
    if bool(args.sql_output)==bool(args.local_db):parser.error('Choose exactly one destination')
    if args.sql_output:
        out=Path(args.sql_output).resolve()
        if out.is_relative_to(ROOT):raise ValueError('Private SQL must be outside repository')
        def literal(v):return str(v) if type(v) is int else "'"+str(v).replace("'","''")+"'"
        sql=[]
        for r in rows:
            values=[r[k] for k in ['product_id','cost_minor','sale_minor','unit','revision','supplier']]
            sql.append('INSERT INTO supplier_prices(product_id,cost_minor,sale_minor,unit,revision,supplier) VALUES('+','.join(map(literal,values))+') ON CONFLICT(product_id) DO UPDATE SET cost_minor=excluded.cost_minor,sale_minor=excluded.sale_minor,unit=excluded.unit,revision=excluded.revision,supplier=excluded.supplier;')
        out.write_text('\n'.join(sql)+'\n');out.chmod(0o600)
    else:
        path=Path(args.local_db).resolve()
        if not path.is_file():raise ValueError('Prepare isolated local catalog DB first')
        with sqlite3.connect(path) as db:
            for r in rows:
                p=db.execute('SELECT details FROM products WHERE id=?',(r['product_id'],)).fetchone()
                if not p:raise ValueError('MISSING_LOCAL_PRODUCT')
                details=json.loads(p[0]);details['price_revision']=r['revision']
                db.execute('UPDATE products SET cost=?,price=?,price_approved=?,details=? WHERE id=?',(r['cost_minor'],r['sale_minor'],0 if details.get('identity_pending') else 1,json.dumps(details,ensure_ascii=False),r['product_id']))
    print('Private price import prepared:',len(rows),'rows; no production changes')
if __name__=='__main__':main()
