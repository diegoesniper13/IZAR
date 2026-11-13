# ciclos.py
# Toda la lógica de fechas de la app: cálculos del ciclo y validaciones.
# No sabe nada de la base de datos: recibe fechas o listas de periodos y devuelve resultados.
# Cada periodo es un diccionario:  {"inicio": date(...), "fin": date(...) o None}

from datetime import date, timedelta


# ---------------------------------------------------------------
# CÁLCULOS
# ---------------------------------------------------------------

# FUNCIÓN 1: días que hay entre dos fechas
# Recibe dos fechas (date) y devuelve un número entero.
# Ojo: si "fin" es ANTERIOR a "inicio", el resultado sale negativo (por ejemplo -28).
def calcular_diferencia(inicio, fin) -> int:
    """Devuelve cuántos días hay entre dos fechas (negativo si fin es anterior a inicio)."""
    resultado = fin - inicio            # restar dos fechas da un timedelta (una cantidad de tiempo)
    return resultado.days               # .days saca solo el número de días


# FUNCIÓN 2: días entre el inicio de un periodo y el inicio del siguiente
# Devuelve una lista de números, por ejemplo [31, 28, 31]
def calcular_tiempo_entre_periodos(periodos) -> list:
    """Devuelve una lista con los días que pasaron entre el inicio de cada periodo y el siguiente."""
    # Con 0 o 1 periodos no hay "siguiente" con el que comparar
    if len(periodos) < 2:
        print("No podemos calcular todavía el tiempo")
        return []                       # salimos de la función devolviendo una lista vacía

    dias_entre_periodos = []            # lista vacía donde guardaremos los resultados

    # Recorremos por POSICIÓN (0, 1, 2...) porque necesitamos dos periodos a la vez.
    # El "- 1" es para que el último no intente mirar un "siguiente" que no existe.
    for i in range(len(periodos) - 1):
        periodo_actual = periodos[i]                # el periodo en la posición i
        periodo_siguiente = periodos[i + 1]         # el que viene después
        tiempo_pasado = periodo_siguiente["inicio"] - periodo_actual["inicio"]
        # .days saca el número de días y .append lo añade al final de la lista
        dias_entre_periodos.append(tiempo_pasado.days)

    return dias_entre_periodos



# FUNCIÓN 3: media de una lista de números
# Recibe una lista de días, por ejemplo [31, 28, 31], y devuelve su media redondeada.
def media_de_periodo(dias_entre_periodos) -> int:
    """Devuelve la media (redondeada) de una lista de días entre periodos."""
    # Si la lista está vacía no se puede calcular (dividiríamos entre 0)
    if len(dias_entre_periodos) < 1:
        print("No podemos calcular la media todavía")
        return 0
    return round(sum(dias_entre_periodos) / len(dias_entre_periodos))


# FUNCIÓN 4: predecir la fecha del próximo periodo
# Usa las funciones 2 y 3. Devuelve una fecha, o None si no hay datos suficientes.
def predecir_proximo_periodo(periodos) -> date:
    """Calcula la fecha en la que probablemente empezará el próximo periodo, o None si faltan datos."""
    # Salida temprana: con menos de 2 periodos no hay media que calcular.
    if len(periodos) < 2:
        print("No hay datos suficientes")
        return None                     # None = "no hay predicción"

    ultimo_periodo = periodos[-1]                       # el periodo más reciente
    inicio_ultimo_periodo = ultimo_periodo["inicio"]    # fecha en la que empezó

    # Primero sacamos la lista de días entre periodos (función 2)...
    tiempo_entre_periodos = calcular_tiempo_entre_periodos(periodos)
    # ...y con esa lista calculamos la media (función 3)
    media = media_de_periodo(tiempo_entre_periodos)

    # timedelta(days=media) convierte la media en "una cantidad de días"
    # que se puede sumar a una fecha
    prediccion = inicio_ultimo_periodo + timedelta(days=media)
    return prediccion


# FUNCIÓN 5: en qué día del ciclo está hoy la usuaria
# Recibe la fecha de inicio del último periodo y devuelve un número (1, 2, 3...).
def calcular_dia_actual_ciclo(fecha_inicio) -> int:
    """Devuelve en qué día del ciclo está la usuaria hoy, a partir del inicio de su último periodo."""
    dia_actual = date.today()                       # la fecha de hoy
    dia_ciclo_actual = dia_actual - fecha_inicio    # restar fechas da la diferencia (timedelta)
    # +1 porque el día en que empieza la regla ya es el "día 1", no el "día 0"
    return dia_ciclo_actual.days + 1


# FUNCIÓN 5B: en qué día del ciclo cae una fecha cualquiera (por ejemplo, la de un síntoma)
# Recibe la fecha y la lista de periodos (del más antiguo al más reciente).
# Devuelve el día del ciclo (1, 2, 3...) o None si la fecha es anterior al primer periodo.
# Ejemplo: periodos que empiezan el 10/09 y el 08/10 -> el 12/10 es el día 5.
def calcular_dia_ciclo_fecha(fecha, periodos) -> int | None:
    """Devuelve en qué día del ciclo cae una fecha cualquiera, o None si es anterior al primer periodo."""
    inicio_del_ciclo = None                     # de momento no hemos encontrado ningún ciclo

    # Buscamos el ÚLTIMO periodo que empezó antes de la fecha (o ese mismo día).
    # Como la lista va de antiguo a reciente, cada periodo que cumple sustituye al anterior:
    # al terminar el bucle queda guardado el más reciente, que es el ciclo de esa fecha.
    for periodo in periodos:
        if periodo["inicio"] <= fecha:
            inicio_del_ciclo = periodo["inicio"]

    # Ningún periodo empezó antes: la fecha no pertenece a ningún ciclo registrado
    if inicio_del_ciclo is None:
        return None

    # Días desde el inicio del ciclo hasta la fecha, +1 porque el día del inicio es el "día 1"
    return calcular_diferencia(inicio_del_ciclo, fecha) + 1


# FUNCIÓN 5C: ciclos terminados (los únicos que sirven para hacer estadísticas)
# Un ciclo empieza con una regla y termina cuando empieza la siguiente.
# El ciclo actual (el del último periodo) aún no ha terminado, así que no se incluye.
# Recibe la lista de periodos (del más antiguo al más reciente) y devuelve una lista como:
#   [{"inicio": date(2026, 9, 10), "fin": date(2026, 10, 8)}, ...]
# donde "fin" es el día en que empezó la SIGUIENTE regla.
DIAS_MAXIMOS_CICLO = 45     # un "ciclo" más largo seguramente son meses sin registrar

def obtener_ciclos_terminados(periodos) -> list:
    """Devuelve los ciclos ya terminados (con inicio y fin), descartando el ciclo actual y los irreales."""
    ciclos_terminados = []

    # Recorremos por POSICIÓN para tener cada periodo y el siguiente a la vez.
    # El "- 1" hace que el último no busque un siguiente que no existe;
    # con menos de 2 periodos el bucle no da ninguna vuelta y se devuelve [].
    for i in range(len(periodos) - 1):
        # Días desde el inicio de este periodo hasta el inicio del siguiente
        tiempo_entre_periodos = calcular_diferencia(periodos[i]["inicio"], periodos[i + 1]["inicio"])

        # Solo guardamos los ciclos de duración creíble (45 días o menos)
        if tiempo_entre_periodos <= DIAS_MAXIMOS_CICLO:
            ciclo = {
                "inicio": periodos[i]["inicio"],      # empieza con esta regla...
                "fin": periodos[i + 1]["inicio"]      # ...y termina cuando empieza la siguiente
            }
            ciclos_terminados.append(ciclo)

    return ciclos_terminados


# FUNCIÓN 5D: los síntomas de UN ciclo, cada uno con su día del ciclo
#
# ¿Para qué sirve? Para poder comparar ciclos entre sí. Una fecha como "12/10" no se
# puede comparar con "09/11", pero "día 3 del ciclo" sí se puede comparar con otro
# "día 3 del ciclo". Esta función hace esa traducción para los síntomas de un ciclo.
#
# Recibe:
#   - ciclo: un ciclo terminado de la función 5C, por ejemplo
#            {"inicio": date(2026, 9, 10), "fin": date(2026, 10, 8)}
#   - sintomas: TODOS los síntomas de la usuaria (los que devuelve bd.obtener_sintomas)
# Devuelve SOLO los síntomas de ese ciclo, con el día en vez de la fecha:
#   [{"dia": 1, "sintoma": "colicos"}, {"dia": 25, "sintoma": "sueno"}]
#
# Ejemplo con el ciclo del 10/09 al 08/10:
#   cólicos el 10/09 -> está dentro, es el día 1   -> se añade {"dia": 1, ...}
#   sueño   el 04/10 -> está dentro, es el día 25  -> se añade {"dia": 25, ...}
#   flujo   el 01/09 -> es ANTES del ciclo         -> no se añade
#   cólicos el 08/10 -> ese día ya empieza el ciclo siguiente -> no se añade
def obtener_sintomas_del_ciclo(ciclo, sintomas) -> list:
    """Devuelve los síntomas que caen dentro de un ciclo, con su día del ciclo en vez de su fecha."""
    sintomas_ciclo = []                         # aquí guardamos los síntomas de este ciclo

    for sintoma in sintomas:                    # miramos los síntomas uno a uno
        # ¿Pasó dentro de este ciclo? Tiene que ser:
        #   - el día del inicio o después (>=)
        #   - y ANTES del fin (<, no <=): el día del fin ya es el día 1 del ciclo siguiente
        if sintoma["fecha"] >= ciclo["inicio"] and sintoma["fecha"] < ciclo["fin"]:
            # Día del ciclo: días desde el inicio hasta la fecha, +1 (el inicio es el "día 1")
            diferencia = calcular_diferencia(ciclo["inicio"], sintoma["fecha"]) + 1
            sintoma_ciclo = {
                "dia": diferencia,              # en qué día del ciclo pasó
                "sintoma": sintoma["sintoma"]   # qué síntoma fue
            }
            sintomas_ciclo.append(sintoma_ciclo)

    return sintomas_ciclo

# FUNCIÓN 5E: ¿tuvo este síntoma cerca de este día en UN ciclo concreto?
#
# Es la pregunta que te harías mirando la libreta de un mes:
#   "en este ciclo, ¿tuve cólicos el día 1, 2 o 3?"
#
# Recibe:
#   - sintomas_ciclo: los síntomas de UN ciclo, como los da la 5D
#                     [{"dia": 3, "sintoma": "colicos"}, {"dia": 20, "sintoma": "sueno"}]
#   - nombre: el síntoma que buscamos, por ejemplo "colicos"
#   - dia: el día del ciclo de hoy, por ejemplo 2
# Devuelve True si lo encuentra cerca de ese día y False si no.
#
# "Cerca" = el mismo día o uno antes o después (VENTANA_DIAS = 1). Así, si un mes tuvo
# cólicos el día 2 y otro mes el día 3, cuentan como "el mismo momento del ciclo".
VENTANA_DIAS = 1

def aparece_en_ciclo(sintomas_ciclo, nombre, dia) -> bool:
    """Dice si un síntoma concreto aparece cerca de un día dado, dentro de los síntomas de UN ciclo."""
    for sintoma in sintomas_ciclo:
        # Tienen que cumplirse las DOS cosas:
        #   - que sea el síntoma que buscamos
        #   - que su día esté entre (dia - 1) y (dia + 1), ambos incluidos.
        #     Python deja escribir el "entre" seguido: a <= x <= b
        es_el_sintoma = sintoma["sintoma"] == nombre
        esta_cerca = dia - VENTANA_DIAS <= sintoma["dia"] <= dia + VENTANA_DIAS
        if es_el_sintoma and esta_cerca:
            return True                         # encontrado: no hace falta seguir mirando
    return False                                # hemos mirado todos y no estaba


# FUNCIÓN 5F: síntomas que es probable que tenga HOY, según sus ciclos anteriores
#
# La idea: imagina una libreta por cada ciclo terminado. Para cada síntoma
# (cólicos, flujo, ánimo, sueño) miramos en cuántas libretas aparece cerca del día de hoy.
# Si aparece en al menos la MITAD de ellas, decimos "es posible que tengas...".
#
# Recibe:
#   - dia: el día del ciclo de hoy (el de calcular_dia_actual_ciclo)
#   - periodos: la lista de periodos (de bd.obtener_periodos)
#   - sintomas: la lista de síntomas (de bd.obtener_sintomas)
# Devuelve una lista de nombres, por ejemplo ["colicos", "sueno"],
# o [] si todavía no hay ciclos terminados con síntomas (por ejemplo, en el primer ciclo).
#
# Ejemplo: hoy es el día 2 y hay 2 ciclos con síntomas.
#   Ciclo 1: cólicos el día 2.     Ciclo 2: cólicos el día 3 y sueño el día 20.
#   - colicos: aparece en los 2 ciclos (2 de 2 = 100 %) -> SÍ
#   - sueno:   el día 20 queda lejos del 2 (0 de 2 = 0 %) -> NO
#   Resultado: ["colicos"]
PORCENTAJE_MINIMO = 0.5     # 0.5 = la mitad de los ciclos

def calcular_sintomas_posibles(dia, periodos, sintomas) -> list:
    """Devuelve los síntomas que es probable tener hoy, según lo que pasó en ciclos anteriores."""
    # --- PARTE 1: preparar los ciclos que sirven (la hiciste tú) ---

    # 1. Solo valen los ciclos ya terminados (función 5C)
    ciclos_terminados = obtener_ciclos_terminados(periodos)

    # 2. De cada ciclo sacamos sus síntomas con su día (función 5D).
    #    Los ciclos SIN ningún síntoma no se guardan: ese mes no registró nada,
    #    y si los contáramos bajarían todos los porcentajes sin motivo.
    ciclos_con_sintomas = []
    for ciclo in ciclos_terminados:
        sintomas_ciclo = obtener_sintomas_del_ciclo(ciclo, sintomas)
        if sintomas_ciclo != []:
            ciclos_con_sintomas.append(sintomas_ciclo)

    # 3. Sin ciclos con síntomas no hay con qué comparar (por ejemplo, el primer ciclo)
    if ciclos_con_sintomas == []:
        return []

    # --- PARTE 2: contar en cuántos ciclos aparece cada síntoma cerca de hoy ---
    posibles = []

    for nombre in SINTOMAS_VALIDOS:             # colicos, flujo, animo, sueno
        veces = 0                               # en cuántos ciclos ha aparecido este síntoma

        for sintomas_ciclo in ciclos_con_sintomas:      # miramos ciclo por ciclo ("libreta" a libreta)
            # Cada ciclo suma COMO MUCHO 1: si tuvo cólicos los días 2 y 3,
            # ese ciclo cuenta una sola vez (por eso usamos la 5E, que dice sí o no).
            if aparece_en_ciclo(sintomas_ciclo, nombre, dia):
                veces += 1

        # Proporción de ciclos en los que apareció: 2 de 2 = 1.0 (100 %), 1 de 2 = 0.5 (50 %)...
        proporcion = veces / len(ciclos_con_sintomas)
        if proporcion >= PORCENTAJE_MINIMO:
            posibles.append(nombre)

    return posibles

# FUNCIÓN 5G: los últimos periodos, listos para enseñarlos en Estadísticas
# Recibe la lista de periodos (del más antiguo al más reciente) y cuántos queremos.
# Devuelve los "cantidad" más recientes, del MÁS RECIENTE al más antiguo, así:
#   [{"inicio": date(2026, 11, 4), "fin": date(2026, 11, 9), "duracion": 6}, ...]
# Si un periodo sigue en curso, su "fin" y su "duracion" son None.
def obtener_ultimos_periodos(periodos, cantidad=5) -> list:
    """Devuelve los últimos periodos (con su duración), del más reciente al más antiguo."""
    ultimos = []

    # periodos[-cantidad:] -> los últimos "cantidad" elementos de la lista (si hay menos, los que haya)
    # reversed(...)        -> los recorre al revés, para que el más reciente salga primero
    for periodo in reversed(periodos[-cantidad:]):
        if periodo["fin"] is None:
            duracion = None                     # sigue en curso: aún no sabemos cuánto dura
        else:
            # +1 porque se cuentan el primer y el último día (del 4 al 9 son 6 días de regla)
            duracion = calcular_diferencia(periodo["inicio"], periodo["fin"]) + 1

        ultimos.append({
            "inicio": periodo["inicio"],
            "fin": periodo["fin"],
            "duracion": duracion
        })

    return ultimos


# ---------------------------------------------------------------
# VALIDACIONES  (todas devuelven True si se puede guardar y False si no)
# ---------------------------------------------------------------

# FUNCIÓN 6: comprobar que la fecha de inicio de un periodo nuevo es válida
# Regla: no se puede registrar una regla que empiece en el futuro.
def validar_inicio_nuevo_periodo(inicio) -> bool:
    """Comprueba que el inicio de un periodo nuevo no sea una fecha futura."""
    if inicio <= date.today():          # hoy o un día anterior: válido
        return True
    return False                        # si llega aquí es que la fecha es futura


# FUNCIÓN 7: comprobar que la fecha de fin de un periodo es válida
# Reglas:
#   - fin <= hoy: no se puede terminar una regla en el futuro
#   - inicio < fin: el fin tiene que ser DESPUÉS del inicio. Con "<" (y no "<=")
#     se rechaza también que fin e inicio sean el mismo día, porque un periodo
#     de un solo día no se da por válido en esta app.
# "and" obliga a que se cumplan LAS DOS condiciones a la vez.
def validar_fin_periodo(fin, inicio) -> bool:
    """Comprueba que el fin de un periodo no sea futuro y que vaya después de su inicio."""
    if fin <= date.today() and inicio < fin:
        return True
    return False


# FUNCIÓN 8: comprobar que un periodo nuevo no se pisa con los que ya hay
# Recibe la lista de periodos guardados y la fecha de inicio del nuevo.
# Devuelve False si el nuevo empieza a menos de 15 días de algún periodo ya guardado,
# y True si está lejos de todos (se puede guardar).
def solapamiento_ciclos(periodos, inicio) -> bool:
    """Comprueba que un periodo nuevo no quede demasiado cerca (menos de 15 días) de otro ya guardado."""
    for periodo in periodos:                        # comparamos con cada periodo guardado
        # Días entre el inicio del periodo guardado y el inicio del nuevo.
        # Si el nuevo es MÁS ANTIGUO que el guardado, la resta sale negativa (por ejemplo -28),
        # así que usamos abs() para quitar el signo: solo nos importa la distancia (28).
        distancia = abs(calcular_diferencia(periodo["inicio"], inicio))
        if distancia < 15:
            return False                            # está demasiado cerca: no se puede guardar
    return True                                     # ha pasado todos los periodos sin problema


# FUNCIÓN 9: comprobar que un síntoma es uno de los que existen en la app
# Recibe el nombre del síntoma como texto y devuelve True si es válido.
# Se escriben siempre igual (minúsculas y sin tildes) para que en la base de datos
# "colicos" no aparezca a veces como "Cólicos" y cuente como otro síntoma distinto.
SINTOMAS_VALIDOS = ["colicos", "flujo", "animo", "sueno"]

def validar_sintoma(sintoma) -> bool:
    """Comprueba que el nombre de un síntoma sea uno de los que existen en la app."""
    # "in" mira si el valor está dentro de la lista: devuelve True o False directamente
    return sintoma in SINTOMAS_VALIDOS
