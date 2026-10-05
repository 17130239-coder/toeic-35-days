const CACHE_NAME = '35days-toeic-v3';
const PRECACHE_ASSETS = [
  './',
  './index.html',
  './wayground.html',
  './vocab_data.js',
  './wayground_data.js',
  './manifest.json',
  './favicon.svg',
  './favicon-wayground.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Cache-first for local media, images, audio and web fonts
  if (url.pathname.includes('/quiz_media/') || url.pathname.match(/\.(png|jpg|jpeg|svg|gif|webp|woff2|woff|ttf|mp3|wav|ogg)$/i)) {
    event.respondWith(
      caches.match(request).then(cachedResponse => {
        if (cachedResponse) return cachedResponse;
        return fetch(request).then(networkResponse => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(request, responseToCache));
          }
          return networkResponse;
        }).catch(() => cachedResponse);
      })
    );
    return;
  }

  // Network-first with cache fallback for documents and data scripts
  event.respondWith(
    fetch(request).then(networkResponse => {
      if (networkResponse && networkResponse.status === 200) {
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, responseToCache));
      }
      return networkResponse;
    }).catch(() => {
      return caches.match(request).then(cachedResponse => {
        if (cachedResponse) return cachedResponse;
        if (request.headers.get('accept') && request.headers.get('accept').includes('text/html')) {
          return caches.match('./index.html');
        }
      });
    })
  );
});
