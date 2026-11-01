# bd.py
# Todo lo que habla con la base de datos regla.db: las usuarias y sus periodos.

import os
import sqlite3                                   # módulo para hablar con la base de datos SQLite
from datetime import date                        # para convertir textos como "2026-01-01" en fechas
from werkzeug.security import generate_password_hash, check_password_hash   # para guardar contraseñas de forma segura

# Ruta absoluta de la base de datos: siempre la que está al lado de bd.py,
# sin importar desde qué carpeta se arranque el servidor.
RUTA_BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "regla.db")


# ---------------------------------------------------------------
# PERIODOS
# ---------------------------------------------------------------

# Devuelve los periodos de UNA usuaria, del más antiguo al más reciente.
# "usuario" es el nombre de usuario que está guardado en la sesión.
def obtener_periodos(usuario) -> list:
    conexion = sqlite3.connect(RUTA_BD)          # abre el archivo de la base de datos
    cursor = conexion.cursor()                   # el "mando" para enviar órdenes SQL

    # La tabla periodos guarda el id numérico de la usuaria (usuario_id), pero la sesión
    # tiene su nombre de usuario. La subconsulta (SELECT id FROM usuarios ...) traduce
    # el nombre al id, y el WHERE deja solo los periodos de esa usuaria.
    # ORDER BY inicio: de más antiguo a más reciente, porque ciclos.py usa periodos[-1]
    # como el más reciente.
    # Pedimos solo inicio y fin (no SELECT *) para que cada fila sea (inicio, fin)
    # y no dependa de cuántas columnas tenga la tabla.
    cursor.execute(
        "SELECT inicio, fin FROM periodos "
        "WHERE usuario_id = (SELECT id FROM usuarios WHERE usuario = ?) "
        "ORDER BY inicio",
        (usuario,)                               # el valor del ? va en una tupla (con coma al final)
    )
    filas = cursor.fetchall()                    # lista de tuplas: [('2026-01-01', '2026-01-06'), ...]
    conexion.close()                             # ya tenemos las filas: cerramos la conexión
    return creador_de_fecha_periodo(filas)


# Traduce las filas al formato que esperan las funciones de ciclos.py
# De: ('2026-01-01', '2026-01-06')                         <- tupla con textos
# A:  {"inicio": date(2026,1,1), "fin": date(2026,1,6)}    <- diccionario con fechas
def creador_de_fecha_periodo(filas) -> list:
    periodos = []
    for fila in filas:
        periodo = {
            # fila[0] es el inicio y fila[1] el fin (ya no hay columna id en el SELECT)
            # date.fromisoformat convierte el texto "año-mes-día" en una fecha de verdad
            "inicio": date.fromisoformat(fila[0]),
            "fin": date.fromisoformat(fila[1])
        }
        periodos.append(periodo)
    return periodos


# Guarda un periodo nuevo a nombre de una usuaria.
# Devuelve True si se guardó, y False si esa usuaria no existe.
def guardar_periodo(usuario, inicio, fin) -> bool:
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    try:
        # Los tres ? se rellenan, por orden, con usuario, inicio y fin.
        # Si el usuario no existe, la subconsulta da "nada" y la base de datos
        # rechaza el INSERT (usuario_id es obligatorio): salta IntegrityError.
        cursor.execute(
            "INSERT INTO periodos (usuario_id, inicio, fin) "
            "VALUES ((SELECT id FROM usuarios WHERE usuario = ?), ?, ?)",
            (usuario, inicio, fin)
        )
        conexion.commit()                        # sin commit el dato NO se guarda en el archivo
    except sqlite3.IntegrityError:
        conexion.close()
        return False
    conexion.close()
    return True


# ---------------------------------------------------------------
# USUARIAS
# ---------------------------------------------------------------

# Crea una cuenta nueva. Devuelve True si se creó, y False si ese usuario ya existe.
def crear_usuario(usuario, nombre, contrasena):
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    hash_contrasena = generate_password_hash(contrasena)      # la contraseña nunca se guarda tal cual
    try:
        cursor.execute(
            "INSERT INTO usuarios (usuario, nombre, contrasena_hash) VALUES (?, ?, ?)",
            (usuario, nombre, hash_contrasena)
        )
        conexion.commit()
    except sqlite3.IntegrityError:               # usuario repetido (la columna es UNIQUE)
        conexion.close()
        return False
    conexion.close()
    return True


# Comprueba usuario y contraseña. Devuelve True si son correctos.
def iniciar_sesion(usuario, contrasena):
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    cursor.execute("SELECT contrasena_hash FROM usuarios WHERE usuario = ?", (usuario,))
    fila = cursor.fetchone()                     # una fila (una tupla con una columna), o None si no existe
    conexion.close()
    if fila is None:
        return False
    # check_password_hash compara la contraseña escrita con el hash guardado (fila[0])
    return check_password_hash(fila[0], contrasena)