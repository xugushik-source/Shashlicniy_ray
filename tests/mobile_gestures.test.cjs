const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const code=fs.readFileSync('static/app.js','utf8').split('// Stop document rubber-banding sideways; preserve vertical scroll and local gestures.')[1].split('// Sticky category navigation')[0],events=new Map();vm.runInNewContext(code,{document:{addEventListener:(n,f,o)=>events.set(n,{f,o})}});
function touch(x,y,count=1){return Array.from({length:count},(_,identifier)=>({identifier,clientX:x,clientY:y}))}
function start(local=false){events.get('touchstart').f({touches:touch(100,100),target:{closest:()=>local}})}
function move(x,y,count=1,cancelable=true){let blocked=false;events.get('touchmove').f({touches:touch(x,y,count),cancelable,preventDefault(){blocked=true}});return blocked}
assert.equal(events.get('touchmove').o.passive,false);
start();assert.equal(move(140,103),true);assert.equal(move(50,103),true);
start();assert.equal(move(103,145),false);assert.equal(move(155,145),false);
start();assert.equal(move(105,103),false);
start(true);assert.equal(move(150,100),false);
start();assert.equal(move(140,100,2),false);assert.equal(move(150,100),false);
start();assert.equal(move(140,100,1,false),false);
start();events.get('touchcancel').f();assert.equal(move(140,100),false);
start();events.get('touchend').f();assert.equal(move(140,100),false);
console.log('Mobile gestures: horizontal page drag blocked; vertical scroll, local gestures, pinch and cancellation preserved');
