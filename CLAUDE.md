# Instrucciones para el agente (Claude Code)

Proyecto: sistema local de reservas de equipos de laboratorio (challenge académico).
La fuente de verdad de los requisitos es `docs/ESPECIFICACION.md`. Si algo de este
archivo contradice la especificación, gana la especificación y hay que avisarlo.

## Al empezar cada tarea

1. Leer `docs/PROGRESO.md` (estado actual, próximo paso, decisiones abiertas).
2. Leer `docs/ESPECIFICACION.md`, las reglas (R1–R15) y los criterios de aceptación (CA-xx).
3. Trabajar solo en el alcance del episodio pedido. No adelantar episodios futuros.

## Stack fijo (no cambiar sin pedido explícito)

- Python 3.13, **solo biblioteca estándar** en la aplicación (`sqlite3`, `argparse`,
  `json`, `datetime`). Única dependencia de desarrollo: `pytest` (fijada
  en `requirements-dev.txt`). No instalar paquetes nuevos sin aprobación.
- Paquete `reservas/` en la raíz del repo, ejecutable con `python -m reservas`.
- Pruebas en `tests/`, ejecutadas con `.venv/Scripts/python -m pytest -v`.
- En Windows usar la herramienta **Bash** (Git Bash) para comandos, con rutas `/`.

## Regla de intervalos (adaptación específica: NO improvisar)

- Los intervalos son **semiabiertos `[inicio, fin)`**.
- Hay **una sola función** que decide la superposición:
  `se_superponen(a_inicio, a_fin, b_inicio, b_fin) -> bool` devuelve
  `a_inicio < b_fin and b_inicio < a_fin`. Prohibido usar `<=` en esa comparación.
- Crear reserva y consultar disponibilidad **deben usar la misma función** de búsqueda
  de conflictos (R13). No duplicar la lógica en la CLI ni en SQL con otra fórmula.
- Solo cuentan como conflicto las reservas con estado `ACTIVA` de la **misma unidad**.
- Toda modificación de esta lógica debe mantener en verde las pruebas de límites
  consecutivos (11:00–12:00 después de 10:00–11:00, y 09:00–10:00 antes).

## Fechas y reloj

- Formato único de entrada: `YYYY-MM-DDTHH:MM`, parseado con
  `datetime.strptime(valor, "%Y-%m-%dT%H:%M")`. Zona horaria fija UTC−3 con
  `datetime.timezone(timedelta(hours=-3))`. **No usar `zoneinfo`**: en Windows falla
  sin el paquete `tzdata` (comprobado, ver especificación v1.1). Se guardan como texto
  en ese mismo formato.
- El "ahora" se recibe mediante un **reloj inyectable** (callable que devuelve
  `datetime`). Las pruebas nunca dependen de la fecha real de la máquina.

## Procedimiento de persistencia (adaptación específica: NO improvisar)

- Almacenamiento: SQLite en `data/reservas.db` (ruta configurable por la variable de
  entorno `RESERVAS_DB` o por parámetro). El inventario se lee de `data/inventario.json`
  y nunca se modifica.
- **Nunca** borrar reservas: cancelar = `UPDATE ... SET estado='CANCELADA',
  cancelada_en=...`. No usar `DELETE` ni `DROP` salvo en el comando explícito de
  reinicio de datos, que exige confirmación.
- Verificar conflicto + insertar dentro de **una misma transacción**
  (`BEGIN IMMEDIATE`) para que un rechazo no deje datos a medias (R14).
- El esquema se crea con `CREATE TABLE IF NOT EXISTS` al abrir la base: abrir una base
  existente **no** debe perder datos.
- Las pruebas usan **siempre** una base temporal (`tmp_path` de pytest).
  Nunca leer, escribir ni borrar `data/reservas.db` desde las pruebas.
- La persistencia se prueba **reabriendo** la base en una instancia nueva (y al menos
  una prueba en un **proceso nuevo** con `subprocess`), no reutilizando el mismo objeto.

## Pruebas

- Cada criterio de aceptación CA-xx tiene al menos una prueba; el nombre o docstring
  de la prueba cita el CA (p. ej. `test_ca03_limites_consecutivos_permitidos`).
- Usar solicitantes **ficticios** (p. ej. "Ana Prueba", "Beto Ficticio"). Nunca datos reales.
- No marcar una tarea como terminada sin ejecutar `pytest` y ver el resultado real.

## Honestidad del registro (obligatorio)

- Distinguir siempre **"ejecutado y observado"** de **"afirmado, no ejecutado"**.
- Nunca inventar resultados de pruebas, salidas de comandos ni decisiones humanas.
- Las decisiones de aceptar, corregir o rechazar las toma el humano. El agente deja
  esos campos como `[COMPLETAR POR EL HUMANO]`.

## Al terminar cada tarea

1. Ejecutar las pruebas y guardar la salida real en `docs/evidencia/` (ver `/cerrar-episodio`).
2. Actualizar `docs/PROGRESO.md`: qué se hizo, qué se verificó, pendientes y próximo paso.
3. Registrar las decisiones técnicas nuevas en `docs/DECISIONES.md`.
4. Proponer un mensaje de commit. El commit requiere aprobación humana.
   **Nunca hacer `git push`.**

## No tocar sin pedido explícito

`docs/ESPECIFICACION.md`, `CLAUDE.md`, `.claude/`, `data/inventario.json`,
`requirements-dev.txt`. Si alguno debería cambiar, proponerlo y explicar el motivo.
