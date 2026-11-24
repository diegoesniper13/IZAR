// pwa.js
// Registra el service worker (sw.js). Se carga en todas las páginas.
//
// Registrar = decirle al navegador "esta web tiene un service worker, ponlo en marcha".
// Es uno de los requisitos para que IZAR se pueda instalar como app (y convertir en APK).

// No todos los navegadores lo tienen (los muy antiguos no): si no existe, no hacemos nada
if ("serviceWorker" in navigator) {
    // Esperamos a que la página termine de cargar para no ralentizarla
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/sw.js").catch((error) => {
            // Si falla, la web sigue funcionando igual; solo no será instalable
            console.error("No se pudo registrar el service worker:", error);
        });
    });
}
