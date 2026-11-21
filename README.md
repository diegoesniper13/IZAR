# IZAR ⭐

Aplicación web para registrar el ciclo menstrual, anticipar el próximo periodo (incluida la ovulación y los días fértiles) y conocer los síntomas que suelen repetirse en cada momento del ciclo.

🌐 **Pruébala en: [izar.pythonanywhere.com](https://izar.pythonanywhere.com)**

> Proyecto personal hecho mientras aprendo Python, Flask, SQL y desarrollo web.

## Funcionalidades

- **Cuentas de usuario**: registro e inicio de sesión. Las contraseñas se guardan cifradas (hash), nunca tal cual. Al registrarse hay que aceptar los **términos y condiciones** y la **política de privacidad**.
- **Pantalla de registro**:
  - el día del ciclo en el que estás;
  - cuántos días faltan para el próximo periodo, o si hay retraso;
  - la tira semanal con el día de hoy marcado;
  - registro rápido de síntomas con un clic, eligiendo también su intensidad o variante (cólicos: intenso/suave; flujo: mucho/normal/poco; ánimo: feliz/enfadada/triste; sueño: mucho/poco);
  - botón para borrar los síntomas registrados hoy.
- **Registro de periodos con calendario**:
  - periodos completos (inicio y fin), también antiguos, para empezar con historial;
  - periodos en curso: se guarda el inicio y se termina más tarde.
- **Pantalla de estadísticas**:
  - tus 5 últimos periodos con su duración;
  - los síntomas que es posible que tengas hoy, según los que registraste en tus ciclos anteriores.
- **Calendario**:
  - vista mensual con flechas para cambiar de mes;
  - pinta los días de regla ya registrada, la regla prevista, la ovulación y la ventana de días fértiles.
- **Pantalla de ajustes**:
  - ver el usuario de la cuenta;
  - cambiar la contraseña;
  - cerrar sesión;
  - eliminar la cuenta y todos sus datos (periodos y síntomas incluidos).
- **Validaciones**:
  - no se aceptan fechas futuras;
  - el fin tiene que ir después del inicio;
  - no se puede registrar un periodo que se solape con otro ya guardado;
  - el mismo síntoma no se puede registrar dos veces el mismo día;
  - la intensidad de un síntoma tiene que ser una de las válidas para ese síntoma en concreto;
  - la contraseña nueva no puede ser igual a la actual.

### Cómo se predicen los síntomas

Cada síntoma se guarda con su fecha e intensidad. Para comparar ciclos, la app traduce la fecha a **día del ciclo** (día 1 = el día que empieza la regla). Después mira, en los ciclos ya terminados, si ese síntoma apareció cerca del día de hoy (un día antes o después). Si pasó en al menos la mitad de los ciclos, lo muestra como posible. (La intensidad, de momento, solo se guarda y se muestra: no influye todavía en esta predicción.)

### Cómo se calcula la ovulación y la ventana fértil

La ovulación no se calcula hacia delante desde que acaba la regla (esa primera mitad del ciclo varía mucho de una persona a otra), sino **hacia atrás desde la próxima regla prevista**: la segunda mitad del ciclo, de la ovulación a la siguiente regla, es mucho más estable (~14 días). La ventana fértil son los días alrededor de esa fecha, antes y después.

## Seguridad

- Cookies de sesión `HttpOnly` y `SameSite`, con caducidad (y `Secure` en producción).
- Protección CSRF: solo se aceptan peticiones JSON desde la propia web.
- Cabeceras de seguridad, incluida una política CSP contra XSS.
- Límite de intentos de inicio de sesión contra ataques de fuerza bruta.
- Consultas SQL parametrizadas.
- HTTPS obligatorio en producción y modo debug apagado.
- Registro de actividad sospechosa en `backend/seguridad.log` (sin contraseñas).

## Tecnologías

| Parte | Tecnología |
|---|---|
| Backend | Python 3 + Flask |
| Base de datos | SQLite |
| Frontend | HTML, CSS y JavaScript |
| Hosting | PythonAnywhere |

## Estructura del proyecto

```
IZAR/
├── backend/
│   ├── app.py            # servidor Flask: las rutas de la API
│   ├── bd.py             # todo lo que habla con la base de datos
│   ├── ciclos.py         # cálculos del ciclo, predicciones y validaciones
│   ├── seguridad.py      # protecciones: CSRF, cabeceras, límite de intentos, log
│   ├── requirements.txt  # librerías de Python necesarias
│   └── .env.example      # plantilla para crear el .env
├── database/
│   ├── schema.sql        # crea las tablas usuarios, periodos y sintomas
│   └── seed.sql          # datos de prueba (opcional)
└── frontend/
    ├── index.html        # pantalla de bienvenida
    ├── login.html        # iniciar sesión
    ├── registro.html     # crear cuenta (con casilla de términos y privacidad)
    ├── principal.html    # pantalla de registro (ciclo, periodos y síntomas)
    ├── estadisticas.html # últimos periodos y síntomas posibles
    ├── calendario.html   # calendario mensual con predicción
    ├── ajustes.html      # cuenta: contraseña, cerrar sesión, eliminar cuenta
    ├── terminos.html      # términos y condiciones
    ├── privacidad.html    # política de privacidad
    ├── css/styles.css
    └── js/  # login.js, registro.js, principal.js, estadisticas.js, calendario.js, ajustes.js
```

## Cómo ejecutarlo en tu ordenador

**1. Clona el repositorio**

```bash
git clone https://github.com/diegoesniper13/IZAR.git
cd IZAR
```

**2. Crea un entorno virtual e instala las dependencias**

```bash
python3 -m venv venv
source venv/bin/activate          # en Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

**3. Crea el archivo `backend/.env`**

Copia la plantilla y rellénala. El `.env` no se sube a GitHub: cada persona crea el suyo.

```bash
cp backend/.env.example backend/.env
```

Dentro tiene que haber:

- `SECRET_KEY`: una clave aleatoria de al menos 32 caracteres. Puedes generarla con `python3 -c "import secrets; print(secrets.token_hex(32))"`.
- `FLASK_DEBUG=1`: solo en tu ordenador, para que el servidor se recargue al guardar.
- **No** pongas `ENTORNO=produccion` en tu ordenador: obliga a usar HTTPS y la web no cargaría en `http://127.0.0.1`.

**4. Crea la base de datos**

La base de datos tampoco se sube a GitHub. Para crearla vacía con sus tablas:

```bash
python3 -c "import sqlite3; c = sqlite3.connect('backend/regla.db'); c.executescript(open('database/schema.sql').read())"
```

**5. Arranca el servidor**

```bash
cd backend
python3 app.py
```

Abre **http://127.0.0.1:5000** en el navegador, crea una cuenta y empieza a registrar periodos.

## Publicarla (PythonAnywhere)

La versión pública funciona en PythonAnywhere. El `.env` del servidor lleva su propia `SECRET_KEY` (distinta de la de tu ordenador) y `ENTORNO=produccion`.

Para actualizarla después de hacer cambios:

1. En tu ordenador: `git push`.
2. En la consola Bash de PythonAnywhere: `cd ~/IZAR` y `git pull`.
3. Si has cambiado algo de la base de datos (una tabla o columna nueva), aplícalo también ahí con `sqlite3 ~/IZAR/backend/regla.db` antes de recargar.
4. En la pestaña **Web**: botón **Reload**.

Con la cuenta gratuita hay que renovar la web una vez al mes (pestaña **Web** → **Run until 1 month from today**).

## API

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/registro` | Crea una cuenta (exige haber aceptado los términos) |
| `POST` | `/login` | Inicia sesión |
| `POST` | `/logout` | Cierra sesión |
| `GET` | `/dashboard` | Datos de las pantallas: usuario, día del ciclo, predicción, últimos periodos y síntomas posibles |
| `POST` | `/periodo` | Registra un periodo, con o sin fecha de fin |
| `POST` | `/periodo/fin` | Pone la fecha de fin al periodo en curso |
| `POST` | `/sintoma` | Guarda un síntoma de un día, con su intensidad |
| `POST` | `/sintoma/borrar` | Borra todos los síntomas registrados hoy |
| `GET` | `/calendario` | Últimos 2 periodos y predicción (regla, ovulación, ventana fértil) para el calendario |
| `POST` | `/cuenta/contrasena` | Cambia la contraseña de la cuenta |
| `POST` | `/cuenta/borrar` | Elimina la cuenta y todos sus datos |

## Próximos pasos

- [x] Registro rápido de síntomas, con intensidad
- [x] Estadísticas: últimos periodos y síntomas posibles
- [x] Publicar la web
- [x] Botón para borrar los síntomas de hoy
- [x] Política de privacidad y consentimiento en el registro
- [x] Cambiar contraseña y eliminar la cuenta
- [x] Calendario con regla prevista, ovulación y ventana fértil
- [ ] Que la intensidad de los síntomas influya también en la predicción
- [ ] Direcciones sin `.html` (por ejemplo, `/principal`)
- [ ] Que la predicción ignore los meses sin registrar
- [ ] Versión instalable (PWA) y app para Android (APK)

## Aviso

IZAR es un proyecto de aprendizaje. Sus predicciones son una estimación a partir de tus ciclos anteriores y **no sustituyen el consejo médico**.
