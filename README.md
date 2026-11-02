# Sistema de reservas de equipos de laboratorio

Challenge IA — Tópicos Avanzados de Ingeniería de Software. Solución local (Python + CLI + SQLite)
construida con un agente de programación (Claude Code).

## 1. Especificación

Resumen: herramienta de consola para consultar disponibilidad, reservar y cancelar
unidades de equipos de laboratorio sin superposiciones y sin perder el historial.

Especificación completa, con reglas R1–R15, supuestos (zona horaria, formato de fecha,
fechas pasadas, límites) y criterios de aceptación CA-01–CA-13:
**[docs/ESPECIFICACION.md](docs/ESPECIFICACION.md)**. La versión inicial y sus cambios
se pueden recuperar con `git log -- docs/ESPECIFICACION.md`.

## 2. Solución

> Se completa en el episodio 3 (estructura, instalación, comandos, ejemplo real, persistencia y limitaciones).

Requisitos previos: Python 3.13, Git.

```bash
py -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest -v
```

## 3. Preparación del agente

Entorno, modelo, instrucciones, contexto, permisos, adaptaciones y retención del progreso:
**[docs/AGENTE.md](docs/AGENTE.md)**. Progreso versionado: [docs/PROGRESO.md](docs/PROGRESO.md).

## 4. Registro de decisiones y delegación

Decisiones técnicas y los tres episodios de delegación: **[docs/DECISIONES.md](docs/DECISIONES.md)**.
Evidencia ejecutada: [docs/evidencia/](docs/evidencia/).
