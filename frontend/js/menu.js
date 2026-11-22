// menu.js
// Abre y cierra el menú lateral (el botón de las tres rayitas ☰ de la cabecera).
// Se carga en TODAS las pantallas con menú, así el código está en un solo sitio:
// si mañana cambias cómo se abre el menú, lo cambias aquí y vale para todas.
//
// Cómo funciona: el menú y el fondo oscuro ya están en el HTML, pero escondidos.
// Abrir = ponerles la clase "abierto" (el CSS los hace aparecer con una animación).
// Cerrar = quitársela.

document.addEventListener("DOMContentLoaded", () => {

    const botonAbrir = document.querySelector("#abrir-menu");    // las tres rayitas ☰
    const botonCerrar = document.querySelector("#cerrar-menu");  // la ✕ de dentro del menú
    const menu = document.querySelector("#menu-lateral");
    const fondo = document.querySelector("#fondo-menu");         // capa oscura detrás del menú

    // Si una página no tiene menú (login, registro...), no hacemos nada
    if (!botonAbrir || !menu || !fondo) {
        return;
    }

    // ---------------------------------------------------------------
    // FUNCIÓN: abre el menú
    // ---------------------------------------------------------------
    function abrirMenu() {
        menu.classList.add("abierto");
        fondo.classList.add("abierto");
        // Mientras el menú está abierto, la página de detrás no se mueve al hacer scroll
        document.body.classList.add("sin-scroll");
        // aria-expanded avisa a los lectores de pantalla de que el menú está abierto
        botonAbrir.setAttribute("aria-expanded", "true");
        // Ponemos el foco en la ✕: así con el teclado (Tab) se empieza a navegar por el menú
        botonCerrar.focus();
    }

    // ---------------------------------------------------------------
    // FUNCIÓN: cierra el menú
    // ---------------------------------------------------------------
    function cerrarMenu() {
        menu.classList.remove("abierto");
        fondo.classList.remove("abierto");
        document.body.classList.remove("sin-scroll");
        botonAbrir.setAttribute("aria-expanded", "false");
        botonAbrir.focus();     // el foco vuelve al botón ☰, que es de donde venía
    }

    // Tres formas de cerrar: la ✕, tocar fuera del menú (el fondo oscuro) o la tecla Escape
    botonAbrir.addEventListener("click", abrirMenu);
    botonCerrar.addEventListener("click", cerrarMenu);
    fondo.addEventListener("click", cerrarMenu);

    document.addEventListener("keydown", (evento) => {
        // Solo cerramos si de verdad estaba abierto
        if (evento.key === "Escape" && menu.classList.contains("abierto")) {
            cerrarMenu();
        }
    });
});
