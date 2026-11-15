"""Build an attributed demo catalogue using downloaded public menu data."""
import json,re,hashlib,shutil,sys
from pathlib import Path
from decimal import Decimal,ROUND_CEILING
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'static/media'
def convert(rub,rate,quantity):return int((Decimal(str(rub))*Decimal(str(rate))/Decimal(str(quantity))).to_integral_value(rounding=ROUND_CEILING))*100
def category(name,cat):
 n=name.lower();c=(cat or '').lower()
 if re.search(r'\b(?:вино|водка|пиво|коньяк)\b',n):return 'alcohol'
 if 'ассорти' in n and any(x in c for x in ['набор','sety']):return 'combo'
 if 'люля' in n:return 'lula'
 if any(x in c for x in ['рыба','fish']) or any(x in n for x in ['семга','сёмга','форель','сибас','дорадо','лосось','осетрина']):return 'fish'
 if any(x in c for x in ['овощ','ovoshi']):return 'vegetables'
 if 'салат' in c or c=='salaty':return 'salads'
 if 'соус' in c or c=='sousy':return 'sauces'
 if 'напит' in c or c=='napitki':return 'drinks'
 if 'гарнир' in c or c=='garniry':return 'sides'
 if 'бара' in c or any(x in n for x in ['баран','ягнен','ягнён']):return 'lamb'
 if 'птица' in c or any(x in n for x in ['кури','индей','цыпл']):return 'poultry'
 if 'говя' in c or any(x in n for x in ['говя','теля']):return 'beef'
 if 'свин' in c or any(x in n for x in ['свин','шея']):return 'pork'
 if 'лаваш' in n or 'хлеб' in n or 'лепеш' in n:return 'bread'
 return 'snacks'
def metadata():
 return json.loads((ROOT/'demo/source_metadata.json').read_text())

def build():
 rates=json.loads((ROOT/'demo/exchange_snapshot.json').read_text());rate=next(x for x in rates[0]['currencies'] if x['code']=='RUB');meta=metadata();products=[];seen=set()
 for row in json.loads((ROOT/'demo/photo_sources.json').read_text()):
  filename=hashlib.sha256(row['image_url'].encode()).hexdigest()[:16]+Path(row['file']).suffix
  original=SOURCE/filename
  if not original.is_file():raise FileNotFoundError('Missing source photograph: '+filename)
  for item in row['menu_items']:
   name=item['name'].strip();key=(row['source_site'],item['page'])
   if key in seen:continue
   seen.add(key);cat=category(name,item['category'])
   if not cat:continue
   m=meta.get(name,{});weight=m.get('weight');weight=int(weight) if isinstance(weight,(int,float)) and weight>0 else None
   desc=m.get('description') or ''
   products.append({'id':'demo-'+hashlib.sha256(str(key).encode()).hexdigest()[:16],'names':{'ru':name,'ka':name,'hy':name},'category':cat,'price':convert(item['price'],rate['rate'],rate['quantity']),'grams':weight or 1,'stock':100,'active':1,'details':{'demo':True,'image':'/media/'+filename,'weight_unknown':weight is None,'source_price_rub':item['price'],'source_page':item['page'],'source_site':row['source_site'],'description':{'ru':desc,'ka':'','hy':''},'translations_pending':True}})
 translations={}
 for line in (ROOT/'demo/translations.tsv').read_text().splitlines():
  ru,ka,hy,en=line.split('|');translations[ru]={'ru':ru,'ka':ka,'hy':hy,'en':en}
 for p in products:
  p['names']=translations[p['names']['ru']];p['details']['translations_pending']=False;p['details']['description']['en']=''
 info={'provider':'National Bank of Georgia','source':'https://nbg.gov.ge/gw/api/ct/monetarypolicy/currencies/en/json/','valid_from':rate['validFromDate'],'rub_quantity':rate['quantity'],'gel_rate':rate['rate'],'rounding':'ceil_to_whole_GEL'}
 (ROOT/'demo/catalog.json').write_text(json.dumps({'exchange':info,'products':products},ensure_ascii=False,indent=2))
 print(json.dumps({'products':len(products),'known_weights':sum(not p['details']['weight_unknown'] for p in products),'rate':info},ensure_ascii=False))
if __name__=='__main__':build()
