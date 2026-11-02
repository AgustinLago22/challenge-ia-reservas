# Progreso del proyecto

> Archivo versionado de retención de progreso. El agente lo lee al empezar cada tarea
> y lo actualiza al terminar (ver `CLAUDE.md`). Cada entrada distingue lo
> **ejecutado y observado** de lo **afirmado, no ejecutado**.

## Estado actual

| Fase | Estado |
|------|--------|
| 0. Preparación del entorno y del agente | Completa (commit `f0e4131`) |
| Episodio 1. Dominio + persistencia SQLite + pruebas de reglas | Completo (commit `f34c873`) |
| Episodio 2. CLI + prueba de persistencia en proceso nuevo | Completo |
| Episodio 3. Auditoría de cobertura CA ↔ pruebas + sección Solución del README | No iniciado |

**Próximo paso:** episodio 3 (`docs/prompts/episodio-3.md`): matriz de cobertura CA/R ↔ pruebas y sección Solución del README.

## Decisiones abiertas

- Ninguna. Desde el 2026-11-02 el humano autorizó el modo automático con commits (D-09).

## Bitácora

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

- No se probó la CLI desde PowerShell ni cmd; solo desde Git Bash y subprocess.
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
