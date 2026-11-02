# Progreso del proyecto

> Archivo versionado de retención de progreso. El agente lo lee al empezar cada tarea
> y lo actualiza al terminar (ver `CLAUDE.md`). Cada entrada distingue lo
> **ejecutado y observado** de lo **afirmado, no ejecutado**.

## Estado actual

| Fase | Estado |
|------|--------|
| 0. Preparación del entorno y del agente | Completa (pendiente commit inicial) |
| Episodio 1. Dominio + persistencia SQLite + pruebas de reglas | No iniciado |
| Episodio 2. CLI + prueba de persistencia en proceso nuevo | No iniciado |
| Episodio 3. Auditoría de cobertura CA ↔ pruebas + sección Solución del README | No iniciado |

**Próximo paso:** abrir una sesión nueva de Claude Code en la raíz del repo y pegar
el prompt de `docs/prompts/episodio-1.md`.

## Decisiones abiertas

- Ninguna. Los supuestos (zona horaria, formato, fechas pasadas, sin límites de
  duración) están cerrados en `docs/ESPECIFICACION.md` §5.

## Bitácora

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
