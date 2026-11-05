/* Sweep — service worker: the notifications on the phone only (web push, brief 02 part 10). No fetch handler and no cache:
   the app loads exactly as without it. Registered only when the trader turns notifications on (src/notify.js). */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('push', (e) => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (x) { d = { body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || 'Sweep', {
    body: d.body || '', tag: d.tag || 'sweep', icon: '/icons/icon-192.png', badge: '/icons/icon-192.png', data: { url: d.url || '/', track: d.track || '' },
  }));
});
self.addEventListener('notificationclick', (e) => {
  e.notification.close();
  const raw = (e.notification.data && e.notification.data.url) || '/';
  const url = new URL(raw.charAt(0) === '#' ? '/' + raw : raw, self.location.origin).href;   // in-app links only (#dashboard)
  // (5 Nov.) an automatic message: tell Sweep it was opened (then its email is not sent); our own address only. Alongside the
  // window, never before it (an iPhone opens a window only within the tap)
  const tr = e.notification.data && e.notification.data.track;
  const seen = /^\/api\/p\/o\/[a-f0-9]{24}$/.test(tr || '') ? fetch(tr, { method: 'POST', credentials: 'omit', keepalive: true }).catch(() => {}) : Promise.resolve();
  e.waitUntil(Promise.all([seen, self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
    for (const c of list) {
      if (new URL(c.url).origin === self.location.origin && 'focus' in c) return c.focus().then((w) => (w && 'navigate' in w ? w.navigate(url) : w));
    }
    return self.clients.openWindow(url);
  })]));
});
