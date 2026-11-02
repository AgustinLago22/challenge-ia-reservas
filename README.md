# Sistema de reservas de equipos de laboratorio

Challenge IA — Tópicos Avanzados de Ingeniería de Software. Aplicación local (Python + SQLite), con **consola y página web local**, para **consultar disponibilidad, reservar y cancelar** unidades de equipos de
laboratorio sin superposiciones y sin perder el historial. La construyó un agente de programación
(Claude Code) a partir de una especificación escrita antes del código.

| Para revisar… | Ir a |
|---------------|------|
| Qué se pidió y cómo se acepta | [§1 Especificación](#1-especificación) · [docs/ESPECIFICACION.md](docs/ESPECIFICACION.md) |
| Cómo instalar, ejecutar y probar | [§2 Solución](#2-solución) |
| Cómo se preparó y controló el agente | [§3 Preparación del agente](#3-preparación-del-agente) · [docs/AGENTE.md](docs/AGENTE.md) |
| Decisiones y los tres episodios | [§4 Registro de decisiones y delegación](#4-registro-de-decisiones-y-delegación) · [docs/DECISIONES.md](docs/DECISIONES.md) |
| Evidencia ejecutada | [docs/evidencia/](docs/evidencia/) |

---

## 1. Especificación

**Problema.** Un laboratorio registra pedidos en mensajes y una planilla. Se confirma la misma unidad
para horarios superpuestos y las cancelaciones siguen bloqueando el horario.

**Alcance.** Leer el inventario precargado (5 unidades: `MIC-01`, `MIC-02`, `OSC-01`, `MUL-01`,
`FUE-01`); consultar disponibilidad por unidad e intervalo; crear reservas (una unidad, un solicitante
ficticio, inicio y fin); cancelar conservando el registro; listar el historial; persistir entre
reinicios. Dos interfaces con las mismas reglas: consola y web local (solo `127.0.0.1`, desde v1.2).
Fuera de alcance: autenticación, notificaciones, acceso desde otras máquinas, edición de reservas
y concurrencia distribuida.

**Reglas principales** (lista completa R1–R15 en la especificación):

- Unidad conocida (comparación exacta), solicitante no vacío ni solo espacios, fechas válidas en
  formato `YYYY-MM-DDTHH:MM`, e inicio **estrictamente** anterior al fin.
- Intervalos **semiabiertos `[inicio, fin)`**: se rechaza una superposición con una reserva **activa** de la
  **misma** unidad; los límites consecutivos (10:00–11:00 y luego 11:00–12:00) están permitidos; las unidades distintas
  se pueden reservar en simultáneo; una reserva cancelada no bloquea.
- La consulta de disponibilidad usa **la misma** función que la creación de reservas.
- Cancelar nunca borra: cambia el estado a `CANCELADA`, guarda la fecha y conserva el ID y los datos.

**Supuestos.** Hora de Argentina como **UTC−3 fijo**; no se crean reservas que empiecen en el
pasado (sí se puede consultar o cancelar en el pasado); **sin** límite de duración ni de
anticipación; un solo proceso a la vez.

**Criterios de aceptación.** CA-01 a CA-14, cada uno con al menos una prueba automática:
ver la [matriz de cobertura](docs/evidencia/matriz-cobertura.md).

**Evolución.** v1 (commit `f0e4131`) → v1.1 (`f34c873`, cambio de zona horaria) → v1.2 (`136fdce`, web local) → v1.3 (orden del historial).
Los motivos están en la tabla "Historial de cambios" de la especificación. Para recuperarla:
`git log --follow -p -- docs/ESPECIFICACION.md`.

---

## 2. Solución

### Estructura

```text
reservas/                 aplicación (solo biblioteca estándar)
  dominio.py              reglas puras: validaciones, se_superponen, formato de fechas
  inventario.py           lectura de data/inventario.json (solo lectura)
  repositorio.py          SQLite: esquema, transacciones, cancelar = UPDATE
  servicio.py             casos de uso; única búsqueda de conflictos (_buscar_conflictos)
  __main__.py             CLI (argparse); sin lógica de negocio
  web.py                  web local: API JSON con http.server; sin lógica de negocio
  static/index.html       página (HTML + JS sin frameworks)
tests/                    144 pruebas pytest (unidad, servicio, persistencia, CLI y web por HTTP real)
scripts/
  verificar_mutaciones.py introduce 7 fallas a propósito y comprueba que las pruebas las detectan
  verificar_matriz.py     comprueba que cada prueba citada en la matriz exista y pase, y que no haya sin citar
  recorrido_web.py        recorrido manual de la web contra el proceso real
data/inventario.json      inventario inicial (versionado)
data/reservas.db          datos de reservas (se crea solo; NO versionado)
docs/                     especificación, agente, decisiones, progreso, prompts y evidencia
CLAUDE.md, .claude/       instrucciones, permisos y comando del agente
```

Capas: (`__main__` | `web`) → `servicio` → (`dominio`, `repositorio`). Por qué así: [D-11](docs/DECISIONES.md).

### Decisiones técnicas

Python 3.13 con biblioteca estándar únicamente (D-01); CLI (D-02); SQLite con `BEGIN IMMEDIATE`
para que verificar e insertar sea atómico (D-03); una sola función de superposición, aplicada en
Python y no en SQL (D-04, D-12); UTC−3 fijo porque `zoneinfo` falla en Windows sin `tzdata` (D-10);
salida UTF-8 forzada (D-16); web con `http.server` y controles de uso local (D-19 a D-22). Detalle de todas en [docs/DECISIONES.md](docs/DECISIONES.md).

### Requisitos previos y versiones

| Herramienta | Versión verificada | Nota |
|-------------|--------------------|------|
| Python | 3.13.5 | `requires-python >= 3.13` (`pyproject.toml`) |
| pytest | 9.1.1 | única dependencia, solo para pruebas; fijada con sus dependencias en `requirements-dev.txt` |
| SQLite | 3.49.1 | viene con Python |
| SO | Windows 11 (Git Bash y PowerShell 5.1) | en Linux o macOS usar `.venv/bin/python` |

La aplicación no necesita ninguna cuenta ni servicio externo. **No hace falta el agente** para
ejecutarla ni para probarla.

### Instalación

```bash
git clone <url-del-repo> && cd <carpeta>
py -m venv .venv                                    # Linux/macOS: python3 -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
```

Verificado desde un clon limpio en el episodio 3: dependencias idénticas a `requirements-dev.txt` y todas las
pruebas en verde (ver [PROGRESO](docs/PROGRESO.md)).

### Carga inicial y reinicio de datos

- **Carga inicial:** no hace falta ningún paso. El inventario se lee de `data/inventario.json` en cada
  ejecución, y `data/reservas.db` se crea vacío en el primer uso.
- **Dónde persisten los datos:** `data/reservas.db` (SQLite). Se puede cambiar con la variable `RESERVAS_DB`.
- **Reinicio de datos:** `.venv/Scripts/python -m reservas reiniciar-datos --confirmar`
  > ⚠️ **Borra TODAS las reservas, activas y canceladas, sin posibilidad de recuperarlas.** Sin `--confirmar` no
  > borra nada y termina con código 1. El inventario no se modifica. Los IDs no se reutilizan
  > después del reinicio: la próxima reserva no vuelve a ser la `#1`.

### Página web local (la forma más fácil de probarlo)

```bash
.venv/Scripts/python -m reservas web          # luego abrir http://127.0.0.1:8000 en el navegador
.venv/Scripts/python -m reservas web --puerto 8080
```

La página permite consultar disponibilidad (de una unidad o de todas), reservar, ver el historial con
filtros y orden (por defecto, las de fecha más reciente primero) y cancelar con un botón. Usa **la misma base** que la consola: lo que se reserva en la web aparece en
`listar`, y al revés. Arriba muestra la hora del servidor y la ruta de la base. Para detener el servidor:
`Ctrl+C`. Los datos quedan guardados. El reinicio de datos **no** está en la web, solo en la consola.

API (útil para probar con otras herramientas): `GET /api/unidades`, `GET /api/reservas?unidad=&estado=&orden=`,
`GET /api/disponibilidad?unidad=<ID|todas>&inicio=&fin=`, `POST /api/reservas` (JSON con `unidad`,
`solicitante`, `inicio`, `fin`), `POST /api/reservas/<id>/cancelar`. Respuestas: 201 creada,
400 entrada inválida, 404 inexistente, 409 superposición o ya cancelada.

### Comandos de la aplicación

```bash
.venv/Scripts/python -m reservas unidades
.venv/Scripts/python -m reservas disponibilidad --unidad MIC-01 --inicio 2026-11-02T10:00 --fin 2026-11-02T11:00
.venv/Scripts/python -m reservas disponibilidad --unidad todas  --inicio 2026-11-02T10:00 --fin 2026-11-02T11:00
.venv/Scripts/python -m reservas reservar --unidad MIC-01 --solicitante "Ana Prueba" --inicio 2026-11-02T10:00 --fin 2026-11-02T11:00
.venv/Scripts/python -m reservas cancelar --id 1
.venv/Scripts/python -m reservas listar [--unidad MIC-01] [--estado ACTIVA|CANCELADA] [--orden fecha_desc]
.venv/Scripts/python -m reservas reiniciar-datos --confirmar
.venv/Scripts/python -m reservas web [--puerto 8000]
```

| Código de salida | Significado |
|------------------|-------------|
| 0 | Operación exitosa. Una consulta que responde "OCUPADA" también es exitosa. |
| 1 | Operación rechazada (regla de negocio o entrada inválida). El mensaje va a stderr. |
| 2 | Uso incorrecto de la CLI (falta un argumento, o el `--id` no es un número). |

Variables de entorno: `RESERVAS_DB` (ruta de la base), `RESERVAS_INVENTARIO` (ruta del inventario),
`RESERVAS_AHORA` (fija el "ahora" en formato `YYYY-MM-DDTHH:MM`, solo para pruebas y demos reproducibles).

### Ejemplo de entrada y salida (ejecución real)

Con `RESERVAS_AHORA=2026-11-01T08:00` y una base vacía. La salida completa, con todos los códigos de
salida, está en [docs/evidencia/ejemplo-cli.txt](docs/evidencia/ejemplo-cli.txt).

```text
$ python -m reservas reservar --unidad MIC-01 --solicitante "Ana Prueba" --inicio 2026-11-02T10:00 --fin 2026-11-02T11:00
Reserva creada: #1    MIC-01  ACTIVA     2026-11-02T10:00 -> 2026-11-02T11:00  Ana Prueba

$ python -m reservas reservar --unidad MIC-01 --solicitante "Beto Ficticio" --inicio 2026-11-02T10:30 --fin 2026-11-02T11:30
Error: La unidad MIC-01 ya está reservada en ese intervalo: #1 (2026-11-02T10:00->2026-11-02T11:00)

$ python -m reservas reservar --unidad MIC-01 --solicitante "Beto Ficticio" --inicio 2026-11-02T11:00 --fin 2026-11-02T12:00
Reserva creada: #2    MIC-01  ACTIVA     2026-11-02T11:00 -> 2026-11-02T12:00  Beto Ficticio

$ python -m reservas reservar --unidad MIC-02 --solicitante "Carla Inventada" --inicio 2026-11-02T10:00 --fin 2026-11-02T11:00
Reserva creada: #3    MIC-02  ACTIVA     2026-11-02T10:00 -> 2026-11-02T11:00  Carla Inventada

$ python -m reservas cancelar --id 1
Reserva cancelada: #1    MIC-01  CANCELADA  2026-11-02T10:00 -> 2026-11-02T11:00  Ana Prueba  (cancelada 2026-11-01T08:00:00)

$ python -m reservas disponibilidad --unidad MIC-01 --inicio 2026-11-02T10:00 --fin 2026-11-02T11:00
MIC-01  DISPONIBLE  2026-11-02T10:00 -> 2026-11-02T11:00

$ python -m reservas listar
#1    MIC-01  CANCELADA  2026-11-02T10:00 -> 2026-11-02T11:00  Ana Prueba  (cancelada 2026-11-01T08:00:00)
#2    MIC-01  ACTIVA     2026-11-02T11:00 -> 2026-11-02T12:00  Beto Ficticio
#3    MIC-02  ACTIVA     2026-11-02T10:00 -> 2026-11-02T11:00  Carla Inventada
```

### Pruebas y verificaciones

```bash
.venv/Scripts/python -m pytest -v                    # 144 pruebas
.venv/Scripts/python scripts/verificar_mutaciones.py # 7 mutaciones; cada una debe hacer fallar alguna prueba
.venv/Scripts/python scripts/verificar_matriz.py     # cada prueba citada en la matriz existe y pasa
.venv/Scripts/python scripts/recorrido_web.py        # recorrido de la web contra el proceso real
```

| Verificación requerida | Dónde | Resultado registrado |
|------------------------|-------|----------------------|
| Creación válida | `test_ca01_*` | ✅ [orden-pytest.txt](docs/evidencia/orden-pytest.txt) |
| Rechazo de superposición | `test_ca02_*` | ✅ |
| Límites consecutivos | `test_ca03_*`, `test_se_superponen` | ✅ |
| Unidades distintas simultáneas | `test_ca04_*` | ✅ |
| Entradas inválidas | `test_ca05_*` … `test_ca08_*`, `test_cli_entradas_invalidas` | ✅ |
| Cancelar conserva y libera | `test_ca10_*` | ✅ |
| Persistencia tras reiniciar (activas y canceladas) | `test_ca12_*` (proceso nuevo) + [procedimiento manual](docs/evidencia/persistencia-manual.md) | ✅ automático y manual, con salida observada |
| Mismas reglas desde la web (CA-14) | `tests/test_web.py` (HTTP real) + [recorrido](docs/evidencia/episodio-4-recorrido-web.txt) | ✅ |
| Que las pruebas detecten errores | `verificar_mutaciones.py` | ✅ 7 de 7 detectadas ([evidencia](docs/evidencia/episodio-4-mutaciones.txt)) |

Las pruebas usan siempre bases temporales (`tmp_path`) y nunca tocan `data/reservas.db`.

### Pendientes y limitaciones

- **Sin concurrencia real:** pensado para un solo usuario a la vez. `BEGIN IMMEDIATE` evita que dos escrituras
  se mezclen, pero no se probaron procesos simultáneos.
- **UTC−3 fijo:** si Argentina volviera a aplicar horario de verano, habría que usar `zoneinfo` + `tzdata`.
- **No se pueden editar reservas:** para cambiar un horario hay que cancelar y crear otra.
- **Rendimiento:** los conflictos se filtran en Python sobre las reservas activas de la unidad, lo que alcanza
  para el volumen de un laboratorio y no para producción.
- **Consola:** la salida se fuerza a UTF-8. Se verificó en Git Bash y en PowerShell 5.1 con la salida capturada;
  **no** se verificó en una consola interactiva de cmd o PowerShell con otra página de códigos, donde los acentos
  podrían verse mal.
- **Sin prueba automática del reloj real** (`ahora_local`): todas las pruebas inyectan el reloj.
- **El agente no probó la página web en un navegador real:** se probaron la API, el proceso real y la sintaxis del
  JavaScript (`node --check`). El aspecto y los clics los verifica el humano.
- **Una falla intermitente sin causa confirmada:** una vez apareció `ConnectionAbortedError` en una prueba web. Se aplicó
  una corrección defensiva y no volvió a aparecer en las corridas posteriores (D-24).
- **El servidor web es solo para uso local** (`http.server`): no está pensado para exponerse en una red.

---

## 3. Preparación del agente

Resumen (detalle y evidencia en **[docs/AGENTE.md](docs/AGENTE.md)**):

- **Entorno y modelo:** Claude Code `2.1.311` (harness existente), modelo Claude Opus 5.5
  (`claude-opus-5-5`), un único agente con herramientas reales sobre el repositorio.
- **Instrucciones:** [`CLAUDE.md`](CLAUDE.md), que Claude Code carga en cada sesión, y los prompts de cada episodio en
  [`docs/prompts/`](docs/prompts/).
- **Contexto:** especificación, inventario, progreso y código. Se excluyeron el PDF del enunciado, la base de datos,
  los archivos `.env` e internet.
- **Permisos:** [`.claude/settings.json`](.claude/settings.json) con tres listas (permitido / requiere aprobación / denegado).
  La sesión corrió en modo *bypass*, pero la regla `deny` **sí se aplicó**: un `rm -rf` fue bloqueado en el episodio 3.
- **Adaptaciones específicas con evidencia de uso:** regla de turnos consecutivos (`se_superponen` con `<`, verificada por la
  mutación M1) y procedimiento de persistencia (cancelar con `UPDATE`, verificado por M6; pruebas en `tmp_path`;
  verificación en proceso nuevo).
- **Retención del progreso:** [`docs/PROGRESO.md`](docs/PROGRESO.md), versionado y actualizado en cada episodio.

## 4. Registro de decisiones y delegación

**[docs/DECISIONES.md](docs/DECISIONES.md)** contiene 25 decisiones (D-01…D-25), con motivo, alternativas y
consecuencias, y cuatro episodios de delegación (la consigna pide tres; el cuarto es la web):

| Episodio | Objetivo | Qué pasó | Decisión | Commit |
|----------|----------|----------|----------|--------|
| 1 | Dominio, persistencia y pruebas de reglas | `zoneinfo` falló en Windows → se corrigió la especificación (v1.1) antes de codificar; 80 pruebas; 2 mutaciones detectadas | Aceptar con corrección | `f34c873` |
| 2 | CLI y persistencia tras reinicio | El procedimiento manual mostró acentos rotos (`est�`) que las pruebas no veían → prueba de regresión en rojo → corrección → verde | Corregir y aceptar | `27f4fb9` |
| 3 | Auditoría de cobertura y documentación | 6 huecos encontrados y cerrados; mutaciones ampliadas de 2 a 6 reglas; reproducción desde un clon limpio | Aceptar | `0f3b0ae`, `7a2c23d` |
| 4 | Web local | Primero la especificación v1.2; el puerto ocupado no daba error en Windows → diagnóstico → corrección; el verificador de la matriz era permisivo → endurecido | Corregir y aceptar | `136fdce` + commit de implementación |
