"""Export a portable, clearly labelled demo. No server, payments or Telegram calls."""
import json,re,shutil,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def export():
 out=ROOT/'demo-preview';out.mkdir(exist_ok=True)
 products=json.loads((ROOT/'demo/catalog.json').read_text())['products'];settings=json.loads((ROOT/'demo/settings.json').read_text())
 data=json.dumps({'products':products,'settings':settings},ensure_ascii=False).replace('</','<\\/')
 adapter='''const demoData=DEMO_DATA;
// This adapter performs local demo calculations only. It never sends network requests.
window.fetch=async function(path,options={}){
 let p={};try{p=JSON.parse(options.body||'{}')}catch{return response(400,{error:'INVALID_BODY'})}
 function response(status,data){return {ok:status>=200&&status<300,status,json:async()=>data}}
 function quote(items){if(!Array.isArray(items)||!items.length)throw Error('EMPTY_CART');const seen=new Set();let total=0,grams=0;const lines=[];for(const l of items){const product=demoData.products.find(x=>x.id===l.id);if(!product||!Number.isInteger(l.quantity)||l.quantity<1||l.quantity>product.stock||seen.has(l.id))throw Error('OUT_OF_STOCK');seen.add(l.id);total+=product.price*l.quantity;grams+=product.grams*l.quantity;lines.push({id:product.id,quantity:l.quantity,price:product.price,grams:product.grams})}return {lines,total,grams}}
 try{
 if(path==='/api/settings')return response(200,demoData.settings);
 if(path==='/api/catalog')return response(200,{products:rankCatalog(demoData.products)});
 if(path==='/api/quote')return response(200,quote(p.items));
 if(path==='/api/feast')return response(200,buildFeast(demoData.products,p));
 if(path==='/api/recommendations')return response(200,{recommendations:recommendProducts(demoData.products,p.selected||[],{allowAlcohol:p.allowAlcohol===true})});
 if(path==='/api/orders'){const q=quote(p.items);if(q.total!==p.confirmed_total)throw Error('PRICE_CHANGED');return response(200,{id:'DEMO-'+Math.random().toString(16).slice(2,10).toUpperCase(),total:q.total,demo:true,payment:'not_charged'})}
 return response(403,{error:'DEMO_READ_ONLY'});
 }catch(e){return response(400,{error:e.message})}
};
'''.replace('DEMO_DATA',data)
 adapter=(ROOT/'worker/merchandising.mjs').read_text().replace('export const','const').replace('export function','function')+'\n'+(ROOT/'worker/feast.mjs').read_text().replace('export const','const').replace('export function','function')+'\n'+adapter
 html=(ROOT/'static/index.html').read_text();css=(ROOT/'static/style.css').read_text().replace("url('/media/","url('./media/")
 app=(ROOT/'static/app.js').read_text().replace("return p.details.image;try", "return '.'+p.details.image;try")
 # Owner panel needs a backend and is outside the portable customer demo.
 html=html.replace('<button id="adminOpen" data-t="manage"></button>','<button id="adminOpen" data-t="manage" hidden></button>')
 html=html.replace('<link rel="stylesheet" href="/style.css">','<style>'+css+'</style>').replace('<script src="/app.js" defer></script>','')
 html=html.replace('poster="/media/','poster="./media/').replace('data-desktop="/media/','data-desktop="./media/').replace('data-mobile="/media/','data-mobile="./media/')
 html=html.replace('src="/motion.js"','src="./motion.js"')
 (out/'motion.js').write_text((ROOT/'static/motion.js').read_text())
 html=html.replace('href="/"','href="#"').replace('</body>','<script>'+adapter+'\n'+app.replace('</','<\\/')+'</script></body>')
 (out/'index.html').write_text(html)
 media=out/'media';media.mkdir(exist_ok=True)
 shutil.copytree(ROOT/'static/icons',out/'icons',dirs_exist_ok=True)
 html=(out/'index.html').read_text().replace('src="/icons/','src="./icons/').replace('href="/icons/','href="./icons/')
 (out/'index.html').write_text(html)
 for p in (ROOT/'static/media').iterdir():
  if p.is_file():shutil.copy2(p,media/p.name)
 (out/'README.txt').write_text('Шашлычный рай — демо для Ахалкалаки.\nРаспакуйте весь архив и откройте index.html в браузере. Сервер и установка не нужны.\nЧетыре языка, фотографии, каталог, корзина и расчёт порций работают локально.\nЗаказы не отправляются, Telegram не подключён, деньги не списываются. Не выполняйте переводы по банковским ссылкам во время демо.\nЦены сторонних ресторанов пересчитаны по НБГ на 14.11.2026: 100 RUB = 3.154 GEL и округлены вверх до целого лари.\nПорционные нормы технические; вес неизвестных позиций не используется для расчёта застолья.\nНазвания блюд переведены, подробные описания и аллергены ещё требуют завершения.\nФотографии сторонних ресторанов, коммерческая лицензия не получена.\n')
 archive=ROOT/'dist/Шашлычный-рай-демо-4-языка.zip'
 archive.parent.mkdir(exist_ok=True)
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for p in out.rglob('*'):
   if p.is_file():z.write(p,Path('Шашлычный-рай-демо')/p.relative_to(out))
 print(archive)
if __name__=='__main__':export()
