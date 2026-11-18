const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const html=fs.readFileSync('static/index.html','utf8'),elements=new Map();
for(const m of html.matchAll(/id="([^"]+)"/g))elements.set('#'+m[1],{value:'',dataset:{},classList:{add(){},remove(){}},setAttribute(k,v){this[k]=v},closest(){return {hidden:false}}});
const phoneLinks=[{},{}],phoneLabels=[{},{}],storage=new Map();
const ctx={crypto,URL,Intl,JSON,Map,console,setTimeout(){},localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},document:{documentElement:{},querySelector:s=>elements.get(s),querySelectorAll:s=>s==='[data-shop-phone]'?phoneLinks:s==='[data-shop-phone-number]'?phoneLabels:[]}};
vm.createContext(ctx);vm.runInContext(fs.readFileSync('static/app.js','utf8').replace('load().catch(error);',''),ctx);
const run=s=>vm.runInContext(s,ctx),el=id=>elements.get('#'+id);
const product=JSON.parse(fs.readFileSync('demo/catalog.json')).products[0];
run('shopSettings={phone:"+995591244075",phone_display:"+995 591 244 075"};products='+JSON.stringify([product])+';cart=[{id:products[0].id,quantity:2}];quote={lines:[{...products[0],quantity:2}],total:products[0].price*2};lang="ru";syncOrderChannels();');
for(const a of phoneLinks)assert.equal(a.href,'tel:+995591244075');for(const n of phoneLabels)assert.equal(n.textContent,'+995 591 244 075');
assert.ok(html.includes('data-shop-phone-number>+995 591 244 075'));
let u=new URL(el('whatsappOrder').href);assert.equal(u.hostname,'wa.me');assert.equal(u.pathname,'/995591244075');assert.ok(u.searchParams.get('text').includes(product.names.ru+' × 2'));assert.ok(u.searchParams.get('text').includes(run('money(quote.total)')));
el('customerName').value='Test & Name';el('customerPhone').value='+995000000000';el('customerAddress').value='Test #5 / A & B';
assert.ok(!u.searchParams.get('text').includes('Test #5'));
const before=run('JSON.stringify(cart)');el('whatsappOrder').onclick({preventDefault(){throw Error('Valid link blocked')}});u=new URL(el('whatsappOrder').href);assert.ok(u.searchParams.get('text').includes('Test #5 / A & B'));assert.ok(u.searchParams.get('text').includes('Test & Name'));assert.equal(run('JSON.stringify(cart)'),before);assert.ok(storage.has('rai.checkout.v1'));assert.equal(storage.has('rai.lastOrder'),false);
for(const lang of ['ka','hy','en']){run('lang='+JSON.stringify(lang)+';syncOrderChannels()');u=new URL(el('whatsappOrder').href);assert.ok(u.searchParams.get('text').includes(product.names[lang]));assert.ok(!u.searchParams.get('text').includes('undefined'))}
run('quote=null;syncOrderChannels()');let blocked=false;el('whatsappOrder').onclick({preventDefault(){blocked=true}});assert.equal(blocked,true);assert.equal(el('whatsappOrder')['aria-disabled'],'true');
run('cart=[];syncOrderChannels()');assert.equal(el('whatsappOrder').hidden,true);assert.equal(new URL(el('whatsappContact').href).pathname,'/995591244075');
console.log('Phone/WhatsApp: visible full number, tel link, server quote, four languages, encoded draft, explicit contact inclusion, no submission/cart clearing, pending quote and empty basket passed');
