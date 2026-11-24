// estadisticas.js
// Pantalla de estadísticas:
//   - comprueba que hay sesión (si no, manda a login.html)
//   - pone el día del ciclo de hoy
//   - enseña los síntomas que es posible que tenga hoy (función 5F de ciclos.py)
//   - enseña sus 5 últimos periodos (función 5G de ciclos.py)
//   - deja eliminar un periodo (papelera de cada fila -> POST /periodo/borrar)
// Todo sale de la misma ruta: /dashboard.

// Cómo se enseña cada síntoma. Las claves son los nombres que guarda la base de datos
// (SINTOMAS_VALIDOS de ciclos.py); los valores, lo que ve la usuaria.
const SINTOMAS_VISIBLES = {
    colicos: { emoji: "〰️", texto: "Cólicos" },
    flujo:   { emoji: "💧", texto: "Flujo" },
    animo:   { emoji: "🙂", texto: "Ánimo" },
    sueno:   { emoji: "💤", texto: "Sueño" }
};

// Cómo se ve cada intensidad. Las claves son los valores que guarda la base de datos
// (INTENSIDADES_VALIDAS de ciclos.py); tiene que ser el mismo texto que usa principal.js
// (OPCIONES_INTENSIDAD) para que la usuaria vea siempre la misma palabra.
const INTENSIDADES_VISIBLES = {
    intenso: "Intenso",
    suave: "Suave",
    mucho: "Mucho",
    normal: "Normal",
    poco: "Poco",
    feliz: "Feliz",
    enfadada: "Enfadada",
    triste: "Triste"
};

// Esperamos a que el HTML esté cargado antes de tocar nada
document.addEventListener("DOMContentLoaded", async () => {

    const numeroDiaCiclo = document.querySelector("#dia-ciclo");
    const listaSintomas = document.querySelector("#lista-sintomas");
    const explicacion = document.querySelector("#explicacion-sintomas");
    const listaPeriodos = document.querySelector("#lista-periodos");
    const mensajePeriodos = document.querySelector("#mensaje-periodos");

    // Ventana de "¿Eliminar este periodo?"
    const ventanaEliminar = document.querySelector("#ventana-eliminar");
    const textoEliminar = document.querySelector("#texto-eliminar");
    const botonConfirmar = document.querySelector("#confirmar-eliminar");
    const botonCancelar = document.querySelector("#cancelar-eliminar");

    // El periodo que se va a borrar: lo guardamos al pulsar la papelera
    // y lo usamos cuando se pulsa ELIMINAR en la ventana
    let periodoAEliminar = null;


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

            //   <button class="boton-eliminar-periodo">🗑️</button>
            const botonEliminar = document.createElement("button");
            botonEliminar.type = "button";
            botonEliminar.className = "boton-eliminar-periodo";
            botonEliminar.textContent = "🗑️";
            // Para lectores de pantalla: el icono solo no dice qué hace
            botonEliminar.setAttribute("aria-label", `Eliminar el periodo que empezó el ${diaYMes(periodo.inicio)}`);
            // Al pulsarla no se borra todavía: primero se pregunta
            botonEliminar.addEventListener("click", () => pedirConfirmacion(periodo));

            // La duración y la papelera van juntas a la derecha de la fila
            const derecha = document.createElement("span");
            derecha.className = "derecha-periodo";
            derecha.appendChild(duracion);
            derecha.appendChild(botonEliminar);

            fila.appendChild(fechas);
            fila.appendChild(derecha);
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
    // FUNCIÓN: pinta una "pastilla" por cada síntoma posible, con su intensidad más común
    // ---------------------------------------------------------------
    // Recibe la lista que manda el servidor, por ejemplo:
    //   [{sintoma: "colicos", intensidad: "intenso"}, {sintoma: "sueno", intensidad: "poco"}]
    function mostrarSintomas(sintomas) {
        listaSintomas.innerHTML = "";               // quitamos el "Cargando..."

        // forEach recorre la lista: una pastilla por síntoma
        sintomas.forEach((item) => {
            // Si llegara un nombre que no conocemos, lo enseñamos tal cual (sin emoji)
            const visible = SINTOMAS_VISIBLES[item.sintoma] || { emoji: "•", texto: item.sintoma };
            // Igual con la intensidad: si no la reconocemos, la enseñamos tal cual
            const intensidadVisible = INTENSIDADES_VISIBLES[item.intensidad] || item.intensidad;

            // Creamos <span class="pastilla pastilla-activa">〰️ Cólicos (Intenso)</span>
            const pastilla = document.createElement("span");
            pastilla.className = "pastilla pastilla-activa";
            pastilla.textContent = `${visible.emoji} ${visible.texto} (${intensidadVisible})`;
            listaSintomas.appendChild(pastilla);
        });
    }


    // ---------------------------------------------------------------
    // FUNCIÓN: pide los datos a /dashboard y pinta toda la pantalla
    // ---------------------------------------------------------------
    // Está en una función para poder llamarla dos veces: al abrir la página
    // y después de eliminar un periodo (para que la lista y las predicciones se actualicen).
    async function cargarEstadisticas() {
        try {
            // Pedimos los datos a la misma ruta que usa la pantalla principal
            const respuesta = await fetch("/dashboard");

            // 401 = no hay sesión: a iniciar sesión
            if (respuesta.status === 401) {
                window.location.href = "login.html";
                return;
            }

            const datos = await respuesta.json();

            // CUENTA NUEVA (o se han borrado todos los periodos): no hay nada que enseñar
            if (datos.estado === "nuevo") {
                mostrarTextoVacio("Registra tu primer periodo para empezar");
                explicacion.textContent = "";
                numeroDiaCiclo.textContent = "–";
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
    }


    // ---------------------------------------------------------------
    // FUNCIÓN: abre la ventana de "¿Eliminar este periodo?"
    // ---------------------------------------------------------------
    function pedirConfirmacion(periodo) {
        periodoAEliminar = periodo;                 // nos lo apuntamos para cuando pulse ELIMINAR
        const textoFin = periodo.fin ? diaYMes(periodo.fin) : "ahora (en curso)";
        textoEliminar.textContent = `Del ${diaYMes(periodo.inicio)} al ${textoFin}. Esta acción no se puede deshacer.`;
        botonConfirmar.disabled = false;
        ventanaEliminar.showModal();
    }

    // CANCELAR: cierra la ventana sin borrar nada
    botonCancelar.addEventListener("click", () => {
        periodoAEliminar = null;
        ventanaEliminar.close();
    });


    // ---------------------------------------------------------------
    // ELIMINAR: manda el periodo a POST /periodo/borrar
    // ---------------------------------------------------------------
    // Le mandamos la fecha de inicio, por ejemplo {"inicio": "2026-11-04"}.
    // Sirve para saber qué periodo es porque dos periodos de la misma
    // usuaria nunca pueden empezar el mismo día (no se pueden solapar).
    botonConfirmar.addEventListener("click", async () => {
        if (periodoAEliminar === null) {
            return;
        }

        // Desactivamos el botón para que no se pueda pulsar dos veces mientras espera
        botonConfirmar.disabled = true;
        mensajePeriodos.textContent = "";
        mensajePeriodos.classList.remove("error");

        try {
            const respuesta = await fetch("/periodo/borrar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ inicio: periodoAEliminar.inicio })
            });

            // 401 = la sesión ha caducado
            if (respuesta.status === 401) {
                window.location.href = "login.html";
                return;
            }

            ventanaEliminar.close();

            if (respuesta.ok) {
                mensajePeriodos.textContent = "Periodo eliminado";
                // Volvemos a pedir los datos: cambia la lista, el día del ciclo y las predicciones
                await cargarEstadisticas();
            } else {
                // 400 / 404...: enseñamos el error que manda el servidor
                const datos = await respuesta.json();
                mensajePeriodos.textContent = datos.error || "No se pudo eliminar el periodo";
                mensajePeriodos.classList.add("error");
            }

        } catch (error) {
            console.error("Error de conexión:", error);
            ventanaEliminar.close();
            mensajePeriodos.textContent = "No se pudo conectar con el servidor";
            mensajePeriodos.classList.add("error");
        }

        periodoAEliminar = null;
    });


    // Al abrir la página, cargamos todo
    cargarEstadisticas();
});
