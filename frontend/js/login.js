// login.js - envía usuario y contraseña a /login y, si son correctos, abre la pantalla principal

// Buscamos los elementos de la página por su id
const boton = document.getElementById("entrar");
const mensaje = document.getElementById("mensaje");

boton.addEventListener("click", async function () {
    // Leemos lo que ha escrito la usuaria
    const usuario = document.getElementById("usuario").value;
    const contrasena = document.getElementById("contrasena").value;

    // Comprobación rápida antes de molestar al servidor
    if (usuario === "" || contrasena === "") {
        mensaje.textContent = "Rellena usuario y contraseña";
        return;                                        // sale de la función: no envía nada
    }

    // Enviamos los datos a la ruta /login de Flask y esperamos su respuesta
    const respuesta = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario: usuario, contrasena: contrasena })
    });
    const datos = await respuesta.json();              // el JSON que devolvió Flask

    // respuesta.ok es true si el número de estado es 2xx (el 200 de login correcto lo es)
    if (respuesta.ok) {
        window.location.href = "principal.html";       // login correcto: vamos a la pantalla principal
    } else {
        mensaje.textContent = datos.error;             // 401: "Usuario o contraseña incorrectos"
    }
});