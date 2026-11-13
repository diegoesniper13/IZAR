# bd.py
# Todo lo que habla con la base de datos regla.db: las usuarias y sus periodos.

import os                                        # para construir la ruta del archivo regla.db
import sqlite3                                  # módulo para hablar con la base de datos SQLite
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
    """Devuelve la lista de periodos de una usuaria, del más antiguo al más reciente."""
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
    """Convierte filas de la base de datos (textos) en diccionarios con fechas de verdad."""
    periodos = []
    for fila in filas:
        periodo = {
            # fila[0] es el inicio y fila[1] el fin (ya no hay columna id en el SELECT)
            # date.fromisoformat convierte el texto "año-mes-día" en una fecha de verdad
            "inicio": date.fromisoformat(fila[0]),
            # Si el periodo sigue en curso, fin está vacío (None en Python): lo dejamos como None
            "fin": date.fromisoformat(fila[1]) if fila[1] is not None else None
        }
        periodos.append(periodo)
    return periodos



# Guarda un periodo nuevo a nombre de una usuaria.
# Devuelve True si se guardó, y False si esa usuaria no existe.
# fin=None: si no se pasa el fin, se guarda vacío (periodo en curso).
def guardar_periodo(usuario, inicio, fin=None) -> bool:
    """Guarda un periodo nuevo (con o sin fecha de fin) a nombre de una usuaria."""
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

# Pone la fecha de fin al periodo que está abierto (fin vacío) de una usuaria.
# Devuelve True si se actualizó un periodo, y False si no había ninguno abierto.
def final_periodo(usuario, inicio, fin) -> bool:
    """Cierra el periodo abierto de una usuaria, poniéndole la fecha de fin."""
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    try:
        # UPDATE cambia una fila que YA existe (INSERT crearía una nueva).
        # SET fin = ?           -> la columna que cambiamos y su nuevo valor
        # WHERE ... AND ... AND -> qué fila cambiamos; tienen que cumplirse las tres:
        #   - que el periodo sea de esta usuaria (la subconsulta traduce el nombre al id)
        #   - que empiece en la fecha "inicio" que nos pasan
        #   - que siga abierto: fin IS NULL (en SQL lo vacío se mira con IS NULL, no con = NULL)
        # Los ? se rellenan por orden: fin, usuario, inicio.
        cursor.execute(
            "UPDATE periodos SET fin = ? "
            "WHERE usuario_id = (SELECT id FROM usuarios WHERE usuario = ?) "
            "AND inicio = ? "
            "AND fin IS NULL",
            (fin, usuario, inicio)
        )
        conexion.commit()
    except sqlite3.IntegrityError:
        conexion.close()
        return False
    # rowcount = cuántas filas ha cambiado el UPDATE.
    # Si es 0, no había ningún periodo abierto con esos datos: devolvemos False.
    # (Un UPDATE que no encuentra nada NO da error, por eso hace falta esta comprobación.)
    filas_cambiadas = cursor.rowcount
    conexion.close()
    return filas_cambiadas > 0


# ---------------------------------------------------------------
# USUARIAS
# ---------------------------------------------------------------

# Crea una cuenta nueva. Devuelve True si se creó, y False si ese usuario ya existe.
def crear_usuario(usuario, nombre, contrasena) -> bool:
    """Crea una cuenta nueva, guardando el hash de la contraseña (nunca la contraseña tal cual)."""
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

# Cambia la contraseña de una usuaria. Devuelve True si se cambió, y False si esa usuaria no existe.
# "contrasena" llega en texto plano (lo que escribe en el formulario): aquí mismo se calcula
# su hash antes de guardarla, igual que en crear_usuario. La contraseña nunca se guarda tal cual.
def cambiar_contraseña(contrasena,usuario)->bool:
    """Cambia la contraseña de una usuaria, guardando el hash de la nueva."""
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    hash_contrasena = generate_password_hash(contrasena)      # la nueva contraseña, ya convertida a hash
    # UPDATE sobre la fila de esa usuaria: cambia solo contrasena_hash, nada más.
    cursor.execute("UPDATE usuarios SET contrasena_hash = ? WHERE usuario = ?",
                   (hash_contrasena,usuario))
    conexion.commit()                             # sin commit el cambio NO se guarda
    # rowcount = cuántas filas ha cambiado el UPDATE. 0 significa que esa usuaria no existe.
    filas_cambiadas = cursor.rowcount
    conexion.close()
    if filas_cambiadas == 0:
        return False

    return True


# Borra la cuenta de una usuaria y TODOS sus datos. Devuelve True si se borró,
# y False si esa usuaria no existía.
# Importante el ORDEN: primero periodos y síntomas (que dependen del id de la usuaria),
# y solo al final la propia fila de usuarios. Si se borrara usuarios primero, la subconsulta
# (SELECT id FROM usuarios WHERE usuario = ?) ya no encontraría a nadie y no se podría
# borrar lo demás.
def eliminar_cuenta(usuario)->bool:
    """Borra la cuenta de una usuaria y todos sus datos (periodos y síntomas)."""
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    # 1. Primero los periodos de esa usuaria (la subconsulta traduce el nombre a su id)
    cursor.execute("DELETE FROM periodos WHERE usuario_id = (SELECT id FROM usuarios WHERE usuario = ?)",
                   (usuario,))
    # 2. Después sus síntomas
    cursor.execute("DELETE FROM sintomas WHERE usuario_id = (SELECT id FROM usuarios WHERE usuario = ?)",
                   (usuario,))
    # 3. Por último, la propia cuenta
    cursor.execute("DELETE FROM usuarios WHERE usuario = ?",
                     (usuario,))
    conexion.commit()                             # sin commit no se borra nada del archivo
    # rowcount aquí solo refleja el ÚLTIMO execute (el de usuarios), que es justo
    # el que nos interesa: si fue 0, esa usuaria no existía.
    filas_cambiadas = cursor.rowcount
    conexion.close()
    if filas_cambiadas == 0:
        return False
    return True


# Comprueba usuario y contraseña. Devuelve True si son correctos.
def iniciar_sesion(usuario, contrasena) -> bool:
    """Comprueba si el usuario existe y si la contraseña coincide con su hash guardado."""
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    cursor.execute("SELECT contrasena_hash FROM usuarios WHERE usuario = ?", (usuario,))
    fila = cursor.fetchone()                     # una fila (una tupla con una columna), o None si no existe
    conexion.close()
    if fila is None:
        return False
    # check_password_hash compara la contraseña escrita con el hash guardado (fila[0])
    return check_password_hash(fila[0], contrasena)


# ---------------------------------------------------------------
# SÍNTOMAS
# ---------------------------------------------------------------

# Guarda un síntoma de una usuaria en un día concreto.
# "fecha" y "sintoma" llegan como texto, por ejemplo "2026-11-05" y "colicos".
# Devuelve True si se guardó, y False si:
#   - ese síntoma ya estaba guardado ese mismo día (la tabla tiene UNIQUE(usuario_id, fecha, sintoma)), o
#   - la usuaria no existe (la subconsulta da "nada" y usuario_id es obligatorio).
# En los dos casos SQLite da IntegrityError.
def guardar_sintoma(usuario, fecha, sintoma) -> bool:
    """Guarda un síntoma de una usuaria en un día concreto."""
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    try:
        # Los tres ? se rellenan, por orden, con usuario, fecha y sintoma.
        # La subconsulta traduce el nombre de usuario a su id, como en guardar_periodo.
        cursor.execute(
            "INSERT INTO sintomas (usuario_id, fecha, sintoma) "
            "VALUES ((SELECT id FROM usuarios WHERE usuario = ?), ?, ?)",
            (usuario, fecha, sintoma)
        )
        conexion.commit()                        # sin commit el dato NO se guarda en el archivo
    except sqlite3.IntegrityError:               # síntoma repetido ese día o usuaria inexistente
        conexion.close()
        return False
    conexion.close()
    return True
# Guarda que una usuaria ha aceptado los términos y la privacidad, con la fecha de HOY.
# La fecha la pone la propia función (date.today()), así quien la llama no se preocupa de ella.
# Devuelve True si se actualizó una fila, y False si esa usuaria no existe (rowcount == 0).
def guardar_terminos(usuario) -> bool:
    """Marca que una usuaria ha aceptado los términos y la privacidad, con la fecha de hoy."""
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    # UPDATE: rellena la columna acepto_terminos de ESA usuaria con la fecha de hoy.
    # date.today().isoformat() da el texto "2026-11-09", que es como guardamos las fechas.
    cursor.execute(
        "UPDATE usuarios SET acepto_terminos = ? WHERE usuario = ?",
        (date.today().isoformat(), usuario)
    )
    conexion.commit()                            # sin commit el cambio NO se guarda
    # rowcount = cuántas filas ha cambiado. 0 significa que esa usuaria no existe.
    filas_cambiadas = cursor.rowcount
    conexion.close()
    return filas_cambiadas > 0

# Devuelve TODOS los síntomas de una usuaria, del más antiguo al más reciente.
# "usuario" es el nombre de usuario que está guardado en la sesión.
# Si no tiene ninguno, devuelve una lista vacía [].
def obtener_sintomas(usuario) -> list:
    """Devuelve todos los síntomas de una usuaria, del más antiguo al más reciente."""
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    # Igual que en obtener_periodos: la subconsulta traduce el nombre al id,
    # y ORDER BY fecha los ordena de más antiguo a más reciente.
    cursor.execute(
        "SELECT fecha, sintoma FROM sintomas "
        "WHERE usuario_id = (SELECT id FROM usuarios WHERE usuario = ?) "
        "ORDER BY fecha",
        (usuario,)                               # el valor del ? va en una tupla (con coma al final)
    )
    filas = cursor.fetchall()                    # lista de tuplas: [('2026-11-05', 'colicos'), ...]
    conexion.close()
    return creador_de_sintoma(filas)


# Traduce las filas al formato que usarán las funciones de ciclos.py
# De: ('2026-11-05', 'colicos')                             <- tupla con textos
# A:  {"fecha": date(2026, 11, 5), "sintoma": "colicos"}    <- diccionario con la fecha de verdad
# Una fila = un síntoma: si un día hay dos síntomas, salen dos diccionarios con la misma fecha.
def creador_de_sintoma(filas) -> list:
    """Convierte filas de síntomas (textos) en diccionarios con la fecha de verdad."""
    sintomas = []                                # lista donde vamos guardando los diccionarios
    for fila in filas:
        sintoma = {
            "fecha": date.fromisoformat(fila[0]),     # texto "año-mes-día" -> fecha de verdad
            "sintoma": fila[1]                        # el nombre ya es texto: se queda igual
        }
        sintomas.append(sintoma)
    return sintomas                              # la lista completa (no solo el último)


# Borra TODOS los síntomas de una usuaria en un día concreto (el botón "Borrar hoy").
# "fecha" llega como texto, por ejemplo "2026-11-08". La decide la ruta de app.py
# (así esta función sirve para cualquier día, no solo para hoy).
# Devuelve cuántos síntomas se han borrado: 0 si ese día no tenía ninguno.
def eliminar_sintomas(usuario, fecha) -> int:
    """Borra todos los síntomas de una usuaria en un día concreto y dice cuántos ha borrado."""
    conexion = sqlite3.connect(RUTA_BD)
    cursor = conexion.cursor()
    # DELETE borra las filas que cumplan el WHERE. Tienen que cumplirse LAS DOS condiciones:
    #   - que sean de esta usuaria (la subconsulta traduce el nombre al id), para no borrar
    #     nunca los síntomas de otra persona
    #   - que sean de esa fecha
    # OJO: un DELETE sin WHERE borraría la tabla entera. Por eso las condiciones son tan importantes.
    # Los ? se rellenan por orden: usuario y fecha.
    cursor.execute(
        "DELETE FROM sintomas "
        "WHERE usuario_id = (SELECT id FROM usuarios WHERE usuario = ?) "
        "AND fecha = ?",
        (usuario, fecha)
    )
    conexion.commit()                            # sin commit no se borra nada del archivo
    # rowcount = cuántas filas ha borrado el DELETE (como en final_periodo con el UPDATE).
    # Un DELETE que no encuentra nada no da error: simplemente devuelve 0.
    borrados = cursor.rowcount
    conexion.close()
    return borrados
