// ajustes.js
// Hace funcionar la página de ajustes. Usa estas rutas del backend:
//   - GET  /dashboard          -> ya existe. Para mostrar el nombre de usuario,
//                                 añade "usuario": usuario a sus dos respuestas en app.py.
//   - POST /logout             -> ya existe. Cierra la sesión.
//   - POST /cuenta/contrasena  -> NUEVA. Recibe {"actual": "...", "nueva": "..."}.
//                                 Responde 200 si se cambió, o un error (400/401) con {"error": "..."}.
//   - POST /cuenta/borrar      -> NUEVA. Borra la cuenta y todos sus datos. Responde 200.

document.addEventListener("DOMContentLoaded", () => {

    // --- Partes del HTML ---
    const nombreUsuario = document.querySelector("#nombre-usuario");
    // Cambiar contraseña
    const inputActual = document.querySelector("#contrasena-actual");
    const inputNueva = document.querySelector("#contrasena-nueva");
    const botonContrasena = document.querySelector("#guardar-contrasena");
    const mensajeContrasena = document.querySelector("#mensaje-contrasena");
    // Sesión y cuenta
    const botonCerrar = document.querySelector("#cerrar-sesion");
    const botonBorrar = document.querySelector("#borrar-cuenta");
    const mensajeCuenta = document.querySelector("#mensaje-cuenta");


    // ---------------------------------------------------------------
    // CARGAR EL NOMBRE DE USUARIO
    // ---------------------------------------------------------------
    // Reutilizamos /dashboard. Si no hay sesión, nos manda a login.
    async function cargarUsuario() {
        try {
            const respuesta = await fetch("/dashboard");
            if (respuesta.status === 401) {
                window.location.href = "login.html";
                return;
            }
            const datos = await respuesta.json();
            // Mostramos el usuario solo si el backend lo envía (hay que añadirlo a /dashboard).
            // Si todavía no lo envía, se queda la raya "—" y no pasa nada.
            if (datos.usuario) {
                nombreUsuario.textContent = datos.usuario;
            }
        } catch (error) {
            console.error("Error de conexión:", error);
        }
    }


    // ---------------------------------------------------------------
    // CERRAR SESIÓN
    // ---------------------------------------------------------------
    botonCerrar.addEventListener("click", async () => {
        botonCerrar.disabled = true;
        try {
            // Avisamos al servidor para que borre la sesión (POST, no GET: cambia estado)
            await fetch("/logout", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: "{}"                               // cuerpo JSON vacío (la ruta no necesita datos)
            });
        } catch (error) {
            console.error("Error de conexión:", error);
        }
        // Pase lo que pase, llevamos a la pantalla de inicio de sesión
        window.location.href = "login.html";
    });


    // ---------------------------------------------------------------
    // CAMBIAR CONTRASEÑA
    // ---------------------------------------------------------------
    botonContrasena.addEventListener("click", async () => {
        mensajeContrasena.textContent = "";
        mensajeContrasena.classList.remove("error");

        const actual = inputActual.value;
        const nueva = inputNueva.value;

        // Comprobaciones rápidas antes de molestar al servidor (él las repite igualmente)
        if (actual === "" || nueva === "") {
            mensajeContrasena.textContent = "Rellena las dos contraseñas";
            mensajeContrasena.classList.add("error");
            return;
        }
        if (nueva.length < 8) {
            mensajeContrasena.textContent = "La nueva debe tener al menos 8 caracteres";
            mensajeContrasena.classList.add("error");
            return;
        }

        botonContrasena.disabled = true;
        try {
            const respuesta = await fetch("/cuenta/contrasena", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ actual: actual, nueva: nueva })
            });

            if (respuesta.status === 401) {
                window.location.href = "login.html";
                return;
            }

            const datos = await respuesta.json();
            if (respuesta.ok) {
                mensajeContrasena.textContent = "Contraseña cambiada";
                inputActual.value = "";                  // limpiamos los campos
                inputNueva.value = "";
            } else {
                mensajeContrasena.textContent = datos.error;   // por ejemplo "Contraseña actual incorrecta"
                mensajeContrasena.classList.add("error");
            }
        } catch (error) {
            console.error("Error de conexión:", error);
            mensajeContrasena.textContent = "No se pudo conectar con el servidor";
            mensajeContrasena.classList.add("error");
        }
        botonContrasena.disabled = false;
    });


    // ---------------------------------------------------------------
    // ELIMINAR CUENTA
    // ---------------------------------------------------------------
    botonBorrar.addEventListener("click", async () => {
        mensajeCuenta.textContent = "";
        mensajeCuenta.classList.remove("error");

        // Doble aviso: borrar la cuenta no se puede deshacer
        if (!confirm("¿Seguro que quieres eliminar tu cuenta? Se borrarán todos tus datos y no se puede deshacer.")) {
            return;
        }

        botonBorrar.disabled = true;
        try {
            const respuesta = await fetch("/cuenta/borrar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: "{}"
            });

            if (respuesta.status === 401) {
                window.location.href = "login.html";
                return;
            }

            if (respuesta.ok) {
                // Cuenta borrada: a la pantalla de inicio
                window.location.href = "index.html";
            } else {
                const datos = await respuesta.json();
                mensajeCuenta.textContent = datos.error;
                mensajeCuenta.classList.add("error");
                botonBorrar.disabled = false;
            }
        } catch (error) {
            console.error("Error de conexión:", error);
            mensajeCuenta.textContent = "No se pudo conectar con el servidor";
            mensajeCuenta.classList.add("error");
            botonBorrar.disabled = false;
        }
    });


    // Al abrir la página, cargamos el nombre de usuario
    cargarUsuario();
});
