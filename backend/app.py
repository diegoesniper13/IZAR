# app.py
# Servidor Flask de la app. Cada ruta une una dirección web con una función
# que usa la lógica de ciclos.py y la base de datos de bd.py.

import os                                        # para leer variables de entorno, como SECRET_KEY
from dotenv import load_dotenv                   # carga en memoria los valores del archivo .env
from flask_cors import CORS                      # permite que una página web hable con este servidor
from flask import Flask, jsonify, request, session
# Flask: la app; jsonify: responder en JSON; request: leer lo que envía el cliente;
# session: guardar "quién ha entrado" (funciona como un diccionario)

# Importamos los módulos completos para poder usarlos en el dashboard
import bd 
import ciclos

# Importamos funciones específicas de la base de datos por comodidad en otras rutas
from bd import obtener_periodos, guardar_periodo, crear_usuario, iniciar_sesion   
from ciclos import predecir_proximo_periodo      
from datetime import date                        # para comprobar que los textos son fechas válidas

# static_folder: la carpeta con las páginas y archivos del frontend. Es una ruta relativa a
#la carpeta de app.py (backend), así que ".." sube a IZAR y entra en frontend.
# static_url_path="": las páginas se sirven sin prefijo (login.html queda en /login.html).
app = Flask(__name__, static_folder="../frontend", static_url_path="")
# La clave secreta sirve para firmar la cookie de sesión. Sin ella, cualquiera podría
# falsificarla. NO se escribe aquí: se lee del archivo .env, que no se sube a Git.
load_dotenv()                                    # lee backend/.env y deja sus valores disponibles
app.secret_key = os.environ["SECRET_KEY"]        # si falta SECRET_KEY en el .env, el servidor no arranca (a propósito)

# Más adelante, al conectar el frontend, habrá que ajustar CORS para que acepte cookies
# (supports_credentials=True y un origen concreto). Por ahora se deja así.
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
        return jsonify({"error": "Datos no validos"}), 400
    if len(contrasena) < 8:                      # contraseña demasiado corta
        return jsonify({"error": "Contraseña muy corta"}), 400

    # crear_usuario guarda el hash de la contraseña (nunca la contraseña original)
    # y devuelve False si ese nombre de usuario ya existe.
    if not crear_usuario(usuario, nombre, contrasena):
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
    if not iniciar_sesion(usuario, contrasena):
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
# RUTA 4: GET /dashboard  ->  Carga los datos de la pantalla principal
# ---------------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    # 1. SEGURIDAD: Identificamos si hay un usuario en la sesión
    usuario_id = session.get("usuario")
    
    if not usuario_id:
        return jsonify({"error": "No autorizado. Inicia sesión primero."}), 401

    # 2. BASE DE DATOS: Pedimos los periodos de este usuario concreto
    periodos = bd.obtener_periodos(usuario_id)

    # 3. LÓGICA Y MATEMÁTICAS
    if periodos and len(periodos) > 0:
        # Extraemos la fecha de inicio del último periodo registrado
        ultimo_periodo = periodos[-1]
        fecha_inicio_ultimo = ultimo_periodo["inicio"]

        # Llamamos a tus funciones de ciclos.py
        dia_actual = ciclos.calcular_dia_actual_ciclo(fecha_inicio_ultimo)
        fecha_proximo = ciclos.predecir_proximo_periodo(periodos)

        # Calculamos cuántos días faltan para la predicción
        if fecha_proximo:
            dias_restantes = (fecha_proximo - date.today()).days
        else:
            dias_restantes = None # Pasa si solo tiene 1 periodo registrado y no se puede hacer media

        # 4. RESPUESTA CON DATOS
        return jsonify({
            "estado": "ok",
            "dia_ciclo": dia_actual,
            "dias_restantes": dias_restantes,
            # Convertimos la fecha a texto (ISO) para que el JSON no dé error
            "fecha_proximo": fecha_proximo.isoformat() if fecha_proximo else None 
        })

    else:
        # 4B. RESPUESTA PARA USUARIO NUEVO
        # Si la lista de periodos está vacía, enviamos datos a 0
        return jsonify({
            "estado": "nuevo",
            "dia_ciclo": 0,
            "dias_restantes": None,
            "mensaje": "Registra tu primer periodo"
        })

# ---------------------------------------------------------------
# ARRANQUE DEL SERVIDOR
# ---------------------------------------------------------------
if __name__ == "__main__":                       # solo se cumple si ejecutas ESTE archivo directamente
    # debug=True reinicia el servidor al guardar y enseña errores detallados.
    # Solo para desarrollo en tu ordenador: NUNCA al publicar la app.
    app.run(debug=True)