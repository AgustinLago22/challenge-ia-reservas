# Registro de decisiones y delegación

## Decisiones técnicas

| ID | Decisión | Motivo | Alternativas descartadas | Consecuencias |
|----|----------|--------|--------------------------|---------------|
| D-01 | Python 3.13, solo biblioteca estándar en la app. | Reproducible sin instalar nada más que pytest; Python ya estaba instalado. | Node/TypeScript; FastAPI. | No hay API HTTP; la interfaz es una consola. |
| D-02 | Interfaz CLI (`python -m reservas`). | La consigna acepta consola; una página web (p. ej. Three.js) no aporta a las reglas evaluadas y agrega superficie de errores. | API local; web. | Las pruebas de extremo a extremo se hacen con `subprocess`. |
| D-03 | SQLite en `data/reservas.db`. | Viene con Python, transacciones atómicas (R14), sobrevive reinicios. | Archivo JSON (riesgo de escritura parcial, sin transacciones). | Archivo binario; se excluye de Git. |
| D-04 | Intervalos semiabiertos `[inicio, fin)` con una única función `se_superponen`. | Permite límites consecutivos (R8) y garantiza que reservar y consultar usen la misma regla (R13). | Intervalos cerrados (rechazaría 11:00–12:00). | Regla fijada en `CLAUDE.md` como adaptación específica. |
| D-05 | Zona horaria fija `America/Argentina/Buenos_Aires`, formato `YYYY-MM-DDTHH:MM`. | Un solo laboratorio; evita ambigüedades y comillas en consola. | Guardar en UTC con conversión. | No se admite otro formato ni otra zona. |
| D-06 | Rechazar creación con inicio en el pasado; permitir consultar y cancelar en el pasado. | Evita reservas sin sentido sin impedir el registro administrativo. | Permitir todo pasado. | Requiere reloj inyectable para pruebas deterministas. |
| D-07 | Sin límite de duración ni de anticipación. | La consigna no lo pide; menos reglas ocultas. | Máx. 8 h / 30 días. | Documentado como supuesto en la especificación. |
| D-08 | Cancelar es `UPDATE` de estado, nunca `DELETE`. | Conservar historial (R11). | Borrar o mover a otra tabla. | El listado muestra activas y canceladas. |

> El agente agrega nuevas decisiones (D-09…) al final de esta tabla.

## Episodios de delegación

Formato por episodio: objetivo y requisito → contexto y extracto de instrucción →
acción o resultado del agente → decisión humana (aceptar / corregir / rechazar) y
motivo → evidencia (archivo, commit, prueba).

### Episodio 1 — Dominio, persistencia y pruebas de reglas

- **Objetivo y requisitos:** R1–R15; CA-01 a CA-11 y CA-13.
- **Contexto suministrado:** `CLAUDE.md`, `docs/ESPECIFICACION.md`, `docs/PROGRESO.md`, `data/inventario.json`.
- **Extracto de instrucción:** ver `docs/prompts/episodio-1.md`.
- **Acción / resultado del agente:** [COMPLETA EL AGENTE]
- **Archivos tocados:** [COMPLETA EL AGENTE]
- **Revisión humana realizada:** [COMPLETAR POR EL HUMANO]
- **Decisión humana:** [COMPLETAR POR EL HUMANO]
- **Motivo:** [COMPLETAR POR EL HUMANO]
- **Evidencia:** `docs/evidencia/episodio-1-pytest.txt`, commit [COMPLETAR]

### Episodio 2 — CLI y persistencia tras reinicio

- **Objetivo y requisitos:** CLI de consultar / reservar / cancelar / listar / reiniciar; CA-12.
- **Contexto suministrado:** igual que el episodio 1 + código del episodio 1.
- **Extracto de instrucción:** ver `docs/prompts/episodio-2.md`.
- **Acción / resultado del agente:** [COMPLETA EL AGENTE]
- **Archivos tocados:** [COMPLETA EL AGENTE]
- **Revisión humana realizada:** [COMPLETAR POR EL HUMANO]
- **Decisión humana:** [COMPLETAR POR EL HUMANO]
- **Motivo:** [COMPLETAR POR EL HUMANO]
- **Evidencia:** `docs/evidencia/episodio-2-pytest.txt`, `docs/evidencia/persistencia-manual.md`, commit [COMPLETAR]

### Episodio 3 — Auditoría de cobertura y documentación de la solución

- **Objetivo y requisitos:** cada CA-xx cubierto por al menos una prueba; README §Solución.
- **Contexto suministrado:** todo el repo.
- **Extracto de instrucción:** ver `docs/prompts/episodio-3.md`.
- **Acción / resultado del agente:** [COMPLETA EL AGENTE]
- **Archivos tocados:** [COMPLETA EL AGENTE]
- **Revisión humana realizada:** [COMPLETAR POR EL HUMANO]
- **Decisión humana:** [COMPLETAR POR EL HUMANO]
- **Motivo:** [COMPLETAR POR EL HUMANO]
- **Evidencia:** `docs/evidencia/episodio-3-pytest.txt`, `docs/evidencia/matriz-cobertura.md`, commit [COMPLETAR]
