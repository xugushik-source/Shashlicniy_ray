const CACHE='rai-offline-v1';
const SAFE=['/offline.html','/offline.js','/style.css','/icons/icon-192.png'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SAFE)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('rai-offline-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{const r=event.request,u=new URL(r.url);if(r.method!=='GET'||u.origin!==self.location.origin||u.pathname.startsWith('/api/'))return;if(r.mode==='navigate'){event.respondWith(fetch(r).catch(()=>caches.match('/offline.html')));return}if(SAFE.includes(u.pathname))event.respondWith(fetch(r).catch(()=>caches.match(u.pathname)));});
