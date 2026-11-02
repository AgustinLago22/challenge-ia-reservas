# Progreso del proyecto

> Archivo versionado de retención de progreso. El agente lo lee al empezar cada tarea
> y lo actualiza al terminar (ver `CLAUDE.md`). Cada entrada distingue lo
> **ejecutado y observado** de lo **afirmado, no ejecutado**.

## Estado actual

| Fase | Estado |
|------|--------|
| 0. Preparación del entorno y del agente | Completa (commit `f0e4131`) |
| Episodio 1. Dominio + persistencia SQLite + pruebas de reglas | Completo (commit `f34c873`) |
| Episodio 2. CLI + prueba de persistencia en proceso nuevo | Completo (commit `27f4fb9`) |
| Episodio 3. Auditoría de cobertura CA ↔ pruebas + sección Solución del README | Completo (commits `0f3b0ae` y `7a2c23d`) |
| Episodio 4. Interfaz web local (especificación v1.2, CA-14) | Completo (commits `136fdce` e implementación) |

**Próximo paso:** el humano abre la web y sigue la lista de `docs/prompts/episodio-4.md`, ratifica los cuatro episodios (`docs/DECISIONES.md`), crea el repositorio remoto, hace `git push` y envía el enlace.

## Decisiones abiertas

- Ninguna. Desde el 2026-11-02 el humano autorizó el modo automático con commits (D-09).

## Bitácora

### 2026-11-02 — Episodio 4

**Ejecutado y observado**

- Especificación v1.2 commiteada antes del código (`136fdce`).
- `pytest -q tests/test_web.py` → **25 passed, 1 failed**: `test_ca14_puerto_ocupado_da_error_claro` llegó al timeout de 30 s.
- Diagnóstico: con la opción por defecto un segundo servidor se enlaza a un puerto ocupado; con `SO_EXCLUSIVEADDRUSE`
  aparece `WinError 10048`. Corregido (D-22) → `128 passed` ([evidencia](evidencia/episodio-4-pytest.txt)).
- `node --check` sobre el JavaScript de la página → sintaxis válida (node v22.16.0).
- `scripts/recorrido_web.py` contra el proceso real → 201 / 409 / 201 / 400 / 200, disponible tras cancelar; datos
  presentes tras reiniciar el servidor ([evidencia](evidencia/episodio-4-recorrido-web.txt)).
- `scripts/recorrido_web.py data/reservas.db` → se niega a ejecutarse (código 1), como se esperaba.
- Mutaciones: 7 de 7 detectadas ([evidencia](evidencia/episodio-4-mutaciones.txt)).
- `verificar_matriz.py`: 16 pruebas sin citar con código 0 → endurecido (D-23) → 66/66 citadas, 128 passed
  ([evidencia](evidencia/episodio-4-matriz.txt)).

**No ejecutado / pendiente**

- **La página no se abrió en un navegador real** (el agente no dispone de uno). Lo verifica el humano con la lista de
  `docs/prompts/episodio-4.md`.
- En el ejecutable de Bash del agente falló una vez un heredoc muy largo (`unexpected EOF`); no se ejecutó nada y se
  repitió el cambio desde un archivo de script.

### 2026-11-02 — Episodio 3

**Ejecutado y observado**

- `pytest --collect-only` → 45 funciones de prueba; la auditoría encontró los huecos H1–H5
  ([matriz](evidencia/matriz-cobertura.md)).
- Pruebas nuevas → `102 passed` ([evidencia](evidencia/episodio-3-pytest.txt)).
- `scripts/verificar_mutaciones.py` → 6 de 6 mutaciones detectadas (M4 reforzada de 1 a 2 fallas)
  ([evidencia](evidencia/episodio-3-mutaciones.txt)).
- `scripts/verificar_matriz.py` → primera ejecución: 6 pruebas sin citar → corregido → 50/50 citadas, 102 passed
  ([evidencia](evidencia/episodio-3-matriz.txt)).
- Comando con `rm -rf` → **denegado por el harness** (regla `deny`).
- Clon limpio en el scratchpad: `git clone` + venv nueva + `pip install -r requirements-dev.txt` → `pip freeze`
  idéntico a `requirements-dev.txt`, `102 passed`.
- PowerShell 5.1.26100: `reservar` → código 0; unidad inválida → código 1; los acentos se ven bien con la salida capturada.
- Ejemplo del README → [ejemplo-cli.txt](evidencia/ejemplo-cli.txt).

**No ejecutado / pendiente**

- No se probó una consola interactiva de cmd o PowerShell con otra página de códigos.
- No se probaron procesos concurrentes (fuera de alcance).
- **Pendiente del humano:** ratificar los episodios, crear el remoto, hacer `git push` (prohibido al agente) y enviar el enlace.

### 2026-11-02 — Episodio 2

**Ejecutado y observado**

- `.venv/Scripts/python -m pytest -q` → 93 passed (antes de ejecutar el procedimiento manual).
- Procedimiento manual, Sesión A → **defecto**: `ya est� reservada` (cp1252 en un pipe de Windows).
- Prueba de regresión nueva → `1 failed (UnicodeDecodeError ... 0xe1)`; tras la corrección → `94 passed`
  ([evidencia](evidencia/episodio-2-pytest.txt)).
- Sesión B en una shell nueva sobre la misma base → activas y canceladas recuperadas, la activa bloquea,
  la cancelada no, el ID siguiente es `#4` ([evidencia](evidencia/persistencia-manual.md)).

**Estado de datos local:** `data/reservas.db` quedó con las 4 reservas de demostración (no se versiona).

**No ejecutado / pendiente**

- No se probó la CLI desde PowerShell ni cmd; solo desde Git Bash y subprocess. (PowerShell: resuelto en el episodio 3.)
- Matriz formal CA/R ↔ pruebas → episodio 3.

### 2026-11-02 — Episodio 1

**Ejecutado y observado**

- `.venv/Scripts/python -c "from zoneinfo import ZoneInfo; ZoneInfo('America/Argentina/Buenos_Aires')"`
  → `ZoneInfoNotFoundError`. Se cambió a UTC−3 fijo (especificación v1.1, D-10).
- `.venv/Scripts/python -m pytest -v` → **80 passed** ([evidencia](evidencia/episodio-1-pytest.txt)).
- `.venv/Scripts/python scripts/verificar_mutaciones.py` → M1: 8 failed, M2: 3 failed;
  código restaurado y verificado con `grep` ([evidencia](evidencia/episodio-1-mutaciones.txt)).

**No ejecutado / pendiente**

- CA-12 en un **proceso nuevo** (solo se probó reabrir la base en el mismo proceso) → episodio 2.
- No hay CLI todavía → episodio 2.

### 2026-10-26 / 2026-10-28 — Fase 0: preparación

**Ejecutado y observado**

- `git init -b main` → repositorio creado.
- `py -m venv .venv` + `pip install pytest` → `pytest==9.1.1` sobre `Python 3.13.5`.
- `pip freeze > requirements-dev.txt` → 6 paquetes fijados.
- `claude --version` → `2.1.311 (Claude Code)`.

**Creado**

- `docs/ESPECIFICACION.md` (v1), `CLAUDE.md`, `.claude/settings.json`,
  `.claude/commands/cerrar-episodio.md`, `data/inventario.json`, `.gitignore`,
  `docs/AGENTE.md`, `docs/DECISIONES.md`, `docs/prompts/episodio-{1,2,3}.md`, `README.md`.

**No ejecutado**

- No hay código de aplicación ni pruebas todavía (a propósito: es trabajo de los episodios).
- La sesión de preparación se interrumpió una vez a mitad de la escritura de
  archivos; se retomó verificando con `find` / `git status` qué había quedado
  escrito antes de continuar.
