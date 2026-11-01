// registro.js - envía los datos del formulario de crear cuenta a /registro

// Buscamos los elementos de la página por su id
const boton = document.getElementById("crear");
const mensaje = document.getElementById("mensaje");

// "async" permite usar "await" dentro de la función (esperar la respuesta del servidor)
boton.addEventListener("click", async function () {
    // Leemos lo que ha escrito la usuaria en cada casilla
    const usuario = document.getElementById("usuario").value;
    const nombre = document.getElementById("nombre").value;
    const contrasena = document.getElementById("contrasena").value;

    // Comprobaciones rápidas antes de molestar al servidor.
    // El servidor las repite igualmente: nunca se confía solo en el frontend.
    if (usuario === "" || nombre === "" || contrasena === "") {
        mensaje.textContent = "Rellena todos los campos";
        return;                                        // sale de la función: no envía nada
    }
    if (contrasena.length < 8) {
        mensaje.textContent = "La contraseña debe tener al menos 8 caracteres";
        return;
    }

    // Enviamos los datos a la ruta /registro de Flask y esperamos su respuesta
    const respuesta = await fetch("/registro", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ usuario: usuario, nombre: nombre, contrasena: contrasena })
    });
    const datos = await respuesta.json();              // el JSON que devolvió Flask

    // respuesta.ok es true si el número de estado es 2xx (el 201 de "creado" lo es)
    if (respuesta.ok) {
        window.location.href = "login.html";           // cuenta creada: vamos a iniciar sesión
    } else {
        mensaje.textContent = datos.error;             // enseñamos el error que mandó Flask
    }
});