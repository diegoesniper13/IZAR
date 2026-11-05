// estadisticas.js
// Pantalla de estadísticas. Por ahora solo:
//   - comprueba que hay sesión (si no, manda a login.html)
//   - pone el día del ciclo real, que ya da la ruta /dashboard
// Los últimos periodos y los posibles síntomas son de ejemplo en el HTML:
// se conectarán cuando estén sus rutas en el backend.

// Esperamos a que el HTML esté cargado antes de tocar nada
document.addEventListener("DOMContentLoaded", async () => {

    const numeroDiaCiclo = document.querySelector("#dia-ciclo");

    try {
        // Reutilizamos la misma ruta que la pantalla principal
        const respuesta = await fetch("/dashboard");

        // 401 = no hay sesión: a iniciar sesión
        if (respuesta.status === 401) {
            window.location.href = "login.html";
            return;
        }

        const datos = await respuesta.json();

        // Si tiene periodos, ponemos el número; si es una cuenta nueva, dejamos la raya "–"
        if (datos.estado === "ok") {
            numeroDiaCiclo.textContent = datos.dia_ciclo;
        }

    } catch (error) {
        // Servidor apagado o fallo de conexión: dejamos la raya y lo apuntamos en la consola
        console.error("Error de conexión:", error);
    }
});
