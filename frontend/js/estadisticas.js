// estadisticas.js
// Pantalla de estadísticas:
//   - comprueba que hay sesión (si no, manda a login.html)
//   - pone el día del ciclo de hoy
//   - enseña los síntomas que es posible que tenga hoy (función 5F de ciclos.py)
//   - enseña sus 5 últimos periodos (función 5G de ciclos.py)
// Todo sale de la misma ruta: /dashboard.

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
    const listaPeriodos = document.querySelector("#lista-periodos");


    // ---------------------------------------------------------------
    // FUNCIÓN: convierte "2026-11-04" en "04/11" (día/mes, que es lo que cabe en la fila)
    // ---------------------------------------------------------------
    function diaYMes(texto) {
        const partes = texto.split("-");            // ["2026", "11", "04"]
        return `${partes[2]}/${partes[1]}`;
    }


    // ---------------------------------------------------------------
    // FUNCIÓN: pinta la lista de últimos periodos
    // ---------------------------------------------------------------
    // Recibe la lista que manda el servidor, por ejemplo:
    //   [{inicio: "2026-11-04", fin: "2026-11-09", duracion: 6}, {inicio: "...", fin: null, duracion: null}]
    // Usamos createElement + textContent (y no innerHTML con los datos) para que
    // ningún texto pueda colarse como código HTML: es parte de la protección contra XSS.
    function mostrarPeriodos(periodos) {
        listaPeriodos.innerHTML = "";               // quitamos el "Cargando..."

        if (periodos.length === 0) {
            const vacio = document.createElement("li");
            vacio.className = "texto-vacio";
            vacio.textContent = "Todavía no has registrado ningún periodo";
            listaPeriodos.appendChild(vacio);
            return;
        }

        periodos.forEach((periodo) => {
            // <li class="fila-periodo">
            const fila = document.createElement("li");
            fila.className = "fila-periodo";

            //   <span class="fechas-periodo"><span class="punto"></span>04/11 – 09/11</span>
            const fechas = document.createElement("span");
            fechas.className = "fechas-periodo";
            const punto = document.createElement("span");
            punto.className = "punto";
            fechas.appendChild(punto);
            // Si sigue en curso no hay fin: ponemos "ahora"
            const textoFin = periodo.fin ? diaYMes(periodo.fin) : "ahora";
            fechas.append(`${diaYMes(periodo.inicio)} – ${textoFin}`);

            //   <span class="duracion">6 días</span>   (o "En curso")
            const duracion = document.createElement("span");
            duracion.className = "duracion";
            if (periodo.duracion === null) {
                duracion.textContent = "En curso";
            } else {
                duracion.textContent = `${periodo.duracion} ${periodo.duracion === 1 ? "día" : "días"}`;
            }

            fila.appendChild(fechas);
            fila.appendChild(duracion);
            listaPeriodos.appendChild(fila);
        });
    }


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
            mostrarPeriodos([]);
            return;
        }

        // ÚLTIMOS PERIODOS
        mostrarPeriodos(datos.ultimos_periodos);

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
        listaPeriodos.innerHTML = "";
    }
});
