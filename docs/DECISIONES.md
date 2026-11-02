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

| D-09 | El humano autoriza al agente a trabajar en automático, incluidos los commits, en 2 o más commits separados (2026-11-02). | Pedido explícito del autor: «te voy a dejar que hagas todo en automático… Vas a hacer los commits solo… en 2-3 commits por lo menos». | Aprobar cada paso a mano (plan original de `CLAUDE.md`). | Cambia el control de "aprobación previa" a "revisión posterior por commit". El agente toma la decisión operativa de aceptar o corregir y la registra; la **ratificación humana** queda como campo aparte. `git push` sigue prohibido. |
| D-10 | Zona horaria con desfase fijo UTC−3 en lugar de `zoneinfo`. | Ejecutado: `ZoneInfo('America/Argentina/Buenos_Aires')` lanza `ZoneInfoNotFoundError` en Windows sin `tzdata`. | Agregar la dependencia `tzdata`. | Sin dependencias nuevas. Sería incorrecto si Argentina volviera a aplicar horario de verano. Especificación v1.1. |
| D-11 | Separar en capas `dominio` (reglas puras) → `servicio` (casos de uso) → `repositorio` (SQLite), y en el episodio 2 → CLI. | La regla de superposición se prueba sin base de datos, y la CLI no puede duplicar lógica. | Un único módulo. | Cuatro archivos chicos; las pruebas apuntan al servicio. |
| D-12 | El filtrado de conflictos se hace en Python con `se_superponen` sobre las activas de la unidad, no en SQL. | Garantiza una sola fórmula de superposición (R13, `CLAUDE.md`). | `WHERE inicio < ? AND ? < fin` en SQL (sería una segunda copia de la regla). | Con pocas reservas por unidad el costo es despreciable; no escala a millones (fuera de alcance). |
| D-13 | Verificar las pruebas con mutaciones (`scripts/verificar_mutaciones.py`). | Que las pruebas pasen no demuestra que detecten errores. | Confiar en que estén en verde. | Evidencia de que romper R8 o R10 hace fallar las pruebas. |

## Episodios de delegación

Formato por episodio: objetivo y requisito → contexto y extracto de instrucción →
acción o resultado del agente → decisión humana (aceptar / corregir / rechazar) y
motivo → evidencia (archivo, commit, prueba).

### Episodio 1 — Dominio, persistencia y pruebas de reglas

- **Objetivo y requisitos:** R1–R15; CA-01 a CA-11 y CA-13.
- **Contexto suministrado:** `CLAUDE.md`, `docs/ESPECIFICACION.md`, `docs/PROGRESO.md`, `data/inventario.json`.
- **Extracto de instrucción:** el prompt de `docs/prompts/episodio-1.md` («implementar el núcleo… la
  función se_superponen exactamente como dice CLAUDE.md… Pruebas pytest… cada una citando su CA»),
  más la instrucción del humano «hacé todo en automático» (D-09). Por eso se omitió el paso
  «mostrame el diseño y esperá mi OK»: el diseño quedó registrado en D-11 y D-12.
- **Acción / resultado del agente:**
  1. Antes de codificar comprobó el riesgo de zona horaria: `ZoneInfo(...)` → `ZoneInfoNotFoundError`.
     **Corrección de la especificación** a v1.1 y de `CLAUDE.md` (D-10).
  2. Implementó `reservas/dominio.py`, `inventario.py`, `repositorio.py` y `servicio.py`, y 80 pruebas
     (`tests/`). Primera ejecución: `80 passed`.
  3. Verificó por mutaciones (D-13): `<=` en `se_superponen` → 8 fallan; canceladas bloqueando → 3 fallan.
  4. **Autocorrección de la verificación:** después de las mutaciones usó `git diff --quiet` para
     confirmar que el código estaba restaurado, pero `git diff` no compara archivos sin seguimiento.
     Lo reemplazó por una búsqueda con `grep` del texto original (encontrado en `dominio.py:86`).
- **Archivos tocados:** `reservas/{__init__,dominio,inventario,repositorio,servicio}.py`,
  `tests/{__init__,conftest,test_superposicion,test_reservas,test_persistencia,test_inventario}.py`,
  `pyproject.toml`, `scripts/verificar_mutaciones.py`, `docs/ESPECIFICACION.md` (v1.1), `CLAUDE.md`.
- **Revisión realizada (agente, modo automático):** se revisó que `se_superponen` sea la única
  comparación de intervalos (`grep "<=" reservas/dominio.py` → 0); que crear y consultar llamen a
  `_buscar_conflictos`; que el único `DELETE` esté en `borrar_todo`; que las pruebas usen `tmp_path`
  (fixture autouse `_aislar_base_real`).
- **Decisión:** **aceptar con corrección**. Se corrigió la especificación (zona horaria) antes de
  implementar; el código se aceptó sin cambios porque pasó las pruebas y las mutaciones.
- **Ratificación humana:** [COMPLETAR POR EL HUMANO tras revisar el commit]
- **Evidencia:** [`episodio-1-pytest.txt`](evidencia/episodio-1-pytest.txt),
  [`episodio-1-mutaciones.txt`](evidencia/episodio-1-mutaciones.txt), commit `episodio 1: …` (ver `git log`).

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
