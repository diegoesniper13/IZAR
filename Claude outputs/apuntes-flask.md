# Apuntes de Flask — explicado con IZAR

Guía de Flask usando ejemplos de tu propia app. Para repasar cuando quieras.

---

## 1. ¿Qué es Flask y qué pinta en tu app?

Flask es un **servidor web** escrito en Python. Su trabajo es: alguien (un navegador) pide algo por una dirección, y Flask responde.

En IZAR, el reparto de papeles es:

- **El navegador** (frontend: HTML, CSS, JS) → lo que ve la usuaria.
- **Flask** (`app.py`) → el que recibe las peticiones y responde.
- **`bd.py`** → habla con la base de datos.
- **`ciclos.py`** → hace los cálculos.

Flask está en medio: recibe la petición, pide ayuda a `bd.py` y `ciclos.py`, y devuelve la respuesta. Por eso en `app.py` casi no hay cálculos ni SQL: solo **coordina**.

```
Navegador  →  Flask (app.py)  →  bd.py / ciclos.py  →  base de datos
           ←                  ←
```

---

## 2. Crear la app

```python
from flask import Flask
app = Flask(__name__, static_folder="../frontend", static_url_path="")
```

- `app` es tu servidor. Todo cuelga de él.
- `static_folder="../frontend"` le dice: "los archivos del frontend están en la carpeta de al lado". Así Flask sirve solo tus `.html`, `.css` y `.js`.
- `__name__` es una variable de Python que vale el nombre del archivo. Flask la usa para saber dónde está.

---

## 3. Las rutas: el corazón de Flask

Una **ruta** une una **dirección** con una **función**. Cuando alguien entra en esa dirección, Flask ejecuta esa función.

```python
@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"logout": True})
```

Partes:

- **`@app.route("/logout", ...)`** → el decorador. La línea que empieza por `@` "engancha" la función de abajo a esa dirección. Si entras en `tuweb.com/logout`, se ejecuta `logout()`.
- **`methods=["POST"]`** → qué tipo de petición acepta. Hay dos principales:
  - **GET** = "dame información" (abrir una página, pedir datos). Es el de por defecto.
  - **POST** = "toma estos datos y haz algo" (crear una cuenta, guardar un periodo).
- **`def logout():`** → lo que se ejecuta.
- **`return ...`** → lo que Flask le devuelve al navegador.

**Regla práctica:** si la petición **cambia datos** (guardar, borrar, iniciar sesión), es POST. Si solo **lee**, es GET. En IZAR, `/dashboard` es GET (solo lee) y `/periodo` es POST (guarda).

---

## 4. Leer lo que envía el navegador: `request`

Cuando el navegador manda datos (por ejemplo, el usuario y la contraseña del login), llegan en formato **JSON**. Se leen con `request`:

```python
from flask import request

datos = request.get_json(silent=True)   # convierte el JSON en un diccionario de Python
usuario = datos["usuario"]
contrasena = datos["contrasena"]
```

- `request` es "la petición que acaba de llegar".
- `get_json()` convierte el JSON en un **diccionario**, así que luego lees los campos con `datos["loquesea"]`.
- `silent=True` → si no llega un JSON válido, devuelve `None` en vez de reventar.

**Por eso siempre va dentro de un `try`:** si falta un campo o no llega JSON, se controla el error en vez de que el servidor falle.

```python
try:
    usuario = datos["usuario"]
except (KeyError, TypeError):
    return jsonify({"error": "Faltan datos"}), 400
```

---

## 5. Responder: `jsonify` y los códigos de estado

Flask responde en JSON, para que el JavaScript lo entienda:

```python
return jsonify({"creado": True}), 201
```

Dos partes:

- **`jsonify({...})`** → convierte un diccionario de Python en JSON.
- **El número del final (201)** → el **código de estado**. Es un número que resume si fue bien o mal:

| Código | Significa | Cuándo en IZAR |
|---|---|---|
| **200** | Todo bien | Login correcto, borrar síntomas |
| **201** | Creado | Cuenta o periodo nuevo |
| **400** | Petición incorrecta | Faltan datos, fecha futura |
| **401** | No autorizado | No has iniciado sesión |
| **409** | Conflicto | Usuario que ya existe |

El navegador mira ese número para saber qué hacer. Por eso en el JS escribes `if (respuesta.ok)`: `ok` es true cuando el código es 2xx.

---

## 6. La sesión: recordar quién ha entrado

HTTP es "sin memoria": cada petición llega sola, el servidor no sabe quién eres. La **sesión** resuelve eso.

```python
from flask import session

# Al iniciar sesión, guardamos quién ha entrado:
session["usuario"] = usuario

# En cualquier otra ruta, comprobamos si hay alguien:
usuario = session.get("usuario")
if not usuario:
    return jsonify({"error": "No autorizado"}), 401
```

¿Cómo funciona por dentro?

1. Al hacer login, Flask guarda `usuario` en una **cookie** que le manda al navegador.
2. La cookie va **firmada** con la `SECRET_KEY`: nadie puede falsificarla sin esa clave.
3. En cada petición siguiente, el navegador manda la cookie, y Flask sabe quién eres.

Por eso la `SECRET_KEY` es tan importante y se guarda en el `.env`: es lo que impide que alguien se haga pasar por otra usuaria.

`session.clear()` borra la sesión (eso hace tu `/logout`).

---

## 7. La `SECRET_KEY` y el archivo `.env`

```python
from dotenv import load_dotenv
load_dotenv(...)                          # lee el archivo .env
app.secret_key = os.environ["SECRET_KEY"]  # coge la clave de ahí
```

- El `.env` guarda cosas secretas (la clave) o que cambian según el sitio (si es producción).
- **No se sube a GitHub** (está en `.gitignore`), así que la clave nunca se hace pública.
- `os.environ["SECRET_KEY"]` lee esa variable. Si falta, el programa falla a propósito: mejor que no arranque a que arranque sin protección.

---

## 8. Hooks: código que corre en cada petición

A veces quieres hacer algo **antes o después de todas las rutas**, sin repetirlo en cada una.

```python
@app.before_request          # ANTES de cada ruta
def antes_de_cada_peticion():
    return seguridad.comprobar_csrf()

@app.after_request           # DESPUÉS de cada ruta
def despues_de_cada_peticion(respuesta):
    return seguridad.poner_cabeceras(respuesta, PRODUCCION)
```

- **`before_request`** → se ejecuta antes de la ruta. Si devuelve algo, la ruta ni se ejecuta. Lo usas para la protección CSRF.
- **`after_request`** → se ejecuta después, y recibe la respuesta para modificarla. Lo usas para añadir las cabeceras de seguridad a todo.

Es como un portero (antes) y un revisor de salida (después) para toda la app.

---

## 9. Cómo encaja una ruta completa

Tu ruta de guardar un síntoma, paso a paso:

```python
@app.route("/sintoma", methods=["POST"])          # 1. dirección + tipo
def nuevo_sintoma():
    usuario = session.get("usuario")              # 2. ¿hay sesión?
    if not usuario:
        return jsonify({"error": "No autorizado..."}), 401

    datos = request.get_json(silent=True)         # 3. leer lo que llega
    try:
        fecha = date.fromisoformat(datos["fecha"])
        sintoma = datos["sintoma"]
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Faltan datos"}), 400

    if not ciclos.validar_sintoma(sintoma):       # 4. validar (ciclos.py)
        return jsonify({"error": "Ese síntoma no existe"}), 400

    if not bd.guardar_sintoma(usuario, ...):       # 5. guardar (bd.py)
        return jsonify({"error": "..."}), 409

    return jsonify({"guardado": True}), 201        # 6. responder
```

Fíjate en el patrón, que se repite en casi todas tus rutas:
**seguridad → leer → validar → actuar (bd) → responder.**

Flask coordina; el trabajo de verdad lo hacen `ciclos.py` (validar) y `bd.py` (guardar).

---

## 10. Arrancar el servidor

```python
if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=DEBUG)
```

- `if __name__ == "__main__":` → "ejecuta esto solo si lanzo este archivo directamente".
- `app.run(...)` → enciende el servidor.
- En tu ordenador usas esto. En PythonAnywhere NO: allí lo arranca el servidor de verdad con el archivo WSGI.

---

## Resumen en una frase

**Flask recibe peticiones en rutas, lee lo que llega con `request`, usa la sesión para saber quién eres, pide ayuda a otros módulos, y responde con `jsonify` y un código de estado.**
