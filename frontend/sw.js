// sw.js — el "service worker" de IZAR
//
// Un service worker es un JavaScript que el navegador deja funcionando aparte de la página,
// entre la app y el servidor. Es lo que hace falta para que el móvil trate la web como una
// app instalable (y para poder convertirla en APK).
//
// Está en la RAÍZ del frontend (no en js/) a propósito: un service worker solo controla
// las direcciones que están "por debajo" de donde vive. En /sw.js controla toda la web.
//
// Qué hace este, y qué NO hace:
//   - Guarda una página "Sin conexión" para enseñarla si abres la app sin internet.
//   - NO guarda tus datos ni las respuestas de la API (/dashboard, /periodo...):
//     esos siempre se piden al servidor, para que nunca veas datos viejos.

// Si algún día cambias offline.html o lo que se guarda, sube este número:
// así el móvil sabe que tiene que tirar lo antiguo y guardar lo nuevo.
const VERSION = "izar-v1";

// Lo que se guarda en el móvil: solo lo necesario para la página sin conexión
const ARCHIVOS_OFFLINE = [
    "/offline.html",
    "/css/styles.css",
    "/img/iconos/icono-192.png"
];


// 1. INSTALAR: la primera vez que se registra, guarda los archivos de la lista
self.addEventListener("install", (evento) => {
    evento.waitUntil(
        caches.open(VERSION).then((cache) => cache.addAll(ARCHIVOS_OFFLINE))
    );
    self.skipWaiting();     // que empiece a funcionar ya, sin esperar a cerrar la app
});


// 2. ACTIVAR: borra lo guardado por versiones anteriores (si cambiaste VERSION)
self.addEventListener("activate", (evento) => {
    evento.waitUntil(
        caches.keys().then((nombres) =>
            Promise.all(
                nombres
                    .filter((nombre) => nombre !== VERSION)    // todas menos la actual...
                    .map((nombre) => caches.delete(nombre))    // ...se borran
            )
        )
    );
    self.clients.claim();   // que controle también las pestañas que ya estaban abiertas
});


// 3. PETICIONES: siempre se intenta primero internet. Solo si no hay conexión:
//    - al abrir una página (navegación) -> enseñamos offline.html
//    - al pedir uno de los archivos guardados (el CSS y el icono que usa offline.html)
//      -> damos la copia guardada
//    Todo lo demás (la API, el resto de imágenes...) pasa tal cual, sin tocarlo.
self.addEventListener("fetch", (evento) => {
    const ruta = new URL(evento.request.url).pathname;     // por ejemplo "/css/styles.css"

    if (evento.request.mode === "navigate") {
        evento.respondWith(
            fetch(evento.request).catch(() => caches.match("/offline.html"))
        );
    } else if (ARCHIVOS_OFFLINE.includes(ruta)) {
        evento.respondWith(
            fetch(evento.request).catch(() => caches.match(ruta))
        );
    }
    // Si no es ninguno de los dos casos no llamamos a respondWith:
    // el navegador hace la petición normal, como si no hubiera service worker
});
