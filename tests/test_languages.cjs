const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert'),crypto=require('node:crypto');
const html=fs.readFileSync('static/index.html','utf8'),elements=new Map();
for(const m of html.matchAll(/id="([^"]+)"/g))elements.set('#'+m[1],{value:'',dataset:{},classList:{add(){},remove(){}},closest(){return {hidden:false}},elements:{}});
const translated=[...html.matchAll(/data-t="([^"]+)"/g)].map(m=>({dataset:{t:m[1]}}));
const ctx={console,crypto,URL,Intl,JSON,Map,setTimeout:()=>{},localStorage:{getItem:()=>null,setItem(){}},document:{documentElement:{},querySelector:s=>elements.get(s),querySelectorAll:s=>s==='[data-t]'?translated:[]}};
vm.createContext(ctx);let code=fs.readFileSync('static/app.js','utf8').replace('load().catch(error);','');
code+='\nproducts='+JSON.stringify(JSON.parse(fs.readFileSync('demo/catalog.json')).products)+';';
code+=`for(const l of Object.keys(demoWords))Object.assign(words[l],demoWords[l]);for(const l of ['ru','ka','hy','en']){lang=l;render();if(!$('#products').innerHTML.includes('data-detail'))throw Error(l+' catalogue missing');for(const e of document.querySelectorAll('[data-t]'))if(!words[l][e.dataset.t])throw Error(l+' missing '+e.dataset.t);for(const p of products)if(!p.names[l])throw Error('missing product translation');}console.log('Four languages render all catalogue cards and UI labels');`;
try{vm.runInContext(code,ctx)}catch(e){console.error(e.name+': '+e.message);process.exitCode=1}
