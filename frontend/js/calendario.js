// calendario.js
// Dibuja el calendario mensual: pinta los días de regla real, regla prevista,
// ovulación y días fértiles. Los datos se piden UNA sola vez a /calendario;
// las flechas de mes solo cambian qué mes se enseña en pantalla, no vuelven
// a pedir nada al servidor (las fechas pintadas no cambian al cambiar de mes).

document.addEventListener("DOMContentLoaded", () => {

    // --- Partes del HTML ---
    const tituloMes = document.querySelector("#titulo-mes");
    const diasCalendario = document.querySelector("#dias-calendario");
    const botonMesAnterior = document.querySelector("#mes-anterior");
    const botonMesSiguiente = document.querySelector("#mes-siguiente");
    const explicacion = document.querySelector("#explicacion-calendario");

    // Nombres de los meses, para el título ("Noviembre 2026")
    const NOMBRES_MES = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ];

    // Lo que llega de /calendario se guarda aquí, para no tener que volver a pedirlo
    // cada vez que la usuaria cambia de mes con las flechas.
    let datosCalendario = null;

    // Mes que se está mostrando ahora. Lo guardamos como el día 1 de ese mes,
    // así sumar o restar un mes entero es sencillo (ver cambiarMes).
    let mesMostrado = new Date(new Date().getFullYear(), new Date().getMonth(), 1);


    // ---------------------------------------------------------------
    // FECHAS: convertir entre texto "2026-11-05" y objetos Date
    // ---------------------------------------------------------------
    // OJO: new Date("2026-11-05") lo interpreta como medianoche en UTC, y en España
    // eso puede caer el día ANTERIOR al pintarlo. Por eso convertimos a mano,
    // con año/mes/día sueltos, para que sea siempre la fecha LOCAL correcta.
    function textoAFecha(texto) {
        const partes = texto.split("-");                      // ["2026", "11", "05"]
        // new Date(año, mes, día) con el mes ya en su índice normal (0 = enero)
        return new Date(Number(partes[0]), Number(partes[1]) - 1, Number(partes[2]));
    }

    // Y al revés: de un objeto Date a texto "2026-11-05", para comparar fechas
    // como si fueran texto (más fácil que comparar objetos Date).
    function fechaATexto(fecha) {
        const anio = fecha.getFullYear();
        const mes = String(fecha.getMonth() + 1).padStart(2, "0");
        const dia = String(fecha.getDate()).padStart(2, "0");
        return `${anio}-${mes}-${dia}`;
    }


    // ---------------------------------------------------------------
    // CARGAR LOS DATOS: una sola vez, al abrir la página
    // ---------------------------------------------------------------
    async function cargarCalendario() {
        try {
            const respuesta = await fetch("/calendario");

            if (respuesta.status === 401) {          // la sesión ha caducado
                window.location.href = "login.html";
                return;
            }

            if (respuesta.status === 500) {
                tituloMes.textContent = "Error";
                explicacion.textContent = "Error en el servidor. Mira la terminal de Flask";
                explicacion.classList.add("error");
                return;
            }

            datosCalendario = await respuesta.json();
            dibujarMes();                             // ya tenemos los datos: pintamos el mes actual

        } catch (error) {
            console.error("Error de conexión:", error);
            tituloMes.textContent = "Error";
            explicacion.textContent = "No se pudo conectar con el servidor";
            explicacion.classList.add("error");
        }
    }


    // ---------------------------------------------------------------
    // DIBUJAR EL MES: crea la cuadrícula de días de "mesMostrado"
    // ---------------------------------------------------------------
    function dibujarMes() {
        const anio = mesMostrado.getFullYear();
        const mes = mesMostrado.getMonth();               // 0 = enero

        tituloMes.textContent = `${NOMBRES_MES[mes]} ${anio}`;

        diasCalendario.innerHTML = "";                    // quitamos los días del mes anterior

        // ¿Qué día de la semana es el día 1 de este mes? getDay() empieza en domingo (0),
        // lo pasamos a que empiece en lunes (0), igual que en principal.js.
        const primerDiaSemana = (new Date(anio, mes, 1).getDay() + 6) % 7;

        // Casillas vacías antes del día 1, para que el día 1 caiga en su columna correcta
        for (let i = 0; i < primerDiaSemana; i++) {
            const vacia = document.createElement("div");
            vacia.className = "dia-calendario dia-vacio";
            diasCalendario.appendChild(vacia);
        }

        // new Date(anio, mes + 1, 0) es "el día 0 del mes siguiente", que en JavaScript
        // es justo el ÚLTIMO día de este mes. Así sabemos cuántos días tiene el mes.
        const diasEnEsteMes = new Date(anio, mes + 1, 0).getDate();
        const textoHoy = fechaATexto(new Date());

        for (let dia = 1; dia <= diasEnEsteMes; dia++) {
            const fecha = new Date(anio, mes, dia);
            const textoFecha = fechaATexto(fecha);

            const casilla = document.createElement("div");
            casilla.className = "dia-calendario";
            casilla.textContent = dia;

            // ponerClasesDelDia decide si este día es de regla, prevista, fértil u ovulación
            ponerClasesDelDia(casilla, textoFecha);

            if (textoFecha === textoHoy) {
                casilla.classList.add("dia-hoy");
            }

            diasCalendario.appendChild(casilla);
        }

        actualizarExplicacion();
    }


    // ---------------------------------------------------------------
    // ¿QUÉ ES ESTE DÍA? Le pone a la casilla la clase que corresponda
    // ---------------------------------------------------------------
    // El orden importa: miramos primero lo más "fuerte" (regla real) y solo si
    // no es eso miramos lo siguiente, para que un día no intente ser dos cosas a la vez.
    function ponerClasesDelDia(casilla, textoFecha) {
        if (estaDentroDeAlgunPeriodo(textoFecha)) {
            casilla.classList.add("dia-regla");
            return;
        }

        const prediccion = datosCalendario.prediccion;
        if (prediccion.inicio_periodo && estaEnRangoPrevisto(textoFecha)) {
            casilla.classList.add("dia-regla-prevista");
            return;
        }

        if (prediccion.ovulacion && textoFecha === prediccion.ovulacion) {
            casilla.classList.add("dia-ovulacion");
            return;
        }

        if (prediccion.ventana_fertil_inicio && prediccion.ventana_fertil_fin &&
            textoFecha >= prediccion.ventana_fertil_inicio && textoFecha <= prediccion.ventana_fertil_fin) {
            casilla.classList.add("dia-fertil");
        }
    }

    // ¿Esta fecha cae dentro de alguno de los periodos reales que manda /calendario?
    // Comparamos como texto ("2026-11-05" <= "2026-11-08"): funciona porque el formato
    // año-mes-día ordena igual en texto que en el tiempo real.
    function estaDentroDeAlgunPeriodo(textoFecha) {
        const textoHoy = fechaATexto(new Date());
        return datosCalendario.periodos.some((periodo) => {
            // Si el periodo sigue en curso (fin == null), lo tratamos como "hasta hoy"
            const fin = periodo.fin ? periodo.fin : textoHoy;
            return textoFecha >= periodo.inicio && textoFecha <= fin;
        });
    }

    // ¿Esta fecha cae dentro del rango previsto de la próxima regla?
    // Si no hay duracion_periodo todavía, el rango previsto es solo ese día (el de inicio).
    function estaEnRangoPrevisto(textoFecha) {
        const prediccion = datosCalendario.prediccion;
        const duracion = prediccion.duracion_periodo || 1;
        // Calculamos el último día previsto sumando la duración al inicio previsto
        const inicio = textoAFecha(prediccion.inicio_periodo);
        const fin = new Date(inicio);
        fin.setDate(fin.getDate() + duracion - 1);
        const textoFin = fechaATexto(fin);
        return textoFecha >= prediccion.inicio_periodo && textoFecha <= textoFin;
    }


    // ---------------------------------------------------------------
    // TEXTO DE ABAJO: avisa si todavía no hay predicción
    // ---------------------------------------------------------------
    function actualizarExplicacion() {
        if (datosCalendario.prediccion.inicio_periodo) {
            explicacion.textContent = "";                 // hay predicción: no hace falta avisar de nada
        } else {
            explicacion.textContent = "Registra al menos 2 periodos para ver la predicción";
        }
    }


    // ---------------------------------------------------------------
    // FLECHAS: cambiar de mes (solo redibuja, no vuelve a pedir datos)
    // ---------------------------------------------------------------
    function cambiarMes(diferencia) {
        // Sumar o restar 1 al mes de un Date hace que JavaScript "arrastre" el año
        // automáticamente si hace falta (diciembre + 1 mes = enero del año siguiente).
        mesMostrado = new Date(mesMostrado.getFullYear(), mesMostrado.getMonth() + diferencia, 1);
        if (datosCalendario) {
            dibujarMes();
        }
    }

    botonMesAnterior.addEventListener("click", () => cambiarMes(-1));
    botonMesSiguiente.addEventListener("click", () => cambiarMes(1));


    // Al abrir la página, pedimos los datos una vez
    cargarCalendario();
});
