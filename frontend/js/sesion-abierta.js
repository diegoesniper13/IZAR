// sesion-abierta.js
// Se carga en la portada (index.html) y en el login (login.html).
//
// Si la usuaria YA tiene la sesión iniciada (la cookie de sesión sigue siendo válida),
// no tiene sentido enseñarle "Iniciar sesión" otra vez: la mandamos directa a la app.
// Así, al abrir la web (o la app del móvil), solo hay que iniciar sesión una vez.

async function comprobarSesion() {
    try {
        // /dashboard responde 200 si hay sesión y 401 si no la hay.
        // No usamos sus datos: solo nos interesa saber si hay sesión.
        const respuesta = await fetch("/dashboard");

        if (respuesta.ok) {
            // location.replace (y no location.href) para que el botón "atrás"
            // no vuelva a esta página, que te volvería a mandar a la app sin parar
            window.location.replace("principal.html");
        }
        // Si es 401 no hacemos nada: se queda la portada o el login, como siempre
    } catch (error) {
        // Sin conexión: tampoco hacemos nada, la página se ve normal
        console.error("No se pudo comprobar la sesión:", error);
    }
}

comprobarSesion();
