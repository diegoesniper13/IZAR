// Esperamos a que todo el HTML de la página esté completamente cargado antes de ejecutar nada
document.addEventListener("DOMContentLoaded", async () => {
    
    // Seleccionamos los textos del HTML que vamos a querer cambiar
    // Usamos querySelector para buscar las etiquetas igual que en CSS
    const tituloCirculo = document.querySelector(".texto-circulo h4");
    const subtituloCirculo = document.querySelector(".texto-circulo p");

    try {
        // 1. PEDIR DATOS AL SERVIDOR (Backend)
        // fetch llama a la ruta que creamos en app.py. Al no poner http://..., 
        // asume que está en el mismo servidor.
        const respuesta = await fetch("/dashboard", {
            method: "GET",
            // Esto es vital: le dice al navegador que envíe la "cookie" de sesión 
            // para que Flask sepa quiénes somos.
            headers: {
                "Content-Type": "application/json"
            }
        });

        // 2. COMPROBAR SEGURIDAD
        // Si Flask nos devuelve un 401 (No autorizado), significa que no hay sesión.
        // Lo redirigimos automáticamente a la pantalla de login.
        if (respuesta.status === 401) {
            window.location.href = "login.html";
            return; // Detenemos la ejecución aquí
        }

        // 3. LEER LA RESPUESTA
        // Convertimos el JSON que nos envió Python en un diccionario de JavaScript (un objeto)
        const datos = await respuesta.json();

        // 4. ACTUALIZAR LA PANTALLA
        if (datos.estado === "ok") {
            // Cambiamos el texto del h4 inyectando el número que calculó ciclos.py
            tituloCirculo.textContent = `Día ${datos.dia_ciclo} de tu ciclo`;

            // Si hay suficientes datos para la predicción, mostramos los días restantes
            if (datos.dias_restantes !== null) {
                subtituloCirculo.textContent = `Próximo periodo en ${datos.dias_restantes} días`;
            } else {
                // Si solo hay un periodo registrado, no hay media posible aún
                subtituloCirculo.textContent = "Faltan datos para predecir";
            }
        } 
        else if (datos.estado === "nuevo") {
            // Si el usuario acaba de crear la cuenta y no tiene registros
            tituloCirculo.textContent = "¡Bienvenida!";
            subtituloCirculo.textContent = datos.mensaje; // Dice: "Registra tu primer periodo"
        }

    } catch (error) {
        // Si el servidor está apagado o falla la conexión, mostramos un error amigable
        console.error("Error de conexión:", error);
        tituloCirculo.textContent = "Error al cargar";
        subtituloCirculo.textContent = "Comprueba tu conexión";
    }
});