// volver.js
// Botón "Volver" de las páginas de términos y de privacidad.
//
// El problema: el enlace llevaba siempre a registro.html, aunque vinieras de Ajustes
// con la sesión iniciada. Ahora "Volver" te devuelve a la página DE LA QUE VINISTE
// (como el botón de atrás del navegador).
//
// Si no hay página a la que volver (por ejemplo, se abrió en una pestaña nueva
// desde el registro, o entraste escribiendo la dirección), el enlace hace lo de
// siempre: ir a su href (registro.html).

document.addEventListener("DOMContentLoaded", () => {

    const enlaceVolver = document.querySelector(".volver");
    if (!enlaceVolver) {
        return;
    }

    enlaceVolver.addEventListener("click", (evento) => {
        // document.referrer = la dirección de la página de la que venimos ("" si no hay)
        // location.origin   = el principio de NUESTRA web (por ejemplo https://izar.pythonanywhere.com)
        // Solo volvemos atrás si venimos de una página de IZAR, no de otra web.
        const vieneDeIzar = document.referrer.startsWith(location.origin);

        // history.length > 1: esta pestaña tiene al menos una página antes que esta
        const hayPaginaAnterior = window.history.length > 1;

        if (vieneDeIzar && hayPaginaAnterior) {
            evento.preventDefault();    // cancelamos el ir a registro.html...
            window.history.back();      // ...y volvemos a la página anterior
        }
        // Si no, no hacemos nada y el enlace funciona normal (va a registro.html)
    });
});
