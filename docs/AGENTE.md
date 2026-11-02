# Preparación del agente

## Entorno y modelo

| Dato | Valor | Cómo se obtuvo |
|------|-------|----------------|
| Harness | Claude Code (CLI), existente, no construido | — |
| Versión | `2.1.311 (Claude Code)` | `claude --version` (2026-10-26) |
| Modelo | Claude Opus 5.5, ID `claude-opus-5-5` | Informado por el entorno de la sesión; la configuración global tiene `"model": "opus"` |
| Sistema | Windows 11, Git Bash como shell del agente | Entorno de la sesión |
| Python / pytest | 3.13.5 / 9.1.1 | `.venv/Scripts/python --version`, `pip freeze` |

**Función:** un único agente que lee el repositorio, edita archivos y ejecuta comandos
(pytest, la CLI, git de solo lectura) con herramientas reales sobre el repo.
**Motivo de la elección:** actúa directamente sobre el repositorio, ya estaba
instalado y permite versionar instrucciones (`CLAUDE.md`), permisos
(`.claude/settings.json`) y comandos propios (`.claude/commands/`).

## Instrucciones y configuración usadas

| Archivo | Rol |
|---------|-----|
| [`CLAUDE.md`](../CLAUDE.md) | Instrucciones del proyecto; Claude Code las carga automáticamente en cada sesión. |
| [`.claude/settings.json`](../.claude/settings.json) | Permisos: permitido / requiere aprobación / denegado. |
| [`.claude/commands/cerrar-episodio.md`](../.claude/commands/cerrar-episodio.md) | Comando `/cerrar-episodio N`: procedimiento fijo de cierre con evidencia. |
| [`docs/prompts/`](prompts/) | Prompts exactos usados en cada episodio. |

**Configuración externa al repositorio (saneada):** `~/.claude/settings.json` del
autor define `"model": "opus"` y hooks de una herramienta local de terceros
(`SessionStart`, `UserPromptSubmit`, `Stop`) que no modifican archivos del proyecto.
No se versionan porque son personales; `.claude/settings.local.json` está en `.gitignore`.

## Contexto suministrado y excluido

- **Suministrado:** especificación, inventario, `CLAUDE.md`, `docs/PROGRESO.md`, el código y las pruebas del repo.
- **Excluido:** el PDF del enunciado (se usó solo en la sesión de preparación; no se
  versiona por estar en `.gitignore`), `data/*.db` (lectura denegada al agente),
  archivos `.env`, internet (`WebFetch` y `WebSearch` denegados), conversaciones completas.

## Permisos, controles y aprobaciones

| Nivel | Acciones |
|-------|----------|
| Permitido sin preguntar | Leer el repo; editar `reservas/`, `tests/`, `docs/PROGRESO.md`, `docs/DECISIONES.md`, `docs/evidencia/`; ejecutar `pytest` y la CLI; `git status/diff/log/show`. |
| Requiere aprobación humana | `git add`, `git commit`, `pip`, editar la especificación, `CLAUDE.md`, `README.md`, el inventario o `.claude/`. |
| Denegado | `git push`, `git reset --hard`, `rm -rf`, `curl`/`wget`, acceso web, leer `data/*.db` y `.env`. |

Además, el prompt de cada episodio pide que el agente muestre el diseño antes de codificar y se
detenga antes de cada commit. Lo que revisa el humano antes de aceptar está en la lista al
final de cada archivo de `docs/prompts/`.

> **Modo de permisos realmente usado:** la sesión de Claude Code de este trabajo corrió en
> modo *bypass permissions* (el harness lo informa al inicio de la sesión). En ese modo el
> harness **no muestra** los pedidos de aprobación de la lista "requiere aprobación", así que
> esa lista funciona como política documentada y no como bloqueo técnico. El control humano
> efectivo es: (1) la autorización explícita del autor para trabajar en automático (ver
> `docs/DECISIONES.md`, D-09), (2) los límites escritos en `CLAUDE.md`, y (3) la revisión
> posterior de cada commit, que queda separado por episodio. Para que el harness pida las
> aprobaciones hay que ejecutar `claude` en modo normal.

### Controles efectivamente aplicados (evidencia)

| Control | Qué pasó | Evidencia |
|---------|----------|-----------|
| Regla `deny: Bash(rm -rf:*)` | En el episodio 3, el harness **denegó** un comando que empezaba con `rm -rf` (preparar un clon limpio). El agente lo repitió con una carpeta nueva, sin borrar. Esto demuestra que las reglas `deny` se aplican incluso en modo *bypass*. | `docs/DECISIONES.md`, episodio 3, paso 5 |
| `git push` prohibido | No se hizo ningún push; el repositorio no tiene remoto configurado. | `git remote -v` vacío |
| Autorización para commits | El humano autorizó los commits automáticos (D-09). Se hizo un commit por episodio para que la revisión posterior sea por partes. | `git log` |
| Pruebas aisladas de la base real | Tras 93 pruebas, `data/reservas.db` no existía. | `docs/PROGRESO.md`, episodio 2 |
| Honestidad del registro | Los campos de decisión humana quedaron separados ("Ratificación humana") en lugar de inventarlos. | `docs/DECISIONES.md` |

## Adaptaciones específicas comprobables

1. **Regla de turnos consecutivos** (`CLAUDE.md` §"Regla de intervalos"): una sola
   función `se_superponen` con `<` estricto (`reservas/dominio.py`), y crear y consultar comparten
   `_buscar_conflictos` (`reservas/servicio.py`). **Evidencia de uso:** las pruebas `test_ca03_*`; la
   mutación M1 (`<` → `<=`) hace fallar 10 pruebas ([evidencia](evidencia/episodio-3-mutaciones.txt)).
2. **Procedimiento de persistencia** (`CLAUDE.md` §"Procedimiento de persistencia"):
   cancelar con `UPDATE`, transacción `BEGIN IMMEDIATE`, pruebas sobre `tmp_path`, y verificación en un proceso
   nuevo. **Evidencia de uso:** `repositorio.py` (único `DELETE` en `borrar_todo`); la mutación M6
   (cancelar con `DELETE`) hace fallar 7 pruebas; `test_ca12_persistencia_tras_reiniciar_en_proceso_nuevo`;
   el [procedimiento manual](evidencia/persistencia-manual.md).
3. **Fechas** (`CLAUDE.md` §"Fechas y reloj"): la instrucción decía `zoneinfo`. Se comprobó que fallaba en Windows y
   **se adaptó la instrucción** (especificación v1.1, D-10). El cambio es visible en `git log -p -- CLAUDE.md`.
4. **Comando `/cerrar-episodio`**: genera `docs/evidencia/episodio-N-pytest.txt` con salida real, sin editar
   (archivos de los episodios 1, 2 y 3).

## Retención del progreso

[`docs/PROGRESO.md`](PROGRESO.md) es versionado; el agente lo lee al empezar y lo actualiza al terminar.
Las decisiones quedan en [`docs/DECISIONES.md`](DECISIONES.md).
