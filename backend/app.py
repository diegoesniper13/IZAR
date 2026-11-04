# app.py
# Servidor Flask de la app. Cada ruta une una dirección web con una función
# que usa la lógica de ciclos.py y la base de datos de bd.py.

# ---------------------------------------------------------------
# IMPORTACIONES
# ---------------------------------------------------------------
import os                                        # para leer variables de entorno, como SECRET_KEY
from datetime import date                        # para trabajar con fechas
from dotenv import load_dotenv                   # carga en memoria los valores del archivo .env
from flask_cors import CORS                      # permite que una página web hable con este servidor
from flask import Flask, jsonify, request, session
# Flask: la app; jsonify: responder en JSON; request: leer lo que envía el cliente;
# session: guardar "quién ha entrado" (funciona como un diccionario)

# Nuestros módulos. Los usamos siempre con su nombre delante (bd.algo, ciclos.algo)
# para que se vea a simple vista de qué archivo viene cada función.
import bd                                        # todo lo que habla con la base de datos
import ciclos                                    # todos los cálculos y validaciones de fechas


# ---------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------
# static_folder: la carpeta con las páginas y archivos del frontend. Es una ruta relativa a
# la carpeta de app.py (backend), así que ".." sube a IZAR y entra en frontend.
# static_url_path="": las páginas se sirven sin prefijo (login.html queda en /login.html).
app = Flask(__name__, static_folder="../frontend", static_url_path="")

# La clave secreta sirve para firmar la cookie de sesión. Sin ella, cualquiera podría
# falsificarla. NO se escribe aquí: se lee del archivo .env, que no se sube a Git.
load_dotenv()                                    # lee backend/.env y deja sus valores disponibles
app.secret_key = os.environ["SECRET_KEY"]        # si falta SECRET_KEY en el .env, el servidor no arranca (a propósito)

# Más adelante, si el frontend se sirve desde otro sitio, habrá que ajustar CORS para que
# acepte cookies (supports_credentials=True y un origen concreto). Por ahora se deja así.
CORS(app)


# ---------------------------------------------------------------
# RUTA: GET /  ->  muestra la pantalla de inicio
# ---------------------------------------------------------------
@app.route("/")
def inicio():
    return app.send_static_file("index.html")    # devuelve frontend/index.html


# ---------------------------------------------------------------
# RUTA 1: POST /registro  ->  crea una cuenta nueva
# ---------------------------------------------------------------
# El cliente envía: {"usuario": "ana", "nombre": "Ana", "contrasena": "abc12345"}
@app.route("/registro", methods=["POST"])
def registro():
    datos = request.get_json()                   # lo que envió el cliente, convertido en diccionario
    try:
        usuario = datos["usuario"]
        contrasena = datos["contrasena"]
        nombre = datos["nombre"]
    except (KeyError, TypeError):                # KeyError: falta una clave; TypeError: no llegó un JSON válido
        return jsonify({"error": "Faltan datos"}), 400    # 400 = "la petición es incorrecta"

    if usuario == "" or nombre == "":            # campos vacíos
        return jsonify({"error": "Datos no válidos"}), 400
    if len(contrasena) < 8:                      # contraseña demasiado corta
        return jsonify({"error": "Contraseña muy corta"}), 400

    # crear_usuario guarda el hash de la contraseña (nunca la contraseña original)
    # y devuelve False si ese nombre de usuario ya existe.
    if not bd.crear_usuario(usuario, nombre, contrasena):
        return jsonify({"error": "Usuario ya existente"}), 409   # 409 = "conflicto: eso ya existe"

    return jsonify({"creado": True}), 201        # 201 = "creado"


# ---------------------------------------------------------------
# RUTA 2: POST /login  ->  comprueba usuario y contraseña, y abre la sesión
# ---------------------------------------------------------------
# El cliente envía: {"usuario": "ana", "contrasena": "abc12345"}
@app.route("/login", methods=["POST"])
def login():
    datos = request.get_json()
    try:
        usuario = datos["usuario"]
        contrasena = datos["contrasena"]
    except (KeyError, TypeError):
        return jsonify({"error": "Faltan datos"}), 400

    # iniciar_sesion compara la contraseña con el hash guardado.
    # El mensaje es el mismo si el usuario no existe o si la contraseña es incorrecta,
    # para que nadie pueda averiguar qué usuarios existen probando nombres.
    if not bd.iniciar_sesion(usuario, contrasena):
        return jsonify({"error": "Usuario o contraseña incorrectos"}), 401   # 401 = "no autorizado"

    # Todo correcto: guardamos quién ha entrado. Flask lo mete en una cookie firmada
    # con la SECRET_KEY, y el navegador la enviará en las siguientes peticiones.
    session["usuario"] = usuario
    return jsonify({"login": True})


# ---------------------------------------------------------------
# RUTA 3: POST /logout  ->  cierra la sesión
# ---------------------------------------------------------------
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()                              # borra todo lo que había guardado en la sesión
    return jsonify({"logout": True})


# ---------------------------------------------------------------
# RUTA 4: GET /dashboard  ->  carga los datos de la pantalla principal
# ---------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    # 1. SEGURIDAD: comprobamos que hay alguien con la sesión iniciada
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"error": "No autorizado. Inicia sesión primero"}), 401

    # 2. BASE DE DATOS: pedimos los periodos de esta usuaria (del más antiguo al más reciente)
    periodos = bd.obtener_periodos(usuario)

    # 3A. RESPUESTA PARA USUARIA NUEVA: sin periodos no hay nada que calcular
    if len(periodos) == 0:
        return jsonify({
            "estado": "nuevo",
            "dia_ciclo": 0,
            "dias_restantes": None,
            "periodo_abierto": False,            # sin periodos no puede haber ninguno abierto
            "mensaje": "Registra tu primer periodo"
        })

    # 3B. CÁLCULOS con las funciones de ciclos.py
    ultimo_periodo = periodos[-1]                        # el periodo más reciente
    fecha_inicio_ultimo = ultimo_periodo["inicio"]
    dia_actual = ciclos.calcular_dia_actual_ciclo(fecha_inicio_ultimo)
    fecha_proximo = ciclos.predecir_proximo_periodo(periodos)   # None si solo hay 1 periodo

    # Cuántos días faltan para la predicción (negativo si ya pasó: hay retraso)
    if fecha_proximo:
        dias_restantes = (fecha_proximo - date.today()).days
    else:
        dias_restantes = None                    # con 1 solo periodo no se puede hacer media

    # 4. RESPUESTA CON DATOS
    return jsonify({
        "estado": "ok",
        "dia_ciclo": dia_actual,
        "dias_restantes": dias_restantes,
        # Convertimos la fecha a texto (ISO) para que el JSON no dé error
        "fecha_proximo": fecha_proximo.isoformat() if fecha_proximo else None,
        # True si el último periodo no tiene fin todavía (la regla sigue en curso).
        # principal.js lo usa para saber si el botón tiene que registrar o terminar un periodo.
        "periodo_abierto": ultimo_periodo["fin"] is None,
        # Fecha de inicio del último periodo, como texto. La ventana del calendario
        # la enseña al terminar un periodo y no deja elegir un fin anterior a ella.
        "inicio_ultimo": fecha_inicio_ultimo.isoformat()
    })


# ---------------------------------------------------------------
# RUTA 5: POST /periodo  ->  registra un periodo nuevo (con o sin fin)
# ---------------------------------------------------------------
# El cliente envía:
#   {"fecha": "2026-11-04"}                          -> periodo en curso (sin fin)
#   {"fecha": "2026-10-01", "fin": "2026-10-06"}     -> periodo completo (por ejemplo, uno antiguo)
# Se permiten fechas pasadas (para registrar periodos antiguos), pero no futuras.
@app.route("/periodo", methods=["POST"])
def nuevo_periodo():
    # 1. SEGURIDAD: solo puede registrar quien tenga la sesión iniciada
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"error": "No autorizado. Inicia sesión antes"}), 401

    # 2. LEER DATOS: convertimos el texto "año-mes-día" en una fecha de verdad
    datos = request.get_json()
    try:
        fecha = date.fromisoformat(datos["fecha"])
        # El fin es OPCIONAL: .get() devuelve None si no viene (datos["fin"] daría KeyError)
        texto_fin = datos.get("fin")
        # Solo lo convertimos si ha llegado algo; si no, se queda en None
        fin = date.fromisoformat(texto_fin) if texto_fin else None
    except (KeyError, TypeError, ValueError, AttributeError):   # falta la clave, no hay JSON o la fecha no existe
        return jsonify({"error": "Faltan datos"}), 400

    # 3. VALIDAR con ciclos.py
    # Pedimos los periodos UNA sola vez: los usan las comprobaciones 3B y 3D
    periodos = bd.obtener_periodos(usuario)

    # 3A. El inicio no puede ser futuro
    if not ciclos.validar_inicio_nuevo_periodo(fecha):
        return jsonify({"error": "La fecha no puede ser futura"}), 400

    # 3B. El periodo nuevo no puede pisarse con uno guardado: tiene que empezar
    # a 15 días o más del inicio de todos los demás (antes o después)
    if not ciclos.solapamiento_ciclos(periodos, fecha):
        return jsonify({"error": "Ya hay un periodo registrado cerca de esa fecha"}), 400

    if fin is not None:
        # 3C. Si hay fin, también lo validamos (no futuro y después del inicio)
        if not ciclos.validar_fin_periodo(fin, fecha):
            return jsonify({"error": "La fecha de fin tiene que ir después del inicio y no ser futura"}), 400
    else:
        # 3D. Sin fin, el periodo queda abierto. Solo puede haber UNO abierto a la vez,
        # porque /periodo/fin cierra siempre el último.
        if len(periodos) > 0 and periodos[-1]["fin"] is None:
            return jsonify({"error": "Ya tienes un periodo en curso. Termínalo primero"}), 400

    # 4. GUARDAR. .isoformat() CON paréntesis convierte la fecha en el texto "2026-11-04" para SQLite.
    # Si no hay fin, pasamos None y la columna fin se queda vacía (periodo en curso).
    # guardar_periodo devuelve False si la usuaria no existe en la base de datos.
    texto_fin_bd = fin.isoformat() if fin is not None else None
    if not bd.guardar_periodo(usuario, fecha.isoformat(), texto_fin_bd):
        return jsonify({"error": "No se pudo guardar el periodo"}), 400

    # 5. RESPONDER: 201 = "creado"
    return jsonify({"guardado": True}), 201


# ---------------------------------------------------------------
# RUTA 6: POST /periodo/fin  ->  cierra el periodo que está abierto
# ---------------------------------------------------------------
# El cliente envía: {"fecha": "2026-11-09"}   (la fecha de FIN)
@app.route("/periodo/fin", methods=["POST"])
def fin_periodo():
    # 1. SEGURIDAD: solo puede registrar quien tenga la sesión iniciada
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"error": "No autorizado. Inicia sesión antes"}), 401

    # 2. LEER DATOS: get_json() CON paréntesis para obtener el diccionario
    datos = request.get_json()
    try:
        fecha = date.fromisoformat(datos["fecha"])     # texto "2026-11-09" -> fecha de verdad
    except (KeyError, ValueError, TypeError):          # falta la clave, no hay JSON o la fecha no existe
        return jsonify({"error": "Faltan datos"}), 400

    # 3. BUSCAR EL PERIODO ABIERTO
    periodos = bd.obtener_periodos(usuario)            # lista del más antiguo al más reciente
    # Si la lista está vacía, periodos[-1] daría error: lo comprobamos antes.
    # "or" basta con que se cumpla UNA: no hay periodos, o el último ya tiene fin.
    if len(periodos) == 0 or periodos[-1]["fin"] is not None:
        return jsonify({"error": "No hay ningún periodo abierto"}), 400
    inicio = periodos[-1]["inicio"]                    # fecha de inicio del periodo abierto

    # 4. VALIDAR con ciclos.py: el fin no puede ser futuro y tiene que ir después del inicio
    if not ciclos.validar_fin_periodo(fecha, inicio):
        return jsonify({"error": "Fecha de fin no válida"}), 400

    # 5. GUARDAR: bd.final_periodo hace el UPDATE y devuelve False si no cambió nada.
    # La función se ejecuta DENTRO del if, y el if mira su resultado.
    # .isoformat() pasa las dos fechas a texto, que es lo que guarda SQLite.
    if not bd.final_periodo(usuario, inicio.isoformat(), fecha.isoformat()):
        return jsonify({"error": "No se pudo guardar el fin"}), 400

    # 6. RESPONDER: 200 = "todo bien" (actualizamos un periodo, no creamos uno nuevo)
    return jsonify({"guardado": True}), 200


# ---------------------------------------------------------------
# ARRANQUE DEL SERVIDOR
# ---------------------------------------------------------------
if __name__ == "__main__":                       # solo se cumple si ejecutas ESTE archivo directamente
    # debug=True reinicia el servidor al guardar y enseña errores detallados.
    # Solo para desarrollo en tu ordenador: NUNCA al publicar la app.
    app.run(debug=True)
