const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const html=fs.readFileSync('static/index.html','utf8'),code=fs.readFileSync('static/app.js','utf8').replace('load().catch(error);','');
function page(storage,initial={}){
 const elements=new Map(),events=new Map();
 for(const m of html.matchAll(/id="([^"]+)"/g))elements.set('#'+m[1],{value:initial[m[1]]||'',dataset:{},classList:{add(){},remove(){}},addEventListener(n,f){this[n]=f},close(){},showModal(){},closest(){return {hidden:false}}});
 const ctx={crypto,URL,Intl,JSON,Map,console,setTimeout(){},matchMedia:()=>({matches:true}),localStorage:storage,window:{addEventListener:(n,f)=>events.set(n,f)},document:{documentElement:{},querySelector:s=>elements.get(s),querySelectorAll:()=>[]},fetch:async()=>({ok:true,json:async()=>({recommendations:[]})})};
 vm.createContext(ctx);vm.runInContext(code,ctx);
 return {ctx,events,el:id=>elements.get('#'+id),run:s=>vm.runInContext(s,ctx)};
}
(async()=>{
const data=new Map([['rai.lang','ru'],['rai.lastOrder','KEEP']]),storage={getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};
for(const [id,token]of [['customerName','name'],['customerPhone','tel'],['customerAddress','street-address']])assert.match(html,new RegExp('id="'+id+'"[^>]*autocomplete="section-delivery shipping '+token+'"'));
let p=page(storage);p.el('customerName').value='Test recipient';p.el('customerPhone').value='+995000000000';p.el('customerAddress').value='TEST STREET';p.el('checkout').input();
const saved=data.get('rai.checkout.v1');assert.ok(saved.includes('TEST STREET'));assert.ok(!saved.includes('KEEP'));
p=page(storage);assert.equal(p.el('customerName').value,'Test recipient');assert.equal(p.el('customerAddress').value,'TEST STREET');
p.run('cart=[{id:"test",quantity:1}]');p.el('clearCart').onclick();assert.equal(data.get('rai.checkout.v1'),saved);assert.equal(p.el('customerPhone').value,'+995000000000');
const submit={disabled:false};p.ctx.FormData=class{constructor(){return [['customer_name',p.el('customerName').value],['phone',p.el('customerPhone').value],['address',p.el('customerAddress').value]][Symbol.iterator]()}};p.ctx.fetch=async(path,opts)=>{if(path==='/api/orders'){assert.equal(JSON.parse(opts.body).customer_name,'Test recipient');return {ok:true,json:async()=>({id:'local-test',token:'test-token'})}}return {ok:true,json:async()=>({recommendations:[]})}};p.run('cart=[{id:"test",quantity:1}];quote={total:100}');await p.el('checkout').onsubmit({preventDefault(){},target:{querySelector:s=>{assert.equal(s,'[type="submit"]');return submit}}});assert.equal(data.get('rai.checkout.v1'),saved);assert.equal(submit.disabled,false);assert.equal(p.run('cart.length'),0);data.set('rai.lastOrder','KEEP');
const autofilled=page(storage,{customerName:'Browser autofilled name'});assert.equal(autofilled.el('customerName').value,'Browser autofilled name');
p.el('forgetContact').onclick();assert.equal(data.has('rai.checkout.v1'),false);assert.equal(p.el('customerAddress').value,'');assert.equal(data.get('rai.lastOrder'),'KEEP');p.run('rememberCheckoutProfile()');assert.equal(data.has('rai.checkout.v1'),false);
data.set('rai.checkout.v1','broken JSON');assert.equal(page(storage).el('customerName').value,'');
data.set('rai.checkout.v1',JSON.stringify({version:1,customer_name:'Test',addresses:{tbilisi:'OTHER CITY'}}));assert.equal(page(storage).el('customerAddress').value,'');
const blocked=page({getItem(){throw Error('blocked')},setItem(){throw Error('blocked')},removeItem(){throw Error('blocked')}});blocked.el('customerPhone').value='+995000000000';blocked.el('checkout').change();assert.match(blocked.el('profileStatus').textContent,/не разрешает|не позволяет/);assert.equal(blocked.el('customerPhone').value,'+995000000000');
console.log('Checkout: semantic autofill, reload, preserved autofill, cart clearing, explicit forget, corrupt/blocked storage and city isolation passed');

})().catch(e=>{console.error(e);process.exitCode=1});
