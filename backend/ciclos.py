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
    resultado = fin - inicio            # restar dos fechas da un timedelta (una cantidad de tiempo)
    return resultado.days               # .days saca solo el número de días


# FUNCIÓN 2: días entre el inicio de un periodo y el inicio del siguiente
# Devuelve una lista de números, por ejemplo [31, 28, 31]
def calcular_tiempo_entre_periodos(periodos) -> list:
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
    # Si la lista está vacía no se puede calcular (dividiríamos entre 0)
    if len(dias_entre_periodos) < 1:
        print("No podemos calcular la media todavía")
        return 0
    return round(sum(dias_entre_periodos) / len(dias_entre_periodos))


# FUNCIÓN 4: predecir la fecha del próximo periodo
# Usa las funciones 2 y 3. Devuelve una fecha, o None si no hay datos suficientes.
def predecir_proximo_periodo(periodos) -> date:
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
    dia_actual = date.today()                       # la fecha de hoy
    dia_ciclo_actual = dia_actual - fecha_inicio    # restar fechas da la diferencia (timedelta)
    # +1 porque el día en que empieza la regla ya es el "día 1", no el "día 0"
    return dia_ciclo_actual.days + 1


# ---------------------------------------------------------------
# VALIDACIONES  (todas devuelven True si se puede guardar y False si no)
# ---------------------------------------------------------------

# FUNCIÓN 6: comprobar que la fecha de inicio de un periodo nuevo es válida
# Regla: no se puede registrar una regla que empiece en el futuro.
def validar_inicio_nuevo_periodo(inicio) -> bool:
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
    if fin <= date.today() and inicio < fin:
        return True
    return False


# FUNCIÓN 8: comprobar que un periodo nuevo no se pisa con los que ya hay
# Recibe la lista de periodos guardados y la fecha de inicio del nuevo.
# Devuelve False si el nuevo empieza a menos de 15 días de algún periodo ya guardado,
# y True si está lejos de todos (se puede guardar).
def solapamiento_ciclos(periodos, inicio) -> bool:
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
    # "in" mira si el valor está dentro de la lista: devuelve True o False directamente
    return sintoma in SINTOMAS_VALIDOS
