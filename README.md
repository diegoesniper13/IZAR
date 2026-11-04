# IZAR ⭐

Aplicación web para registrar el ciclo menstrual y anticipar el próximo periodo.

IZAR guarda las fechas de inicio y fin de cada periodo y, con ellas, calcula en qué día del ciclo estás y cuántos días faltan para el siguiente.

> 🚧 Proyecto en desarrollo. Lo estoy construyendo mientras aprendo Python, Flask, SQL y desarrollo web.

## Funcionalidades

- **Cuentas de usuario**: registro e inicio de sesión. Las contraseñas se guardan cifradas (hash), nunca tal cual.
- **Pantalla principal**:
  - el día del ciclo en el que estás;
  - cuántos días faltan para el próximo periodo, o si hay retraso;
  - la tira semanal con el día de hoy marcado.
- **Registro de periodos con calendario**:
  - periodos completos (inicio y fin), también antiguos, para empezar con historial;
  - periodos en curso: se guarda el inicio y se termina más tarde.
- **Validaciones**:
  - no se aceptan fechas futuras;
  - el fin tiene que ir después del inicio;
  - no se puede registrar un periodo que se solape con otro ya guardado.

## Tecnologías

| Parte | Tecnología |
|---|---|
| Backend | Python 3 + Flask |
| Base de datos | SQLite |
| Frontend | HTML, CSS y JavaScript |

## Estructura del proyecto

```
IZAR/
├── backend/
│   ├── app.py            # servidor Flask: las rutas de la API
│   ├── bd.py             # todo lo que habla con la base de datos
│   ├── ciclos.py         # cálculos del ciclo y validaciones de fechas
│   └── requirements.txt  # librerías de Python necesarias
├── database/
│   ├── schema.sql        # crea las tablas usuarios y periodos
│   └── seed.sql          # datos de prueba (opcional)
└── frontend/
    ├── index.html        # pantalla de bienvenida
    ├── login.html        # iniciar sesión
    ├── registro.html     # crear cuenta
    ├── principal.html    # pantalla principal
    ├── css/styles.css
    └── js/               # login.js, registro.js, principal.js
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

**3. Crea el archivo `backend/.env` con una clave secreta**

La clave sirve para firmar la sesión. El archivo `.env` no se sube a GitHub, así que cada persona crea el suyo:

```
SECRET_KEY=escribe-aqui-una-clave-larga-y-aleatoria
```

Puedes generar una clave con:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

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

## API

| Método | Ruta | Qué hace |
|---|---|---|
| `POST` | `/registro` | Crea una cuenta |
| `POST` | `/login` | Inicia sesión |
| `POST` | `/logout` | Cierra sesión |
| `GET` | `/dashboard` | Datos de la pantalla principal (día del ciclo, predicción…) |
| `POST` | `/periodo` | Registra un periodo, con o sin fecha de fin |
| `POST` | `/periodo/fin` | Pone la fecha de fin al periodo en curso |

## Próximos pasos

- [ ] Registro rápido de síntomas (cólicos, flujo, ánimo, sueño)
- [ ] Pantalla de calendario con el historial de periodos
- [ ] Estadísticas: duración media del ciclo y del periodo
- [ ] Perfil de usuario

## Aviso

IZAR es un proyecto de aprendizaje. Sus predicciones son una estimación a partir de la media de tus ciclos y **no sustituyen el consejo médico**.
