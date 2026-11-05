CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    contrasena_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS periodos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    inicio TEXT NOT NULL,
    fin TEXT          -- puede quedar vacío (NULL) mientras el periodo sigue en curso
);
-- Síntomas que registra cada usuaria, día a día.
-- Una fila = un síntoma de una usuaria en un día. Si un día tiene cólicos y sueño,
-- son dos filas con la misma fecha.
CREATE TABLE IF NOT EXISTS sintomas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    fecha TEXT NOT NULL,       -- el día del síntoma, como texto "2026-11-05"
    sintoma TEXT NOT NULL,     -- nombre del síntoma, por ejemplo "colicos"
    -- UNIQUE con varias columnas: no puede haber dos filas con la MISMA usuaria,
    -- el MISMO día y el MISMO síntoma. Si se intenta, SQLite da IntegrityError.
    -- Distintos síntomas el mismo día sí se permiten.
    UNIQUE (usuario_id, fecha, sintoma)
);
