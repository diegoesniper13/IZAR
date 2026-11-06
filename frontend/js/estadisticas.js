// estadisticas.js
// Pantalla de estadísticas:
//   - comprueba que hay sesión (si no, manda a login.html)
//   - pone el día del ciclo de hoy
//   - enseña los síntomas que es posible que tenga hoy (función 5F de ciclos.py)
// La caja de "Últimos periodos" sigue siendo de ejemplo hasta que exista su ruta en el backend.

// Cómo se enseña cada síntoma. Las claves son los nombres que guarda la base de datos
// (SINTOMAS_VALIDOS de ciclos.py); los valores, lo que ve la usuaria.
const SINTOMAS_VISIBLES = {
    colicos: { emoji: "〰️", texto: "Cólicos" },
    flujo:   { emoji: "💧", texto: "Flujo" },
    animo:   { emoji: "🙂", texto: "Ánimo" },
    sueno:   { emoji: "💤", texto: "Sueño" }
};

// Esperamos a que el HTML esté cargado antes de tocar nada
document.addEventListener("DOMContentLoaded", async () => {

    const numeroDiaCiclo = document.querySelector("#dia-ciclo");
    const listaSintomas = document.querySelector("#lista-sintomas");
    const explicacion = document.querySelector("#explicacion-sintomas");


    // ---------------------------------------------------------------
    // FUNCIÓN: escribe un texto gris dentro de la lista (cuando no hay pastillas que enseñar)
    // ---------------------------------------------------------------
    function mostrarTextoVacio(texto) {
        listaSintomas.innerHTML = "";               // borramos lo que hubiera
        const parrafo = document.createElement("span");
        parrafo.className = "texto-vacio";
        parrafo.textContent = texto;
        listaSintomas.appendChild(parrafo);
    }


    // ---------------------------------------------------------------
    // FUNCIÓN: pinta una "pastilla" por cada síntoma posible
    // ---------------------------------------------------------------
    // Recibe la lista que manda el servidor, por ejemplo ["colicos", "sueno"]
    function mostrarSintomas(sintomas) {
        listaSintomas.innerHTML = "";               // quitamos el "Cargando..."

        // forEach recorre la lista: una pastilla por síntoma
        sintomas.forEach((nombre) => {
            // Si llegara un nombre que no conocemos, lo enseñamos tal cual (sin emoji)
            const visible = SINTOMAS_VISIBLES[nombre] || { emoji: "•", texto: nombre };

            // Creamos <span class="pastilla pastilla-activa">〰️ Cólicos</span>
            const pastilla = document.createElement("span");
            pastilla.className = "pastilla pastilla-activa";
            pastilla.textContent = `${visible.emoji} ${visible.texto}`;
            listaSintomas.appendChild(pastilla);
        });
    }


    try {
        // Pedimos los datos a la misma ruta que usa la pantalla principal
        const respuesta = await fetch("/dashboard");

        // 401 = no hay sesión: a iniciar sesión
        if (respuesta.status === 401) {
            window.location.href = "login.html";
            return;
        }

        const datos = await respuesta.json();

        // CUENTA NUEVA: todavía no hay ningún periodo registrado
        if (datos.estado === "nuevo") {
            mostrarTextoVacio("Registra tu primer periodo para empezar");
            explicacion.textContent = "";
            return;
        }

        // DÍA DEL CICLO
        numeroDiaCiclo.textContent = datos.dia_ciclo;

        // SÍNTOMAS POSIBLES
        const sintomas = datos.sintomas_posibles;
        if (sintomas.length > 0) {
            mostrarSintomas(sintomas);
            explicacion.textContent = "Según los síntomas que registraste estos días en tus ciclos anteriores.";
        } else {
            // Lista vacía: o no hay datos suficientes todavía, o no suele tener nada estos días.
            // El servidor no distingue los dos casos, así que lo explicamos con un texto que vale para ambos.
            mostrarTextoVacio("Nada destacable para hoy");
            explicacion.textContent = "Las predicciones aparecen cuando tienes al menos un ciclo completo con síntomas registrados.";
        }

    } catch (error) {
        // Servidor apagado o fallo de conexión
        console.error("Error de conexión:", error);
        mostrarTextoVacio("No se pudo conectar con el servidor");
    }
});
