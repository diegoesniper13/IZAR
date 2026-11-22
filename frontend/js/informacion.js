// informacion.js
// La parte interactiva de la página de Información: "Explora tu ciclo día a día".
//   - crea la tira de 28 casillas (una por día, cada una del color de su fase)
//   - al mover la barra o tocar una casilla, enseña qué pasa ese día
//   - mueve la rayita que marca el día sobre la gráfica de hormonas
// No habla con el servidor: todo es contenido fijo de un ciclo de ejemplo de 28 días.

const DIAS_CICLO = 28;

// Días fértiles del ejemplo: igual que ventana_fertil de ciclos.py,
// 4 días antes de la ovulación (día 14), el propio día y el día siguiente: del 10 al 15
const PRIMER_DIA_FERTIL = 10;
const DIA_OVULACION = 14;
const ULTIMO_DIA_FERTIL = 15;

// ---------------------------------------------------------------
// FUNCIÓN: ¿es fértil este día? (true / false)
// ---------------------------------------------------------------
function esFertil(dia) {
    return dia >= PRIMER_DIA_FERTIL && dia <= ULTIMO_DIA_FERTIL;
}

// ---------------------------------------------------------------
// FUNCIÓN: a qué fase pertenece un día. Devuelve la clase CSS y el nombre visible.
// ---------------------------------------------------------------
function faseDelDia(dia) {
    if (dia <= 5) {
        return { clase: "fase-regla", nombre: "Regla" };
    }
    if (dia < DIA_OVULACION) {
        return { clase: "fase-folicular", nombre: "Fase folicular" };
    }
    if (dia === DIA_OVULACION) {
        return { clase: "fase-ovulacion", nombre: "Ovulación" };
    }
    return { clase: "fase-lutea", nombre: "Fase lútea" };
}

// ---------------------------------------------------------------
// FUNCIÓN: el texto que explica qué pasa ese día
// ---------------------------------------------------------------
function textoDelDia(dia) {
    if (dia === 1) {
        return "Empieza la regla: es el día 1 y arranca un ciclo nuevo. El estrógeno y la progesterona están bajos.";
    }
    if (dia <= 5) {
        return "Sigues con la regla: el útero suelta el endometrio. Es normal tener cólicos y algo de cansancio.";
    }
    if (dia < PRIMER_DIA_FERTIL) {
        return "Se acabó la regla. En el ovario crecen los folículos y el estrógeno sube: mucha gente nota más energía.";
    }
    if (dia < DIA_OVULACION) {
        return "Días fértiles. El estrógeno está alto y el flujo se vuelve más transparente.";
    }
    if (dia === DIA_OVULACION) {
        return "¡Ovulación! Un pico de LH hace que el ovario suelte un óvulo. Es el día más fértil del ciclo.";
    }
    if (dia === ULTIMO_DIA_FERTIL) {
        return "Empieza la fase lútea, pero todavía es un día fértil: el óvulo puede vivir unas horas más y el flujo sigue siendo transparente.";
    }
    if (dia <= 21) {
        return "El folículo vacío se convierte en el cuerpo lúteo y fabrica progesterona, que engorda el endometrio.";
    }
    return "Final del ciclo. Si no hay embarazo, las hormonas bajan y pueden aparecer síntomas premenstruales: hinchazón, cambios de ánimo, pecho sensible...";
}

// ---------------------------------------------------------------
// FUNCIÓN: dónde cae un día en la gráfica, en % del ancho de la imagen.
// ---------------------------------------------------------------
// Estos números salen de cómo está dibujada img/hormonas.svg: mide 320 de ancho,
// el día 1 está en x = 34 y el día 28 en x = 310.
function posicionEnGrafica(dia) {
    const x = 34 + (dia - 1) * (310 - 34) / (DIAS_CICLO - 1);
    return (x / 320) * 100;
}


document.addEventListener("DOMContentLoaded", () => {

    const tira = document.querySelector("#tira-dias");
    const selector = document.querySelector("#selector-dia");
    const infoDia = document.querySelector("#info-dia");
    const numeroDia = document.querySelector("#numero-dia");
    const faseDia = document.querySelector("#fase-dia");
    const textoDia = document.querySelector("#texto-dia");
    const marcador = document.querySelector("#marcador-dia");

    // 1. Creamos las 28 casillas de la tira (con createElement, como en el resto de la app)
    const casillas = [];
    for (let dia = 1; dia <= DIAS_CICLO; dia++) {
        const casilla = document.createElement("button");
        casilla.type = "button";
        casilla.className = `celda-dia ${faseDelDia(dia).clase}`;
        // Los días fértiles llevan una rayita verde debajo (clase "fertil")
        if (esFertil(dia)) {
            casilla.classList.add("fertil");
        }
        casilla.textContent = dia;
        casilla.setAttribute("aria-label", `Día ${dia}`);
        // Tocar una casilla = elegir ese día
        casilla.addEventListener("click", () => mostrarDia(dia));
        tira.appendChild(casilla);
        casillas.push(casilla);
    }

    // 2. FUNCIÓN: enseña toda la información de un día
    function mostrarDia(dia) {
        const fase = faseDelDia(dia);

        // La barra se pone en ese día (por si se eligió tocando una casilla)
        selector.value = dia;

        // Textos de la tarjeta
        numeroDia.textContent = dia;
        faseDia.textContent = fase.nombre;
        // Los días fértiles (menos la ovulación, que ya lo dice su nombre) lo añaden al título
        if (esFertil(dia) && dia !== DIA_OVULACION) {
            faseDia.textContent += " · día fértil";
        }
        textoDia.textContent = textoDelDia(dia);

        // Color de la tarjeta: quitamos la clase de fase que tuviera y ponemos la nueva
        infoDia.classList.remove("fase-regla", "fase-folicular", "fase-ovulacion", "fase-lutea");
        infoDia.classList.add(fase.clase);

        // Marcamos la casilla elegida (y desmarcamos las demás)
        casillas.forEach((casilla, i) => {
            casilla.classList.toggle("seleccionado", i + 1 === dia);
        });

        // Movemos la rayita de la gráfica
        marcador.style.left = `${posicionEnGrafica(dia)}%`;
    }

    // 3. Al mover la barra. "input" salta mientras arrastras (no solo al soltar).
    //    selector.value es texto ("14"): Number() lo convierte en número.
    selector.addEventListener("input", () => mostrarDia(Number(selector.value)));

    // 4. Al cargar la página enseñamos el día 1
    mostrarDia(1);
});
