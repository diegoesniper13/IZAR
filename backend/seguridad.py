# seguridad.py
# Todas las protecciones de la app en un solo sitio, para que app.py siga limpio:
#   - registro de actividad sospechosa (archivo seguridad.log)
#   - límite de intentos de inicio de sesión y de registro (contra ataques de fuerza bruta)
#   - protección CSRF (que otra web no pueda hacer peticiones en nombre de la usuaria)
#   - cabeceras de seguridad (contra XSS, clickjacking, etc.)
#   - comprobación de los textos que envía el cliente

import logging                                   # para escribir avisos en un archivo
import os
import re                                        # expresiones regulares: para comprobar formatos de texto
import time                                      # para medir los minutos de bloqueo
from logging.handlers import RotatingFileHandler # archivo de log que no crece sin límite
from urllib.parse import urlparse                # para leer el dominio de una URL

from flask import jsonify, request


# ---------------------------------------------------------------
# 1. REGISTRO DE ACTIVIDAD SOSPECHOSA
# ---------------------------------------------------------------
# Guarda en backend/seguridad.log cosas como inicios de sesión fallidos o bloqueos.
# NUNCA se guardan contraseñas: solo el usuario, la IP y qué ha pasado.
# RotatingFileHandler: cuando el archivo llega a 1 MB empieza otro (guarda 3 antiguos).
RUTA_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seguridad.log")

registro = logging.getLogger("izar.seguridad")
registro.setLevel(logging.INFO)
if not registro.handlers:                        # evita añadirlo dos veces si Flask recarga el módulo
    manejador = RotatingFileHandler(RUTA_LOG, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    manejador.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    registro.addHandler(manejador)


def ip_cliente() -> str:
    # La IP de quien hace la petición (en producción, detrás de un proxy, la corrige ProxyFix)
    return request.remote_addr or "desconocida"


def avisar(mensaje: str):
    # Escribe un aviso en seguridad.log con la IP delante
    registro.warning(f"[{ip_cliente()}] {mensaje}")


# ---------------------------------------------------------------
# 2. LÍMITE DE INTENTOS (contra fuerza bruta)
# ---------------------------------------------------------------
# Si alguien falla la contraseña muchas veces seguidas, se le bloquea un rato.
# Se guarda en memoria: si se reinicia el servidor, los contadores se vacían.
# Es suficiente para una app pequeña; una app grande usaría Redis o similar.
#
# intentos = { "login:192.168.1.5:ana": [hora1, hora2, ...], ... }
_intentos = {}

def _limpiar_antiguos(clave: str, ventana_segundos: int) -> list:
    # Se queda solo con los intentos que están dentro de la ventana de tiempo
    ahora = time.time()
    recientes = [t for t in _intentos.get(clave, []) if ahora - t < ventana_segundos]
    _intentos[clave] = recientes
    return recientes


def esta_bloqueado(clave: str, maximo: int, ventana_segundos: int) -> bool:
    # True si esa clave ya ha llegado al máximo de intentos dentro de la ventana
    return len(_limpiar_antiguos(clave, ventana_segundos)) >= maximo


def apuntar_intento(clave: str):
    # Suma un intento (por ejemplo, un login fallido)
    _intentos.setdefault(clave, []).append(time.time())


def borrar_intentos(clave: str):
    # Cuando el login sale bien, se olvidan los fallos anteriores
    _intentos.pop(clave, None)


# Límites que usa app.py
LOGIN_MAX_FALLOS = 5            # 5 contraseñas mal...
LOGIN_VENTANA = 15 * 60         # ...en 15 minutos -> bloqueo durante esos 15 minutos
REGISTRO_MAX = 10               # 10 cuentas nuevas...
REGISTRO_VENTANA = 60 * 60      # ...por hora desde la misma IP


# ---------------------------------------------------------------
# 3. PROTECCIÓN CSRF
# ---------------------------------------------------------------
# CSRF: una web maliciosa intenta que tu navegador haga una petición a IZAR
# (por ejemplo, registrar un periodo) aprovechando que tienes la sesión abierta.
# Nos protegemos de tres formas a la vez:
#   a) la cookie de sesión es SameSite=Lax (en app.py): el navegador no la manda
#      en peticiones POST que vengan de otras webs;
#   b) solo aceptamos POST con JSON: un formulario HTML de otra web no puede enviar JSON;
#   c) si el navegador indica de qué web viene la petición (cabecera Origin),
#      tiene que ser la nuestra.
def comprobar_csrf():
    # Solo afecta a las peticiones que cambian datos
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return None

    # b) Tiene que ser JSON
    if not request.is_json:
        avisar(f"CSRF: petición {request.method} {request.path} sin JSON")
        return jsonify({"error": "Formato no válido"}), 415     # 415 = "tipo de contenido no admitido"

    # c) Si hay cabecera Origin, su dominio tiene que ser el nuestro
    origen = request.headers.get("Origin")
    if origen is not None:
        dominio_origen = urlparse(origen).netloc
        if dominio_origen != request.host:
            avisar(f"CSRF: origen ajeno {origen} en {request.path}")
            return jsonify({"error": "Origen no permitido"}), 403   # 403 = "prohibido"

    return None                                  # todo bien: la petición sigue su camino


# ---------------------------------------------------------------
# 4. CABECERAS DE SEGURIDAD
# ---------------------------------------------------------------
# Se añaden a TODAS las respuestas. Le dicen al navegador cómo protegerse.
#
# Content-Security-Policy (CSP): de dónde puede cargar cosas la página.
#   - scripts y todo lo demás: solo de nuestro propio servidor ('self')
#   - estilos: los nuestros y la hoja de Google Fonts (la importa styles.css)
#   - fuentes: las de Google Fonts
#   Así, aunque alguien consiguiera colar un <script> en la página (XSS), el navegador no lo ejecutaría.
CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)

def poner_cabeceras(respuesta, produccion: bool):
    respuesta.headers["Content-Security-Policy"] = CSP
    respuesta.headers["X-Content-Type-Options"] = "nosniff"        # no "adivinar" el tipo de archivo
    respuesta.headers["X-Frame-Options"] = "DENY"                  # nadie puede meter IZAR dentro de un iframe
    respuesta.headers["Referrer-Policy"] = "same-origin"           # no contar a otras webs de dónde vienes
    respuesta.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    # Las respuestas de la API (JSON) tienen datos personales: que nadie las guarde en caché
    if respuesta.mimetype == "application/json":
        respuesta.headers["Cache-Control"] = "no-store"

    # HSTS: "a partir de ahora, entra siempre por HTTPS". Solo en producción, que es
    # donde hay HTTPS (en tu ordenador, con http://127.0.0.1, no tendría sentido).
    if produccion:
        respuesta.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return respuesta


# ---------------------------------------------------------------
# 5. COMPROBACIÓN DE TEXTOS
# ---------------------------------------------------------------
# Nombre de usuario: de 3 a 30 letras, números, punto, guion o guion bajo.
# Evita nombres raros, enormes o con caracteres extraños.
FORMATO_USUARIO = re.compile(r"[A-Za-z0-9._-]{3,30}")

def es_texto(valor, minimo: int, maximo: int) -> bool:
    # True si es un texto (str) con una longitud entre minimo y maximo
    return isinstance(valor, str) and minimo <= len(valor) <= maximo


def usuario_valido(usuario) -> bool:
    return isinstance(usuario, str) and FORMATO_USUARIO.fullmatch(usuario) is not None
