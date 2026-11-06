# app.py
# Servidor Flask de la app. Cada ruta une una dirección web con una función
# que usa la lógica de ciclos.py y la base de datos de bd.py.

# ---------------------------------------------------------------
# IMPORTACIONES
# ---------------------------------------------------------------
import os                                        # para leer variables de entorno, como SECRET_KEY
from datetime import date, timedelta             # para trabajar con fechas (y la duración de la sesión)
from dotenv import load_dotenv                   # carga en memoria los valores del archivo .env
from flask import Flask, jsonify, request, session, redirect
from werkzeug.middleware.proxy_fix import ProxyFix   # para saber si llegó por HTTPS detrás de un proxy
# Flask: la app; jsonify: responder en JSON; request: leer lo que envía el cliente;
# session: guardar "quién ha entrado" (funciona como un diccionario)

# Nuestros módulos. Los usamos siempre con su nombre delante (bd.algo, ciclos.algo)
# para que se vea a simple vista de qué archivo viene cada función.
import bd                                        # todo lo que habla con la base de datos
import ciclos                                    # todos los cálculos y validaciones de fechas
import seguridad                                 # protecciones: CSRF, cabeceras, límites de intentos, log


# ---------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------
# static_folder: la carpeta con las páginas y archivos del frontend. Es una ruta relativa a
# la carpeta de app.py (backend), así que ".." sube a IZAR y entra en frontend.
# static_url_path="": las páginas se sirven sin prefijo (login.html queda en /login.html).
app = Flask(__name__, static_folder="../frontend", static_url_path="")

# La clave secreta sirve para firmar la cookie de sesión. Sin ella, cualquiera podría
# falsificarla. NO se escribe aquí: se lee del archivo .env, que no se sube a Git.
# load_dotenv busca el .env junto a app.py, arranques el servidor desde donde lo arranques.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
app.secret_key = os.environ["SECRET_KEY"]        # si falta SECRET_KEY en el .env, el servidor no arranca (a propósito)

# Una clave corta se podría adivinar probando: exigimos al menos 32 caracteres.
if len(app.secret_key) < 32:
    raise RuntimeError("SECRET_KEY es demasiado corta: usa al menos 32 caracteres aleatorios")

# ENTORNO=produccion en el .env del servidor de verdad. En tu ordenador no hace falta ponerlo.
PRODUCCION = os.environ.get("ENTORNO") == "produccion"

# Modo debug: SOLO si lo pides con FLASK_DEBUG=1 en el .env, y NUNCA en producción
# (el modo debug enseña el código y deja ejecutar Python desde el navegador si hay un error).
DEBUG = os.environ.get("FLASK_DEBUG") == "1" and not PRODUCCION

# --- Cookie de sesión segura ---
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,      # JavaScript no puede leer la cookie (aunque hubiera XSS)
    SESSION_COOKIE_SAMESITE="Lax",     # el navegador no la manda en POST que vengan de otras webs (CSRF)
    SESSION_COOKIE_SECURE=PRODUCCION,  # en producción, la cookie solo viaja por HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),   # la sesión caduca a los 7 días
    MAX_CONTENT_LENGTH=16 * 1024,      # peticiones de 16 KB como mucho (nuestros JSON ocupan muy poco)
)

# En producción la app estará detrás de un servidor (Nginx, etc.) que hace el HTTPS.
# ProxyFix lee las cabeceras que ese servidor añade para saber la IP real y si llegó por HTTPS.
if PRODUCCION:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# CORS: NO lo activamos. El frontend lo sirve este mismo servidor, así que no hace falta,
# y sin CORS ninguna otra web puede leer las respuestas de nuestra API.


# ---------------------------------------------------------------
# PROTECCIONES QUE SE APLICAN A TODAS LAS PETICIONES
# ---------------------------------------------------------------
# before_request: se ejecuta ANTES de cada ruta. Si devuelve algo, la ruta no llega a ejecutarse.
@app.before_request
def antes_de_cada_peticion():
    # 1. Forzar HTTPS en producción: si alguien entra por http://, lo mandamos a https://
    if PRODUCCION and not request.is_secure:
        return redirect(request.url.replace("http://", "https://", 1), code=301)

    # 2. Protección CSRF (ver seguridad.py)
    return seguridad.comprobar_csrf()


# after_request: se ejecuta DESPUÉS de cada ruta, justo antes de enviar la respuesta
@app.after_request
def despues_de_cada_peticion(respuesta):
    return seguridad.poner_cabeceras(respuesta, PRODUCCION)


# Errores en JSON, para que el JavaScript pueda leerlos y no se vea una página de error
@app.errorhandler(413)
def demasiado_grande(error):
    seguridad.avisar(f"Petición demasiado grande en {request.path}")
    return jsonify({"error": "Petición demasiado grande"}), 413


@app.errorhandler(404)
def no_encontrado(error):
    return jsonify({"error": "No encontrado"}), 404


@app.errorhandler(500)
def error_interno(error):
    # Al usuario no le enseñamos detalles (podrían dar pistas a un atacante); quedan en la terminal
    return jsonify({"error": "Error interno del servidor"}), 500


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
    # Límite: como mucho 10 cuentas nuevas por hora desde la misma IP (evita crear cuentas en masa)
    clave_limite = f"registro:{seguridad.ip_cliente()}"
    if seguridad.esta_bloqueado(clave_limite, seguridad.REGISTRO_MAX, seguridad.REGISTRO_VENTANA):
        seguridad.avisar("Registro bloqueado: demasiadas cuentas nuevas desde esta IP")
        return jsonify({"error": "Demasiados intentos. Prueba más tarde"}), 429   # 429 = "demasiadas peticiones"

    datos = request.get_json(silent=True)        # silent=True: si no es JSON válido, da None (no un error)
    try:
        usuario = datos["usuario"]
        contrasena = datos["contrasena"]
        nombre = datos["nombre"]
    except (KeyError, TypeError):                # KeyError: falta una clave; TypeError: no llegó un JSON válido
        return jsonify({"error": "Faltan datos"}), 400    # 400 = "la petición es incorrecta"

    # Comprobamos tipo y tamaño de cada dato (que sean textos y no demasiado largos)
    if not seguridad.usuario_valido(usuario):
        return jsonify({"error": "El usuario debe tener de 3 a 30 letras, números, puntos o guiones"}), 400
    if not seguridad.es_texto(nombre, 1, 50):
        return jsonify({"error": "Datos no válidos"}), 400
    if not seguridad.es_texto(contrasena, 8, 128):    # mínimo 8; máximo 128 para no gastar CPU con textos enormes
        return jsonify({"error": "La contraseña debe tener entre 8 y 128 caracteres"}), 400

    seguridad.apuntar_intento(clave_limite)      # cuenta para el límite de registros

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
    datos = request.get_json(silent=True)
    try:
        usuario = datos["usuario"]
        contrasena = datos["contrasena"]
    except (KeyError, TypeError):
        return jsonify({"error": "Faltan datos"}), 400

    # Tienen que ser textos de tamaño razonable
    if not seguridad.es_texto(usuario, 1, 30) or not seguridad.es_texto(contrasena, 1, 128):
        return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

    # Límite contra fuerza bruta: 5 fallos en 15 minutos para ese usuario desde esa IP -> bloqueo
    clave_limite = f"login:{seguridad.ip_cliente()}:{usuario}"
    if seguridad.esta_bloqueado(clave_limite, seguridad.LOGIN_MAX_FALLOS, seguridad.LOGIN_VENTANA):
        seguridad.avisar(f"Login bloqueado por demasiados fallos (usuario: {usuario})")
        return jsonify({"error": "Demasiados intentos fallidos. Espera 15 minutos"}), 429

    # iniciar_sesion compara la contraseña con el hash guardado.
    # El mensaje es el mismo si el usuario no existe o si la contraseña es incorrecta,
    # para que nadie pueda averiguar qué usuarios existen probando nombres.
    if not bd.iniciar_sesion(usuario, contrasena):
        seguridad.apuntar_intento(clave_limite)
        seguridad.avisar(f"Login fallido (usuario: {usuario})")      # nunca se guarda la contraseña
        return jsonify({"error": "Usuario o contraseña incorrectos"}), 401   # 401 = "no autorizado"

    # Todo correcto. Primero vaciamos la sesión anterior: así nadie puede "colar" una sesión
    # preparada de antemano (ataque de fijación de sesión).
    seguridad.borrar_intentos(clave_limite)
    session.clear()
    session["usuario"] = usuario
    session.permanent = True                     # usa la duración de PERMANENT_SESSION_LIFETIME (7 días)
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
            "mensaje": "Registra tu primer periodo",
            "sintomas_posibles": []              # sin periodos no hay síntomas que prever
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

    # Síntomas que suele tener por estas fechas, según sus ciclos anteriores (función 5F).
    # Devuelve una lista de nombres como ["colicos", "sueno"], o [] si aún no hay datos.
    sintomas = bd.obtener_sintomas(usuario)
    sintomas_posibles = ciclos.calcular_sintomas_posibles(dia_actual, periodos, sintomas)

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
        "inicio_ultimo": fecha_inicio_ultimo.isoformat(),
        # Ya es una lista de textos: el JSON la acepta tal cual (estadisticas.js la enseña)
        "sintomas_posibles": sintomas_posibles
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
    datos = request.get_json(silent=True)
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
    datos = request.get_json(silent=True)
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
# RUTA 7: POST /sintoma  ->  guarda un síntoma de un día
# ---------------------------------------------------------------
# El cliente envía: {"fecha": "2026-11-05", "sintoma": "colicos"}
# Un síntoma por petición. Si un día hay varios, se envía una petición por cada uno.
@app.route("/sintoma", methods=["POST"])
def nuevo_sintoma():
    # 1. SEGURIDAD: la usuaria SIEMPRE sale de la sesión, nunca del JSON.
    # Si la leyéramos del JSON, cualquiera podría guardar síntomas en la cuenta de otra.
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"error": "No autorizado. Inicia sesión antes"}), 401

    # 2. LEER DATOS: los dos son obligatorios, por eso usamos corchetes y no .get()
    # (si falta alguno salta KeyError y respondemos "Faltan datos")
    datos = request.get_json(silent=True)
    try:
        fecha = date.fromisoformat(datos["fecha"])     # texto "2026-11-05" -> fecha de verdad
        sintoma = datos["sintoma"]                     # por ejemplo "colicos"
    except (KeyError, TypeError, ValueError):          # falta una clave, no hay JSON o la fecha no existe
        return jsonify({"error": "Faltan datos"}), 400

    # 3. VALIDAR con ciclos.py
    # 3A. La fecha no puede ser futura (reutilizamos la validación del inicio de periodo)
    if not ciclos.validar_inicio_nuevo_periodo(fecha):
        return jsonify({"error": "La fecha no puede ser futura"}), 400

    # 3B. El síntoma tiene que ser uno de los que existen en la app
    if not ciclos.validar_sintoma(sintoma):
        return jsonify({"error": "Ese síntoma no existe"}), 400

    # 4. GUARDAR. La fecha va como texto con .isoformat(), igual que en los periodos.
    # guardar_sintoma devuelve False si ese síntoma ya estaba guardado ese día.
    # (Que la usuaria no exista no puede pasar aquí: viene de una sesión válida.)
    if not bd.guardar_sintoma(usuario, fecha.isoformat(), sintoma):
        return jsonify({"error": "Ya registraste ese síntoma ese día"}), 409   # 409 = "conflicto: eso ya existe"

    # 5. RESPONDER: 201 = "creado"
    return jsonify({"guardado": True}), 201



# ---------------------------------------------------------------
# ARRANQUE DEL SERVIDOR
# ---------------------------------------------------------------
if __name__ == "__main__":                       # solo se cumple si ejecutas ESTE archivo directamente
    # El modo debug depende de FLASK_DEBUG en el .env (ver CONFIGURACIÓN): apagado por defecto.
    # host="127.0.0.1": solo se puede entrar desde tu propio ordenador, no desde otros de tu red.
    # En producción NO se usa app.run: se arranca con un servidor de verdad (gunicorn, waitress...).
    app.run(host="127.0.0.1", debug=DEBUG)
