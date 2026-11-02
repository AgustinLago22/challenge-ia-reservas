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
| D-14 | Códigos de salida de la CLI: 0 = éxito, 1 = rechazo de negocio, 2 = uso incorrecto (argparse). Consultar una unidad ocupada devuelve 0. | Se puede usar desde scripts; una consulta respondida es una operación exitosa aunque la respuesta sea "ocupada". | Devolver 1 cuando está ocupada. | Documentado en el README y en el docstring de `__main__.py`. |
| D-15 | Variable `RESERVAS_AHORA` para fijar el "ahora" desde la consola. | Las pruebas de extremo a extremo y el ejemplo del README tienen que dar lo mismo cualquier día (`CLAUDE.md`: el reloj es inyectable). | Usar fechas muy futuras con el reloj real. | Solo para pruebas y demos; sin la variable se usa la hora real UTC−3. |
| D-16 | La CLI fuerza UTF-8 en stdout y stderr. | Defecto observado: `ya est� reservada` con la salida redirigida en Windows. | Pedir al usuario que configure `PYTHONUTF8=1`. | En una consola de Windows se ve igual; en archivos o pipes llega UTF-8. Si una terminal espera otra codificación, los acentos se verían mal. |
| D-17 | `reiniciar-datos` sin `--confirmar` no borra y devuelve 1. El reinicio hace `DELETE` de filas, pero no reinicia el contador de IDs (`AUTOINCREMENT`). | Proteger contra el borrado accidental; un ID nunca se reutiliza, ni siquiera tras reiniciar (R15). | Borrar el archivo `.db`. | Tras reiniciar, la próxima reserva no vuelve a ser la `#1`. |

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
- **Contexto suministrado:** igual que el episodio 1 + código del episodio 1 (commit `f34c873`).
- **Extracto de instrucción:** `docs/prompts/episodio-2.md` («La CLI no debe tener lógica de negocio
  propia… Pruebas de extremo a extremo con subprocess… procedimiento manual reproducible. Ejecutalo vos
  y pegá la salida observada real»).
- **Acción / resultado del agente:**
  1. Implementó `reservas/__main__.py` (6 subcomandos) y `tests/test_cli.py`, con cada llamada como
     proceso nuevo. Resultado: `93 passed`.
  2. Ejecutó el procedimiento manual sobre `data/reservas.db`, con la base real.
     **Encontró un defecto que las pruebas no veían:** `ya est� reservada`. Las pruebas no lo
     detectaban porque fijaban `PYTHONIOENCODING=utf-8`.
  3. **Corrección:** escribió primero una prueba que lo reproduce **sin** configurar la codificación →
     `1 failed (UnicodeDecodeError ... 0xe1)`; luego agregó `_salida_utf8()` → `94 passed` (D-16).
  4. Repitió el paso manual fallido y ejecutó la Sesión B (reinicio en una shell nueva): todo coincidió con lo esperado.
- **Archivos tocados:** `reservas/__main__.py`, `tests/test_cli.py`, `docs/evidencia/persistencia-manual.md`.
- **Revisión realizada (agente, modo automático):** la CLI solo llama a métodos de `ServicioReservas`
  (no importa `se_superponen`); `reiniciar-datos` sin `--confirmar` no borra (prueba
  `test_cli_reiniciar_datos_sin_confirmar_no_borra` y paso manual); las 93 pruebas previas no crearon
  `data/reservas.db` (`ls data/` → solo `inventario.json`).
- **Decisión:** **corregir y aceptar**. La regla de negocio era correcta, pero la salida en Windows no;
  se aceptó después de la corrección y de la prueba de regresión.
- **Ratificación humana:** [COMPLETAR POR EL HUMANO tras revisar el commit]
- **Evidencia:** [`episodio-2-pytest.txt`](evidencia/episodio-2-pytest.txt),
  [`persistencia-manual.md`](evidencia/persistencia-manual.md),
  prueba `test_cli_salida_utf8_sin_configurar_el_entorno`, commit `episodio 2: …` (ver `git log`).

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
