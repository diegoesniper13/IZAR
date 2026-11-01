-- Datos de prueba: periodos para una usuaria que ya exista.
-- Cambia 'ana' por el nombre de usuario con el que te hayas registrado.
INSERT INTO periodos (usuario_id, inicio, fin)
VALUES ((SELECT id FROM usuarios WHERE usuario = 'ana'), '2026-08-13', '2026-08-18');

INSERT INTO periodos (usuario_id, inicio, fin)
VALUES ((SELECT id FROM usuarios WHERE usuario = 'ana'), '2026-09-10', '2026-09-15');

INSERT INTO periodos (usuario_id, inicio, fin)
VALUES ((SELECT id FROM usuarios WHERE usuario = 'ana'), '2026-10-09', '2026-10-14');