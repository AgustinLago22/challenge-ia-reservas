# Procedimiento manual de persistencia (CA-12)

Verifica que las reservas **activas y canceladas** se recuperan tras detener y reiniciar la
aplicación **sin borrar datos**. Cada comando es un proceso independiente que termina
(la aplicación "se detiene"). La Sesión B se ejecuta en una **shell nueva** sobre el mismo
archivo `data/reservas.db`.

## Cómo reproducirlo

Desde la raíz del repo, en Git Bash (en PowerShell: `$env:RESERVAS_AHORA="2026-11-01T08:00"`).
`RESERVAS_AHORA` fija el "ahora" para que el resultado no dependa del día en que se ejecute.

1. Partir de una base vacía. **Atención: esto borra todas las reservas de `data/reservas.db`.**
   `.venv/Scripts/python -m reservas reiniciar-datos --confirmar`
   (En la ejecución registrada abajo no hizo falta, porque `data/reservas.db` no existía todavía.)
2. `export RESERVAS_AHORA=2026-11-01T08:00` y ejecutar los comandos de la Sesión A.
3. Cerrar la terminal. Abrir una terminal nueva, repetir el `export` y ejecutar la Sesión B.

## Resultado esperado

| Paso | Esperado |
|------|----------|
| A1 | `#1` MIC-01 10:00–11:00 creada (código 0). |
| A2 | MIC-01 10:30–11:30 rechazada por conflicto con `#1` (código 1). |
| A3 | MIC-01 11:00–12:00 creada como `#2`: límite consecutivo (código 0). |
| A4 | MIC-02 10:00–11:00 creada como `#3`: otra unidad (código 0). |
| A5 | `#3` cancelada, con la fecha de cancelación. |
| B1 | Tras reiniciar: `#1` y `#2` ACTIVA, `#3` CANCELADA, con los mismos datos. |
| B2 | Disponibilidad 10:00–11:00: MIC-01 OCUPADA (por `#1`), MIC-02 DISPONIBLE (la `#3` está cancelada). |
| B3 | MIC-01 10:15–10:45 rechazada: la activa sigue bloqueando tras el reinicio. |
| B4 | MIC-02 10:00–11:00 creada como `#4`: el ID no reutiliza el 3. |
| B5 | El historial de canceladas sigue mostrando `#3`. |

## Resultado observado (ejecución real del 2026-11-02, Python 3.13.5, Windows 11 + Git Bash)

```text
## Sesión A (proceso por comando)

$ python -m reservas reservar --unidad MIC-01 --solicitante Ana Prueba --inicio 2026-11-02T10:00 --fin 2026-11-02T11:00
Reserva creada: #1    MIC-01  ACTIVA     2026-11-02T10:00 -> 2026-11-02T11:00  Ana Prueba
[código de salida: 0]

$ python -m reservas reservar --unidad MIC-01 --solicitante Beto Ficticio --inicio 2026-11-02T10:30 --fin 2026-11-02T11:30
Error: La unidad MIC-01 ya est� reservada en ese intervalo: #1 (2026-11-02T10:00->2026-11-02T11:00)   # ← � = byte crudo 0xE1 (cp1252)
[código de salida: 1]

$ python -m reservas reservar --unidad MIC-01 --solicitante Beto Ficticio --inicio 2026-11-02T11:00 --fin 2026-11-02T12:00
Reserva creada: #2    MIC-01  ACTIVA     2026-11-02T11:00 -> 2026-11-02T12:00  Beto Ficticio
[código de salida: 0]

$ python -m reservas reservar --unidad MIC-02 --solicitante Carla Inventada --inicio 2026-11-02T10:00 --fin 2026-11-02T11:00
Reserva creada: #3    MIC-02  ACTIVA     2026-11-02T10:00 -> 2026-11-02T11:00  Carla Inventada
[código de salida: 0]

$ python -m reservas cancelar --id 3
Reserva cancelada: #3    MIC-02  CANCELADA  2026-11-02T10:00 -> 2026-11-02T11:00  Carla Inventada  (cancelada 2026-11-01T08:00:00)
[código de salida: 0]

$ python -m reservas listar
#1    MIC-01  ACTIVA     2026-11-02T10:00 -> 2026-11-02T11:00  Ana Prueba
#2    MIC-01  ACTIVA     2026-11-02T11:00 -> 2026-11-02T12:00  Beto Ficticio
#3    MIC-02  CANCELADA  2026-11-02T10:00 -> 2026-11-02T11:00  Carla Inventada  (cancelada 2026-11-01T08:00:00)
[código de salida: 0]

## Aplicación detenida. Archivo de datos en disco:
16384 bytes data/reservas.db

## Sesión B (shell nueva, misma base, sin borrar datos)

$ python -m reservas listar
#1    MIC-01  ACTIVA     2026-11-02T10:00 -> 2026-11-02T11:00  Ana Prueba
#2    MIC-01  ACTIVA     2026-11-02T11:00 -> 2026-11-02T12:00  Beto Ficticio
#3    MIC-02  CANCELADA  2026-11-02T10:00 -> 2026-11-02T11:00  Carla Inventada  (cancelada 2026-11-01T08:00:00)
[código de salida: 0]

$ python -m reservas disponibilidad --unidad todas --inicio 2026-11-02T10:00 --fin 2026-11-02T11:00
MIC-01  OCUPADA     2026-11-02T10:00 -> 2026-11-02T11:00  conflicto con: #1 2026-11-02T10:00->2026-11-02T11:00 (Ana Prueba)
MIC-02  DISPONIBLE  2026-11-02T10:00 -> 2026-11-02T11:00
OSC-01  DISPONIBLE  2026-11-02T10:00 -> 2026-11-02T11:00
MUL-01  DISPONIBLE  2026-11-02T10:00 -> 2026-11-02T11:00
FUE-01  DISPONIBLE  2026-11-02T10:00 -> 2026-11-02T11:00
[código de salida: 0]

$ python -m reservas reservar --unidad MIC-01 --solicitante Dario Ejemplo --inicio 2026-11-02T10:15 --fin 2026-11-02T10:45
Error: La unidad MIC-01 ya está reservada en ese intervalo: #1 (2026-11-02T10:00->2026-11-02T11:00)
[código de salida: 1]

$ python -m reservas reservar --unidad MIC-02 --solicitante Dario Ejemplo --inicio 2026-11-02T10:00 --fin 2026-11-02T11:00
Reserva creada: #4    MIC-02  ACTIVA     2026-11-02T10:00 -> 2026-11-02T11:00  Dario Ejemplo
[código de salida: 0]

$ python -m reservas listar --estado CANCELADA
#3    MIC-02  CANCELADA  2026-11-02T10:00 -> 2026-11-02T11:00  Carla Inventada  (cancelada 2026-11-01T08:00:00)
[código de salida: 0]

```

**Comparación:** todos los pasos coinciden con lo esperado **salvo un defecto de presentación en A2**.
El mensaje salió como `ya est� reservada`: en Windows, con la salida redirigida, Python escribía
en cp1252 y Git Bash lo leía como UTF-8. La regla de negocio funcionó (rechazo y código 1);
lo que falló fue la codificación del texto.

**Corrección:** la prueba `tests/test_cli.py::test_cli_salida_utf8_sin_configurar_el_entorno`
reprodujo el defecto (`UnicodeDecodeError: ... byte 0xe1`, 1 failed). Se corrigió con
`_salida_utf8()` en `reservas/__main__.py` y la prueba pasó. Al repetir el paso A2 después de la
corrección, la salida observada fue:

```text
Error: La unidad MIC-01 ya está reservada en ese intervalo: #1 (2026-11-02T10:00->2026-11-02T11:00), #2 (2026-11-02T11:00->2026-11-02T12:00)
[código 1]
```

En la repetición aparecen dos conflictos porque en ese momento `#2` (11:00–12:00) ya existía,
y 10:30–11:30 también se superpone con ella. Es correcto. La Sesión B se ejecutó después de la corrección.

La versión automática de este procedimiento es `tests/test_cli.py::test_ca12_persistencia_tras_reiniciar_en_proceso_nuevo`.
