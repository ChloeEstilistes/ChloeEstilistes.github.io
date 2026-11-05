/* Agenda Chloe Estilistes · service worker (05/11/2026)
   Guarda la "carcasa" de la agenda (pantalla de entrada, iconos, logo, letra) para que
   la app abra aunque no haya internet. Los datos de las citas los guarda la propia agenda. */
var VERSION = 'agenda-shell-v1';
var SHELL = [
  '/agenda/',
  '/agenda/manifest.json',
  '/agenda/icon-192.png',
  '/agenda/icon-512.png',
  '/agenda/apple-touch-icon.png',
  '/img/logo-chloe-estilistes.webp',
  '/fonts/josefin-sans.woff2'
];

self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(VERSION).then(function (c) { return c.addAll(SHELL); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k.indexOf('agenda-shell-') === 0 && k !== VERSION; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return; /* las llamadas a Google no se tocan */

  /* La pagina de la agenda: primero internet (siempre la version mas nueva); sin internet, la guardada */
  if (req.mode === 'navigate' && url.pathname.indexOf('/agenda') === 0) {
    e.respondWith(fetch(req).then(function (res) {
      if (res && res.ok) { var copia = res.clone(); caches.open(VERSION).then(function (c) { c.put('/agenda/', copia); }); }
      return res;
    }).catch(function () {
      return caches.match('/agenda/');
    }));
    return;
  }

  /* Iconos, logo y letra: lo guardado al momento y se refresca por detras */
  if (SHELL.indexOf(url.pathname) > -1) {
    e.respondWith(caches.match(req).then(function (hit) {
      var red = fetch(req).then(function (res) {
        if (res && res.ok) { var copia = res.clone(); caches.open(VERSION).then(function (c) { c.put(req, copia); }); }
        return res;
      }).catch(function () { return hit; });
      return hit || red;
    }));
  }
});
