# ciclos.py
from datetime import date, timedelta

# FUNCIÓN 1: cuántos días dura cada periodo
# Recibe la lista de periodos. Cada periodo es un diccionario:
#   {"inicio": date(...), "fin": date(...)}
# Devuelve un texto con una línea por periodo.
def calcular_diferencia(periodos)-> str:
    resultado = ""                       
    for periodo in periodos:             # recorremos los periodos de uno en uno
        # Restar dos fechas da un objeto con la diferencia; la usamos en el paso siguiente
        diferencia = periodo["fin"] - periodo["inicio"]
        # .days saca el número de días; sumamos 1 para contar también el día de inicio
        # (del 1 al 6 son 5 de diferencia, pero 6 días de periodo)
        resultado += "La diferencia es: " + str(diferencia.days + 1) + "\n"   
    return resultado                     

# FUNCIÓN 2: días entre el inicio de un periodo y el inicio del siguiente

# Devuelve una lista de números, por ejemplo [31, 28, 31]
def calcular_tiempo_entre_periodos(periodos)-> list:
    # Con 0 o 1 periodos no hay "siguiente" con el que comparar
    if len(periodos) < 2:
        print("No podemos calcular todavia el tiempo")
        return[]                         # salimos de la función devolviendo una lista vacía

    dias_entre_periodos = []             # lista vacía donde guardaremos los resultados

    # Recorremos por POSICIÓN (0, 1, 2...) porque necesitamos dos periodos a la vez.
    # El "- 1" es para que el último no intente mirar un "siguiente" que no existe.
    for i in range(len(periodos) -1):
        periodo_actual = periodos[i]             # el periodo en la posición i
        periodo_siguiente = periodos[i + 1]      # el que viene después
        tiempo_pasado = periodo_siguiente["inicio"] - periodo_actual["inicio"]
        # .days saca el número de días y .append lo añade al final de la lista
        dias_entre_periodos.append(tiempo_pasado.days)

    return dias_entre_periodos          


# FUNCIÓN 3: media de una lista de números

# Recibe una lista de días, por ejemplo [31, 28, 31], y devuelve su media.
def media_de_periodo(dias_entre_periodos)-> float:
    # Si la lista está vacía no se puede calcular (dividiríamos entre 0)
    if len(dias_entre_periodos) < 1:
        print("No podemos calcular la media todavia")
        return 0.0
    return round(sum(dias_entre_periodos) / len(dias_entre_periodos))



# FUNCIÓN 4: predecir la fecha del próximo periodo

# Usa las funciones 2 y 3. Devuelve una fecha, o None si no hay datos suficientes.
def predecir_proximo_periodo(periodos)-> date:
    # Salida temprana: con menos de 2 periodos no hay media que calcular.
    if len(periodos) < 2:
        print("No hay datos suficientes")
        return None                      # None = "no hay predicción"

    ultimo_periodo = periodos[-1]                     # Ultimo periodo
    inicio_ultimo_periodo = ultimo_periodo["inicio"]  # fecha en la que empezó el último periodo

    # Primero sacamos la lista de días entre periodos (función 2)...
    tiempo_entre_periodos = calcular_tiempo_entre_periodos(periodos)
    #con esa lista calculamos la media (función 3)
    media = media_de_periodo(tiempo_entre_periodos)

    # timedelta(days=media) convierte la media en "una cantidad de días"
    # que se puede sumar a una fecha
    prediccion = inicio_ultimo_periodo + timedelta(days=media)
    return prediccion                    

def calcular_dia_actual_ciclo(fecha_inicio)->int:
    dia_actual = date.today()
    dia_ciclo_actual = dia_actual - fecha_inicio
    return dia_ciclo_actual.days + 1
