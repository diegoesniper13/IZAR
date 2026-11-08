// principal.js
// Carga los datos de la pantalla principal y hace funcionar el botón de registrar periodo,
// que abre una ventana con calendario para elegir las fechas.

// Esperamos a que todo el HTML de la página esté completamente cargado antes de ejecutar nada
document.addEventListener("DOMContentLoaded", () => {

    // --- Partes del HTML que vamos a usar (las buscamos por su id) ---
    // Círculo de la pantalla principal
    const tituloCirculo = document.querySelector("#dia-ciclo");
    const subtituloCirculo = document.querySelector("#proximo-periodo");
    // Botón que abre la ventana
    const botonRegistro = document.querySelector("#registro");
    // Ventana del calendario y lo que hay dentro
    const ventana = document.querySelector("#ventana-registro");
    const tituloVentana = document.querySelector("#titulo-ventana");
    const infoInicio = document.querySelector("#info-inicio");
    const campoInicio = document.querySelector("#campo-inicio");
    const inputInicio = document.querySelector("#fecha-inicio");
    const inputFin = document.querySelector("#fecha-fin");
    const ayudaFin = document.querySelector("#ayuda-fin");
    const mensaje = document.querySelector("#mensaje");
    const botonGuardar = document.querySelector("#guardar-periodo");
    const botonCancelar = document.querySelector("#cancelar-periodo");

    // Datos que rellena cargarDashboard() y que usa la ventana:
    let periodoAbierto = false;    // ¿hay un periodo sin fin?
    let inicioAbierto = null;      // si lo hay, su fecha de inicio ("2026-10-30")


    // ---------------------------------------------------------------
    // FUNCIÓN: devuelve la fecha de hoy como texto "año-mes-día"
    // ---------------------------------------------------------------
    // No usamos toISOString() porque da la fecha en hora UTC, y en España
    // entre las 00:00 y la 01:00 (o 02:00 en verano) daría el día anterior.
    function fechaDeHoy() {
        const hoy = new Date();
        const anio = hoy.getFullYear();
        // getMonth() empieza en 0 (enero = 0), por eso sumamos 1.
        // padStart(2, "0") pone un 0 delante si hace falta: 7 -> "07"
        const mes = String(hoy.getMonth() + 1).padStart(2, "0");
        const dia = String(hoy.getDate()).padStart(2, "0");
        return `${anio}-${mes}-${dia}`;
    }

    // ---------------------------------------------------------------
    // FUNCIÓN: convierte "2026-10-30" en "30/10/2026" para enseñarlo bonito
    // ---------------------------------------------------------------
    function fechaLegible(texto) {
        // split("-") corta el texto por los guiones: ["2026", "10", "30"]
        const partes = texto.split("-");
        return `${partes[2]}/${partes[1]}/${partes[0]}`;
    }

    // ---------------------------------------------------------------
    // FUNCIÓN: suma días a una fecha en texto: ("2026-09-10", 14) -> "2026-09-24"
    // ---------------------------------------------------------------
    function sumarDias(texto, dias) {
        const partes = texto.split("-");             // ["2026", "09", "10"]
        // new Date(año, mes, día): el mes empieza en 0, por eso restamos 1.
        // Si el día se pasa del mes (por ejemplo 35 de septiembre), JavaScript
        // salta solo al mes siguiente (5 de octubre).
        const fecha = new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]) + dias);
        const anio = fecha.getFullYear();
        const mes = String(fecha.getMonth() + 1).padStart(2, "0");
        const dia = String(fecha.getDate()).padStart(2, "0");
        return `${anio}-${mes}-${dia}`;
    }

    // ---------------------------------------------------------------
    // FUNCIÓN: ajusta el calendario del FIN a partir de la fecha de inicio
    // ---------------------------------------------------------------
    // El calendario de un <input type="date"> vacío se abre en el mes de hoy,
    // salvo que hoy quede fuera de los límites min/max: entonces se abre en el límite.
    // Por eso limitamos el fin a como mucho 14 días después del inicio
    // (ninguna regla dura tanto): si el inicio fue en septiembre, el calendario
    // del fin se abre en septiembre.
    const DIAS_MAXIMOS_PERIODO = 14;                 // duración máxima que dejamos elegir (en días)

    function ajustarCalendarioFin(inicio) {
        const hoy = fechaDeHoy();
        let limite = sumarDias(inicio, DIAS_MAXIMOS_PERIODO);
        // El fin tampoco puede ser futuro: si el límite pasa de hoy, el límite es hoy.
        // Los textos "año-mes-día" se pueden comparar con < y > como si fueran fechas.
        if (limite > hoy) {
            limite = hoy;
        }
        inputFin.min = inicio;                       // no antes del inicio
        inputFin.max = limite;                       // ni más de 14 días después (ni futuro)
    }


    // ---------------------------------------------------------------
    // FUNCIÓN: pide los datos a /dashboard y actualiza la pantalla
    // ---------------------------------------------------------------
    // Va en una función porque la usamos dos veces: al abrir la página
    // y después de guardar un periodo (para que se vean los datos nuevos).
    async function cargarDashboard() {
        try {
            // 1. PEDIR DATOS AL SERVIDOR
            // Como es el mismo servidor que sirve la página, el navegador envía
            // la cookie de sesión solo, y así Flask sabe quién somos.
            const respuesta = await fetch("/dashboard");

            // 2. COMPROBAR SEGURIDAD: 401 = no hay sesión, mandamos a iniciar sesión
            if (respuesta.status === 401) {
                window.location.href = "login.html";
                return;
            }

            // 3. LEER LA RESPUESTA: el JSON de Python pasa a ser un objeto de JavaScript
            const datos = await respuesta.json();

            // 4. GUARDAR SI HAY PERIODO ABIERTO y cambiar el texto del botón
            periodoAbierto = datos.periodo_abierto;
            inicioAbierto = datos.inicio_ultimo;     // solo lo usaremos si periodoAbierto es true
            if (periodoAbierto) {
                botonRegistro.textContent = "TERMINAR PERIODO";
            } else {
                botonRegistro.textContent = "REGISTRAR PERIODO (+)";
            }

            // 5. ACTUALIZAR EL CÍRCULO
            if (datos.estado === "ok") {
                // El número del día lo calculó ciclos.py
                tituloCirculo.textContent = `Día ${datos.dia_ciclo} de tu ciclo`;

                const dias = datos.dias_restantes;
                if (dias === null) {
                    // Con un solo periodo registrado no hay media posible aún
                    subtituloCirculo.textContent = "Faltan datos para predecir";
                } else if (dias > 1) {
                    subtituloCirculo.textContent = `Próximo periodo en ${dias} días`;
                } else if (dias === 1) {
                    subtituloCirculo.textContent = "Próximo periodo mañana";
                } else if (dias === 0) {
                    subtituloCirculo.textContent = "Tu periodo podría empezar hoy";
                } else {
                    // dias negativo: la fecha prevista ya pasó (Math.abs quita el signo menos)
                    const retraso = Math.abs(dias);
                    subtituloCirculo.textContent = `Retraso de ${retraso} ${retraso === 1 ? "día" : "días"}`;
                }
            }
            else if (datos.estado === "nuevo") {
                // Cuenta nueva sin ningún periodo registrado
                tituloCirculo.textContent = "¡Bienvenida!";
                subtituloCirculo.textContent = datos.mensaje;   // "Registra tu primer periodo"
            }

        } catch (error) {
            // Si el servidor está apagado o falla la conexión
            console.error("Error de conexión:", error);
            tituloCirculo.textContent = "Error al cargar";
            subtituloCirculo.textContent = "Comprueba tu conexión";
        }
    }


    // ---------------------------------------------------------------
    // BOTÓN "REGISTRAR / TERMINAR": prepara la ventana y la abre
    // ---------------------------------------------------------------
    botonRegistro.addEventListener("click", () => {
        const hoy = fechaDeHoy();

        // Vaciamos lo que quedara de la última vez
        mensaje.textContent = "";
        inputInicio.value = "";
        inputFin.value = "";

        // max = el calendario no deja elegir días futuros
        inputInicio.max = hoy;
        inputFin.max = hoy;

        if (periodoAbierto) {
            // MODO TERMINAR: el inicio ya está guardado, solo se elige el fin
            tituloVentana.textContent = "Terminar periodo";
            infoInicio.textContent = `Tu periodo empezó el ${fechaLegible(inicioAbierto)}`;
            infoInicio.classList.remove("oculto");
            campoInicio.classList.add("oculto");     // escondemos el campo de inicio
            ayudaFin.classList.add("oculto");        // aquí el fin es obligatorio
            // El calendario del fin se abre cerca del inicio (entre el inicio y 14 días después)
            ajustarCalendarioFin(inicioAbierto);
            // Propuesta: hoy, pero solo si hoy cabe dentro de esos límites.
            // Si el periodo empezó hace mucho, lo dejamos vacío y el calendario
            // se abre en el mes del inicio.
            if (hoy <= inputFin.max) {
                inputFin.value = hoy;
            }
        } else {
            // MODO REGISTRAR: se elige el inicio y, si ya acabó, también el fin
            tituloVentana.textContent = "Registrar periodo";
            infoInicio.classList.add("oculto");
            campoInicio.classList.remove("oculto");
            ayudaFin.classList.remove("oculto");     // "Déjala vacía si sigue en curso"
            inputInicio.value = hoy;                 // propuesta: hoy (se puede cambiar)
            ajustarCalendarioFin(hoy);               // límites del fin según ese inicio
        }

        // showModal() abre la ventana encima de la página y bloquea lo de detrás
        ventana.showModal();
    });


    // Cuando cambia el inicio, recolocamos el calendario del fin para que se abra
    // en el mes de ese inicio (por ejemplo, inicio en septiembre -> fin en septiembre)
    inputInicio.addEventListener("change", () => {
        if (inputInicio.value === "") {
            return;                                  // si lo han borrado, no hay nada que ajustar
        }
        ajustarCalendarioFin(inputInicio.value);
        // Si ya había un fin elegido que ahora queda fuera de los límites, lo borramos
        if (inputFin.value !== "" && (inputFin.value < inputFin.min || inputFin.value > inputFin.max)) {
            inputFin.value = "";
        }
    });


    // ---------------------------------------------------------------
    // BOTÓN "CANCELAR": cierra la ventana sin guardar nada
    // ---------------------------------------------------------------
    botonCancelar.addEventListener("click", () => {
        ventana.close();
    });


    // ---------------------------------------------------------------
    // BOTÓN "GUARDAR": envía las fechas elegidas al servidor
    // ---------------------------------------------------------------
    botonGuardar.addEventListener("click", async () => {
        mensaje.textContent = "";

        // 1. ELEGIR RUTA Y DATOS según el modo
        let ruta;
        let cuerpo;
        if (periodoAbierto) {
            // Terminar: solo mandamos la fecha de fin
            if (inputFin.value === "") {
                mensaje.textContent = "Elige la fecha de fin";
                return;                              // no seguimos sin fecha
            }
            ruta = "/periodo/fin";
            cuerpo = { fecha: inputFin.value };
        } else {
            // Registrar: el inicio es obligatorio, el fin opcional
            if (inputInicio.value === "") {
                mensaje.textContent = "Elige la fecha de inicio";
                return;
            }
            ruta = "/periodo";
            cuerpo = { fecha: inputInicio.value };
            // Solo añadimos "fin" si ha elegido una fecha; si no, el periodo queda en curso
            if (inputFin.value !== "") {
                cuerpo.fin = inputFin.value;
            }
        }

        // Desactivamos el botón mientras esperamos, para que no se pulse dos veces
        botonGuardar.disabled = true;

        try {
            // 2. ENVIAR AL SERVIDOR (el valor de un input type="date" ya es "año-mes-día")
            const respuesta = await fetch(ruta, {
                method: "POST",
                headers: { "Content-Type": "application/json" },   // avisa a Flask de que va JSON
                body: JSON.stringify(cuerpo)                       // objeto -> texto JSON
            });

            if (respuesta.status === 401) {          // la sesión ha caducado
                window.location.href = "login.html";
                return;
            }

            const datos = await respuesta.json();

            // 3. RESULTADO: respuesta.ok es true con los códigos 200-299 (nuestros 200 y 201)
            if (respuesta.ok) {
                ventana.close();                     // todo bien: cerramos la ventana
                await cargarDashboard();             // y recargamos el círculo y el botón
            } else {
                // Mostramos dentro de la ventana el error que mandó app.py
                mensaje.textContent = datos.error;
            }

        } catch (error) {
            console.error("Error de conexión:", error);
            mensaje.textContent = "No se pudo conectar con el servidor";
        }

        botonGuardar.disabled = false;               // volvemos a activar el botón
    });


    // ---------------------------------------------------------------
    // FUNCIÓN: pinta en rosa el día de la semana de hoy en la tira L M X J V S D
    // ---------------------------------------------------------------
    function marcarDiaDeHoy() {
        // querySelectorAll devuelve TODOS los .dia, en el orden del HTML:
        // posición 0 = L, 1 = M, 2 = X ... 6 = D
        const dias = document.querySelectorAll(".dia");

        // getDay() da el día de la semana como número, pero EMPIEZA EN DOMINGO:
        // 0 = domingo, 1 = lunes, 2 = martes ... 6 = sábado
        const diaSemana = new Date().getDay();

        // Lo pasamos a nuestro orden, que empieza en lunes (lunes = 0 ... domingo = 6).
        // Sumamos 6 y nos quedamos con el resto de dividir entre 7 (%):
        //   lunes:   (1 + 6) % 7 = 0      martes: (2 + 6) % 7 = 1
        //   domingo: (0 + 6) % 7 = 6
        const posicion = (diaSemana + 6) % 7;

        // Le ponemos la clase "activo" (en styles.css lo pinta de rosa)
        dias[posicion].classList.add("activo");
    }


    // ---------------------------------------------------------------
    // BOTONES DE SÍNTOMAS: guardan el síntoma con la fecha de hoy
    // ---------------------------------------------------------------
    // Solo los botones que tienen data-sintoma (los 4 síntomas). El botón "Borrar hoy"
    // también usa la clase boton-sintoma para verse igual, pero no tiene data-sintoma,
    // así que este selector lo deja fuera.
    const botonesSintoma = document.querySelectorAll(".boton-sintoma[data-sintoma]");
    const mensajeSintomas = document.querySelector("#mensaje-sintomas");

    // forEach recorre la lista de botones y le pone a CADA uno el mismo "escuchador" de clic
    botonesSintoma.forEach((boton) => {
        boton.addEventListener("click", async () => {
            // dataset.sintoma lee el atributo data-sintoma del HTML: "colicos", "flujo"...
            const sintoma = boton.dataset.sintoma;
            // Texto visible del botón sin el emoji, para los mensajes ("Cólicos").
            // Quitamos el texto del <span> (el emoji) y los espacios de los lados con trim().
            const emoji = boton.querySelector("span").textContent;
            const nombreVisible = boton.textContent.replace(emoji, "").trim();

            // Quitamos el mensaje anterior
            mensajeSintomas.textContent = "";
            mensajeSintomas.classList.remove("error");

            boton.disabled = true;                   // evita dos clics seguidos mientras esperamos

            try {
                // Enviamos {"fecha": "2026-11-05", "sintoma": "colicos"} a la ruta 7 de app.py
                const respuesta = await fetch("/sintoma", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ fecha: fechaDeHoy(), sintoma: sintoma })
                });

                if (respuesta.status === 401) {      // la sesión ha caducado
                    window.location.href = "login.html";
                    return;
                }

                // 500 = el servidor ha fallado por dentro (un error de Python).
                // En ese caso Flask no devuelve JSON sino una página HTML, y .json() fallaría:
                // por eso lo comprobamos antes y lo explicamos. El detalle está en la terminal de Flask.
                if (respuesta.status === 500) {
                    mensajeSintomas.textContent = "Error en el servidor. Mira la terminal de Flask";
                    mensajeSintomas.classList.add("error");
                    boton.disabled = false;
                    return;
                }

                const datos = await respuesta.json();

                // Los botones son de un solo clic: no se quedan marcados.
                // Lo único que cambia es el mensaje de debajo.
                if (respuesta.ok) {
                    // 201: guardado
                    mensajeSintomas.textContent = `${nombreVisible}: guardado para hoy`;
                } else if (respuesta.status === 409) {
                    // 409: ya estaba guardado hoy. No es un fallo grave: solo lo avisamos.
                    mensajeSintomas.textContent = `${nombreVisible}: ya estaba registrado hoy`;
                } else {
                    // Cualquier otro error: mostramos el mensaje que mandó app.py, en rojo
                    mensajeSintomas.textContent = datos.error;
                    mensajeSintomas.classList.add("error");
                }

            } catch (error) {
                console.error("Error de conexión:", error);
                mensajeSintomas.textContent = "No se pudo conectar con el servidor";
                mensajeSintomas.classList.add("error");
            }

            boton.disabled = false;                  // volvemos a activar el botón
        });
    });


    // ---------------------------------------------------------------
    // BOTÓN "BORRAR HOY": borra todos los síntomas registrados hoy
    // ---------------------------------------------------------------
    const botonBorrar = document.querySelector("#borrar-sintomas");

    botonBorrar.addEventListener("click", async () => {
        // Pedimos confirmación antes de borrar: borrar no se puede deshacer.
        // confirm() enseña una ventanita del navegador con "Aceptar" y "Cancelar".
        if (!confirm("¿Borrar todos los síntomas que has registrado hoy?")) {
            return;                                  // ha pulsado Cancelar: no hacemos nada
        }

        mensajeSintomas.textContent = "";
        mensajeSintomas.classList.remove("error");
        botonBorrar.disabled = true;                 // evita dos clics seguidos mientras esperamos

        try {
            // Enviamos {"fecha": "2026-11-08"} a la ruta 8 de app.py
            const respuesta = await fetch("/sintoma/borrar", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ fecha: fechaDeHoy() })
            });

            if (respuesta.status === 401) {          // la sesión ha caducado
                window.location.href = "login.html";
                return;
            }

            const datos = await respuesta.json();

            if (respuesta.ok) {
                // El servidor dice cuántos ha borrado: elegimos el mensaje según el número
                if (datos.borrados === 0) {
                    mensajeSintomas.textContent = "No había síntomas registrados hoy";
                } else if (datos.borrados === 1) {
                    mensajeSintomas.textContent = "Se ha borrado 1 síntoma de hoy";
                } else {
                    mensajeSintomas.textContent = `Se han borrado ${datos.borrados} síntomas de hoy`;
                }
            } else {
                // Cualquier error: mostramos el mensaje que mandó app.py, en rojo
                mensajeSintomas.textContent = datos.error;
                mensajeSintomas.classList.add("error");
            }

        } catch (error) {
            console.error("Error de conexión:", error);
            mensajeSintomas.textContent = "No se pudo conectar con el servidor";
            mensajeSintomas.classList.add("error");
        }

        botonBorrar.disabled = false;                // volvemos a activar el botón
    });


    // Al abrir la página: marcamos el día de hoy (no necesita al servidor)
    // y cargamos los datos por primera vez
    marcarDiaDeHoy();
    cargarDashboard();
});
