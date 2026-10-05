/* SpeakMasri service worker.
 * Scope: baseline installability + light offline support.
 *
 * IMPORTANT: this app deploys to production frequently. The HTML document
 * is ALWAYS network-first so users get fresh code/bugfixes; cache is only
 * a fallback for offline use. Bump CACHE_VERSION when the precached shell
 * list changes so old caches get cleaned up on activate.
 */

const CACHE_VERSION = "speakmasri-v2";

const APP_SHELL = [
  "index.html",
  "manifest.json",
  "logo-512.png",
  "logo-192.png",
  "favicon-32.png",
  "favicon-16.png",
  "apple-touch-icon.png"
];

const IMAGE_EXTENSIONS = [".webp", ".png", ".jpg", ".jpeg", ".gif", ".svg"];

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(APP_SHELL))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_VERSION)
          .map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

function isAudioOrImage(pathname) {
  if (pathname.startsWith("/audio/") || pathname.startsWith("/audio_female/")) return true;
  if (pathname.startsWith("/mascot/")) return true;
  return IMAGE_EXTENSIONS.some((ext) => pathname.endsWith(ext));
}

/* Network-first, falling back to cache on failure. Used for the HTML
 * document and the manifest so deploys always reach users who are online. */
async function networkFirst(request) {
  const cache = await caches.open(CACHE_VERSION);
  try {
    // "no-store" is deliberate: a plain fetch() here can still be satisfied by the
    // browser's own HTTP disk cache (a layer below the service worker), which would
    // silently defeat "network-first" and serve a stale deploy to users who are
    // genuinely online. Confirmed this happens for real. Also confirmed: passing
    // {cache:"no-store"} as a second argument alongside the original navigation-mode
    // Request object does NOT reliably override its cache mode (Chrome appears to
    // keep the original Request's own cache mode for navigation requests regardless
    // of the init override) - fetching the URL string directly, instead of the
    // Request object, is what actually forces a real network hit.
    const response = await fetch(request.url, {cache: "no-store"});
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw err;
  }
}

/* Cache-first, falling back to network and storing the result. Used for
 * audio/image assets so a user's device organically builds an offline
 * cache of lessons they've actually done. */
async function cacheFirst(request) {
  const cache = await caches.open(CACHE_VERSION);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok) cache.put(request, response.clone());
  return response;
}

self.addEventListener("fetch", (event) => {
  const request = event.request;

  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate" || url.pathname.endsWith("/manifest.json")) {
    event.respondWith(networkFirst(request));
    return;
  }

  if (isAudioOrImage(url.pathname)) {
    event.respondWith(cacheFirst(request));
    return;
  }

  event.respondWith(networkFirst(request));
});
