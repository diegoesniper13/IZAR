# Apuntes de SQL (SQLite) — explicado con IZAR

Guía de SQL usando ejemplos de tu propia app. Para repasar cuando quieras.

---

## 1. ¿Qué es una base de datos y qué es SQL?

Una **base de datos** es donde guardas la información para que no se pierda al apagar el servidor. IZAR usa **SQLite**, que guarda todo en **un solo archivo**: `regla.db`.

**SQL** es el idioma para hablar con la base de datos: crear tablas, guardar, leer, borrar. Siempre son las mismas cuatro acciones:

| Quiero... | Palabra SQL |
|---|---|
| Guardar algo nuevo | `INSERT` |
| Leer | `SELECT` |
| Cambiar algo que existe | `UPDATE` |
| Borrar | `DELETE` |

En IZAR, el único archivo que habla SQL es **`bd.py`**. Flask y `ciclos.py` no tocan la base de datos.

---

## 2. Las tablas: cómo se organizan los datos

Una tabla es como una hoja de cálculo: **columnas** (los campos) y **filas** (los registros). IZAR tiene tres tablas, definidas en `schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    contrasena_hash TEXT NOT NULL
);
```

Cada columna tiene un **tipo** y unas **reglas**:

- **`INTEGER` / `TEXT`** → el tipo: número o texto. (Las fechas las guardas como TEXT, por ejemplo `"2026-11-09"`.)
- **`PRIMARY KEY AUTOINCREMENT`** → `id` es el identificador único de cada fila, y se pone solo (1, 2, 3...). No tienes que dárselo tú.
- **`NOT NULL`** → esa columna no puede quedar vacía.
- **`UNIQUE`** → no puede repetirse. Por eso no puede haber dos usuarias con el mismo nombre de usuario.

La tabla `periodos` enseña dos cosas más:

```sql
CREATE TABLE IF NOT EXISTS periodos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    inicio TEXT NOT NULL,
    fin TEXT
);
```

- **`REFERENCES usuarios(id)`** → `usuario_id` apunta al `id` de una usuaria. Así cada periodo sabe de quién es. Esto se llama **clave foránea**.
- **`fin TEXT`** (sin `NOT NULL`) → el fin puede quedar vacío (`NULL`), para los periodos en curso.

Y la tabla `sintomas` enseña el UNIQUE de varias columnas:

```sql
UNIQUE (usuario_id, fecha, sintoma)
```

Significa: no puede repetirse la combinación de esas tres. Una usuaria no puede tener el mismo síntoma dos veces el mismo día, pero sí dos síntomas distintos ese día.

---

## 3. Conectar y el patrón de siempre

Toda función de `bd.py` sigue el mismo esqueleto:

```python
import sqlite3

conexion = sqlite3.connect(RUTA_BD)   # 1. abrir el archivo
cursor = conexion.cursor()            # 2. el "mando" para dar órdenes
cursor.execute("...SQL...", (...))    # 3. ejecutar la orden
# ... (según la acción)
conexion.close()                      # 4. cerrar
```

- **`conexion`** → abre el archivo `regla.db`.
- **`cursor`** → es con quien le das las órdenes SQL.
- **`close()`** → cerrar al terminar, siempre.

---

## 4. INSERT: guardar algo nuevo

```python
cursor.execute(
    "INSERT INTO usuarios (usuario, nombre, contrasena_hash) VALUES (?, ?, ?)",
    (usuario, nombre, hash_contrasena)
)
conexion.commit()
```

- **`INSERT INTO tabla (columnas) VALUES (?, ?, ?)`** → la forma de guardar.
- **Los `?`** → huecos que se rellenan con la tupla del final, por orden. (En el punto 8 verás por qué es importante.)
- **`commit()`** → ⚠️ **IMPRESCINDIBLE.** Sin él, el INSERT se hace pero NO se guarda en el archivo. Es como escribir en Word y no guardar. Tú ya te has encontrado este fallo.

---

## 5. SELECT: leer

```python
cursor.execute(
    "SELECT inicio, fin FROM periodos "
    "WHERE usuario_id = (SELECT id FROM usuarios WHERE usuario = ?) "
    "ORDER BY inicio",
    (usuario,)
)
filas = cursor.fetchall()
```

- **`SELECT columnas FROM tabla`** → qué columnas quieres y de qué tabla.
- **`WHERE condición`** → filtra: solo las filas que cumplan la condición. Aquí, solo los periodos de esa usuaria.
- **`ORDER BY inicio`** → ordena por esa columna (de más antiguo a más reciente).
- **`fetchall()`** → recoge todas las filas que ha encontrado, como una lista de tuplas: `[('2026-01-01', '2026-01-06'), ...]`.
- **`fetchone()`** → cuando solo esperas una fila (como al buscar una contraseña).

### La subconsulta (SELECT dentro de SELECT)

```sql
WHERE usuario_id = (SELECT id FROM usuarios WHERE usuario = ?)
```

La sesión tiene el **nombre** de usuario, pero la tabla `periodos` guarda el **id** (un número). El `SELECT` de dentro traduce el nombre a su id. Es como decir: "los periodos de la usuaria cuyo id es el de 'ana'".

---

## 6. UPDATE: cambiar algo que ya existe

Tu función de cerrar un periodo:

```python
cursor.execute(
    "UPDATE periodos SET fin = ? "
    "WHERE usuario_id = (SELECT id FROM usuarios WHERE usuario = ?) "
    "AND inicio = ? AND fin IS NULL",
    (fin, usuario, inicio)
)
conexion.commit()
```

- **`UPDATE tabla SET columna = ?`** → cambia esa columna.
- **`WHERE ...`** → ⚠️ en qué filas. **Sin `WHERE`, cambiaría TODAS las filas.**
- **`fin IS NULL`** → en SQL, lo vacío se comprueba con `IS NULL`, no con `= NULL`.
- También lleva `commit()`.

**`cursor.rowcount`** te dice cuántas filas cambió. Si es 0, no había ninguna que cumpliera el WHERE. Lo usas para saber si de verdad se cerró un periodo.

---

## 7. DELETE: borrar

Tu función de borrar los síntomas de hoy:

```python
cursor.execute(
    "DELETE FROM sintomas "
    "WHERE usuario_id = (SELECT id FROM usuarios WHERE usuario = ?) "
    "AND fecha = ?",
    (usuario, fecha)
)
conexion.commit()
borrados = cursor.rowcount
```

- **`DELETE FROM tabla WHERE ...`** → borra las filas que cumplan el WHERE.
- ⚠️ **`DELETE FROM sintomas` SIN `WHERE` borraría la tabla ENTERA.** El WHERE es lo que lo hace seguro.
- Dos condiciones con `AND`: de esa usuaria **y** de esa fecha. Así nunca borras los de otra persona.
- `rowcount` te dice cuántos borró (0 si no había ninguno).

---

## 8. Los `?`: lo más importante de seguridad

**NUNCA** metas datos de la usuaria directamente en el texto del SQL. Siempre con `?`:

```python
# BIEN: el ? se rellena aparte
cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))

# MAL: pegar el dato en el texto
cursor.execute("SELECT * FROM usuarios WHERE usuario = '" + usuario + "'")
```

¿Por qué? Imagina que alguien escribe como usuario: `' OR '1'='1`. En la versión MAL, eso se mezcla con tu SQL y puede saltarse la seguridad o borrar datos. Es la **inyección SQL**, uno de los ataques más comunes.

Con `?`, SQLite trata el dato **siempre como un dato**, nunca como una orden. Da igual lo que escriba la usuaria. Por eso todas tus consultas usan `?`: tu app ya está protegida contra esto (lo comprobamos en la revisión de seguridad).

Detalle: la tupla de un solo valor lleva una coma al final → `(usuario,)`. Sin la coma, Python no lo entiende como tupla.

---

## 9. Ver la base de datos a mano

Desde una terminal, para mirar qué hay guardado:

```bash
sqlite3 regla.db        # abre la base de datos
.headers on             # muestra los nombres de las columnas
.mode column            # lo pone en columnas ordenadas
SELECT * FROM periodos; # ver todo (el ; es obligatorio)
.quit                   # salir
```

Los comandos con punto (`.headers`, `.quit`) son de la herramienta `sqlite3`. Los demás son SQL normal.

Recuerda: las contraseñas no se ven, solo su **hash**. No se pueden revertir, y eso es a propósito.

---

## Resumen en una frase

**SQL guarda los datos en tablas con columnas y reglas; usas INSERT para crear, SELECT para leer, UPDATE para cambiar y DELETE para borrar; el WHERE decide sobre qué filas, el commit lo hace permanente, y los `?` protegen contra ataques.**
