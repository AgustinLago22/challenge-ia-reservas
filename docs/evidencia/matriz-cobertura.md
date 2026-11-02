# Matriz de cobertura: criterios y reglas → pruebas

Generada en el episodio 3. Cada referencia `archivo::prueba` es verificable con
`.venv/Scripts/python scripts/verificar_matriz.py`, que extrae las referencias de este archivo,
comprueba que existan y las ejecuta. La salida real está en [`episodio-3-matriz.txt`](episodio-3-matriz.txt) y, tras sumar la web, en [`episodio-4-matriz.txt`](episodio-4-matriz.txt).

## 1. Auditoría inicial: huecos encontrados antes de agregar pruebas

Se comparó cada regla y cada supuesto de `docs/ESPECIFICACION.md` con las 45 funciones de prueba
existentes después del episodio 2 (`pytest --collect-only`).

| Hueco | Qué faltaba | Por qué importa | Cerrado con |
|-------|-------------|-----------------|-------------|
| H1 | Supuesto §5: se puede **cancelar** una reserva activa cuyo horario ya pasó. Ninguna prueba lo ejercitaba. | Una validación de "pasado" mal ubicada en `cancelar` habría pasado desapercibida. | `test_supuesto_se_puede_cancelar_una_reserva_cuyo_horario_ya_paso` |
| H2 | Supuesto §5: sin máximo de **anticipación**. Solo se probaba la duración de varios días. | Un límite de anticipación agregado por error no habría hecho fallar nada. | `test_supuesto_sin_limite_de_anticipacion` |
| H3 | R14: **rollback** si algo falla después de insertar. Solo se probaban rechazos *antes* de insertar. | La atomicidad de `BEGIN IMMEDIATE`/`ROLLBACK` no estaba demostrada. | `test_ca13_error_dentro_de_la_transaccion_deshace_lo_escrito` |
| H4 | R13 desde la consola: `disponibilidad` con entradas inválidas (código 1). | Las validaciones de la consulta solo se probaban en el servicio, no en la CLI. | `test_cli_disponibilidad_entradas_invalidas` |
| H5 | Alcance: el inventario **nunca se modifica**, ni siquiera con `reiniciar-datos`. | Era una regla de `CLAUDE.md` sin verificación. | `test_cli_no_modifica_el_inventario` |
| H6 | Las mutaciones solo cubrían R8 y R10. Al ampliarlas, **R4 quedó detectada por un único caso**. | Una sola prueba que protege una regla es frágil. | Mutaciones M3–M6 y un caso `inicio == fin` en `test_cli_disponibilidad_entradas_invalidas` (M4: de 1 a 2 fallas) |

Resultado: de 94 a **102 casos de prueba**, todos en verde ([episodio-3-pytest.txt](episodio-3-pytest.txt)).
En el episodio 4 se agregaron 26 casos de la web: **128 en total** ([episodio-4-pytest.txt](episodio-4-pytest.txt)). Los conteos de fallas por mutación de la sección 3 son los del episodio 3; los vigentes están en [episodio-4-mutaciones.txt](episodio-4-mutaciones.txt).

## 2. Criterios de aceptación

| CA | Criterio (resumen) | Pruebas |
|----|--------------------|---------|
| CA-01 | Crear reserva válida | `tests/test_reservas.py::test_ca01_crear_reserva_valida`, `tests/test_reservas.py::test_ca01_ids_unicos_y_crecientes`, `tests/test_reservas.py::test_ca01_solicitante_se_guarda_sin_espacios_extremos`, `tests/test_cli.py::test_cli_ejemplo_del_enunciado` |
| CA-02 | Rechazar superposición en la misma unidad | `tests/test_reservas.py::test_ca02_rechaza_superposicion_misma_unidad`, `tests/test_cli.py::test_cli_ejemplo_del_enunciado` |
| CA-03 | Límites consecutivos permitidos | `tests/test_reservas.py::test_ca03_limites_consecutivos_permitidos`, `tests/test_reservas.py::test_ca03_encadenar_tres_turnos_consecutivos`, `tests/test_superposicion.py::test_se_superponen` |
| CA-04 | Unidades distintas simultáneas | `tests/test_reservas.py::test_ca04_unidades_distintas_simultaneas`, `tests/test_cli.py::test_cli_ejemplo_del_enunciado` |
| CA-05 | Unidad desconocida | `tests/test_reservas.py::test_ca05_rechaza_unidad_desconocida`, `tests/test_cli.py::test_cli_entradas_invalidas` |
| CA-06 | Solicitante vacío o solo espacios | `tests/test_reservas.py::test_ca06_rechaza_solicitante_vacio_o_solo_espacios`, `tests/test_cli.py::test_cli_entradas_invalidas` |
| CA-07 | Fechas inválidas e inicio ≥ fin | `tests/test_reservas.py::test_ca07_rechaza_fechas_invalidas`, `tests/test_reservas.py::test_ca07_rechaza_inicio_no_anterior_al_fin`, `tests/test_reservas.py::test_ca07_reserva_de_varios_dias_es_valida`, `tests/test_cli.py::test_cli_entradas_invalidas` |
| CA-08 | Inicio en el pasado | `tests/test_reservas.py::test_ca08_rechaza_inicio_en_el_pasado`, `tests/test_reservas.py::test_ca08_permite_inicio_en_el_minuto_actual`, `tests/test_reservas.py::test_ca08_los_segundos_del_reloj_no_rechazan_el_minuto_actual`, `tests/test_reservas.py::test_ca08_se_puede_consultar_disponibilidad_en_el_pasado` |
| CA-09 | Disponibilidad con las mismas reglas | `tests/test_reservas.py::test_ca09_disponibilidad_usa_las_mismas_reglas`, `tests/test_reservas.py::test_ca09_consulta_y_creacion_coinciden`, `tests/test_reservas.py::test_ca09_disponibilidad_valida_entradas`, `tests/test_reservas.py::test_ca09_disponibilidad_de_todas_las_unidades`, `tests/test_cli.py::test_cli_disponibilidad`, `tests/test_cli.py::test_cli_disponibilidad_entradas_invalidas` |
| CA-10 | Cancelar conserva el registro y libera el horario | `tests/test_reservas.py::test_ca10_cancelar_conserva_datos_y_libera_horario`, `tests/test_reservas.py::test_ca10_cancelar_solo_libera_esa_reserva` |
| CA-11 | Cancelar inexistente, ya cancelada o con ID inválido | `tests/test_reservas.py::test_ca11_cancelar_inexistente_se_rechaza`, `tests/test_reservas.py::test_ca11_cancelar_dos_veces_se_rechaza_sin_cambios`, `tests/test_reservas.py::test_ca11_cancelar_con_id_invalido`, `tests/test_cli.py::test_cli_cancelar_errores` |
| CA-12 | Persistencia tras detener y reiniciar | `tests/test_persistencia.py::test_ca12_reabrir_recupera_activas_y_canceladas`, `tests/test_persistencia.py::test_abrir_base_existente_no_pierde_datos`, `tests/test_cli.py::test_ca12_persistencia_tras_reiniciar_en_proceso_nuevo` + [procedimiento manual](persistencia-manual.md) |
| CA-13 | Un rechazo no modifica datos | `tests/test_reservas.py::test_ca13_rechazos_no_modifican_datos`, `tests/test_reservas.py::test_ca13_conflicto_no_deja_la_transaccion_abierta`, `tests/test_reservas.py::test_ca13_error_dentro_de_la_transaccion_deshace_lo_escrito` |
| CA-14 | Web local con las mismas reglas (episodio 4) | `tests/test_web.py::test_ca14_ejemplo_del_enunciado_por_http`, `tests/test_web.py::test_ca14_entradas_invalidas_devuelven_400`, `tests/test_web.py::test_ca14_cuerpos_invalidos`, `tests/test_web.py::test_ca14_disponibilidad`, `tests/test_web.py::test_ca14_cancelar`, `tests/test_web.py::test_ca14_listar_con_filtros`, `tests/test_web.py::test_ca14_persistencia_al_reiniciar_el_servidor`, `tests/test_web.py::test_ca14_web_y_consola_comparten_los_datos`, `tests/test_web.py::test_ca14_info_y_unidades`, `tests/test_web.py::test_ca14_pagina_principal`, `tests/test_web.py::test_ca14_proceso_real_python_m_reservas_web` |

## 3. Reglas de negocio

| Regla | Pruebas | Mutación que la rompe → fallas |
|-------|---------|--------------------------------|
| R1 unidad conocida | `tests/test_reservas.py::test_ca05_rechaza_unidad_desconocida`, `tests/test_reservas.py::test_listar_valida_filtros` | — |
| R2 solicitante | `tests/test_reservas.py::test_ca06_rechaza_solicitante_vacio_o_solo_espacios` | M5 → 4 |
| R3 formato de fecha | `tests/test_reservas.py::test_ca07_rechaza_fechas_invalidas`, `tests/test_cli.py::test_cli_ahora_invalido` | — |
| R4 inicio < fin | `tests/test_reservas.py::test_ca07_rechaza_inicio_no_anterior_al_fin`, `tests/test_cli.py::test_cli_disponibilidad_entradas_invalidas` | M4 → 2 |
| R5 no en el pasado | `tests/test_reservas.py::test_ca08_rechaza_inicio_en_el_pasado`, `tests/test_reservas.py::test_supuesto_se_puede_cancelar_una_reserva_cuyo_horario_ya_paso` | — |
| R6 intervalos semiabiertos | `tests/test_superposicion.py::test_se_superponen` | M1 → 10 |
| R7 sin superposición de activas | `tests/test_reservas.py::test_ca02_rechaza_superposicion_misma_unidad` | M3 → 12 |
| R8 consecutivos permitidos | `tests/test_reservas.py::test_ca03_limites_consecutivos_permitidos` | M1 → 10 |
| R9 unidades distintas | `tests/test_reservas.py::test_ca04_unidades_distintas_simultaneas` | — |
| R10 cancelada no bloquea | `tests/test_reservas.py::test_ca10_cancelar_conserva_datos_y_libera_horario`, `tests/test_persistencia.py::test_ca12_reabrir_recupera_activas_y_canceladas` | M2 → 4 |
| R11 cancelar conserva | `tests/test_reservas.py::test_ca10_cancelar_conserva_datos_y_libera_horario` | M6 → 7 |
| R12 cancelación inválida | `tests/test_reservas.py::test_ca11_cancelar_inexistente_se_rechaza`, `tests/test_reservas.py::test_ca11_cancelar_dos_veces_se_rechaza_sin_cambios` | — |
| R13 misma regla al consultar | `tests/test_reservas.py::test_ca09_consulta_y_creacion_coinciden` | M1 → 10 (rompe ambas a la vez) |
| R14 rechazo sin cambios | `tests/test_reservas.py::test_ca13_rechazos_no_modifican_datos`, `tests/test_reservas.py::test_ca13_error_dentro_de_la_transaccion_deshace_lo_escrito` | — |
| R15 IDs únicos, sin reutilizar | `tests/test_reservas.py::test_ca01_ids_unicos_y_crecientes`, `tests/test_persistencia.py::test_ca12_reabrir_recupera_activas_y_canceladas` | — |

## 4. Controles de la web local (episodio 4)

| Control | Pruebas | Mutación |
|---------|---------|----------|
| Solo escucha en `127.0.0.1` | `tests/test_web.py::test_ca14_solo_escucha_en_localhost` | — |
| Rechaza un `Host` ajeno (DNS rebinding) | `tests/test_web.py::test_ca14_rechaza_host_ajeno` | — |
| No muestra HTML del usuario (`textContent`, sin `innerHTML`) | `tests/test_web.py::test_ca14_la_pagina_no_inserta_html_del_usuario` | — |
| No hay reinicio de datos por la web; rutas desconocidas → 404 | `tests/test_web.py::test_ca14_rutas_inexistentes_y_sin_reinicio_de_datos` | — |
| Puerto ocupado → error claro (defecto de Windows corregido) | `tests/test_web.py::test_ca14_puerto_ocupado_da_error_claro` | — |
| Lee el cuerpo antes de responder, también en los rechazos (D-24) | `tests/test_web.py::test_ca14_rechazos_con_cuerpo_responden_sin_cortar_la_conexion`, `tests/test_web.py::test_ca14_cuerpo_demasiado_grande` | — |
| 409 ante un conflicto | `tests/test_web.py::test_ca14_ejemplo_del_enunciado_por_http`, `tests/test_web.py::test_ca14_cancelar` | M7 → 3 |

## 5. Alcance funcional (§2) sin un CA propio

| Funcionalidad | Pruebas |
|---------------|---------|
| Leer el inventario precargado | `tests/test_inventario.py::test_inventario_precargado_tiene_las_cinco_unidades`, `tests/test_inventario.py::test_inventario_invalido`, `tests/test_inventario.py::test_inventario_inexistente`, `tests/test_cli.py::test_cli_unidades` |
| Listar el historial con filtros | `tests/test_cli.py::test_cli_listar_filtros`, `tests/test_reservas.py::test_listar_valida_filtros` |
| Orden del historial (v1.3) | `tests/test_reservas.py::test_listar_ordenado`, `tests/test_reservas.py::test_listar_orden_por_defecto_es_creacion_y_se_combina_con_filtros`, `tests/test_reservas.py::test_listar_orden_invalido`, `tests/test_cli.py::test_cli_listar_ordenado`, `tests/test_web.py::test_ca14_historial_ordenado` |
| Reinicio de datos con confirmación | `tests/test_reservas.py::test_reiniciar_datos_exige_confirmacion`, `tests/test_cli.py::test_cli_reiniciar_datos_sin_confirmar_no_borra` |

Supuestos de §5 con prueba: duración de varios días (`test_ca07_reserva_de_varios_dias_es_valida`),
sin límite de anticipación (`tests/test_reservas.py::test_supuesto_sin_limite_de_anticipacion`), reinicio con confirmación
(`tests/test_cli.py::test_cli_reiniciar_datos_sin_confirmar_no_borra`), inventario de solo lectura
(`tests/test_cli.py::test_cli_no_modifica_el_inventario`), salida UTF-8 (`tests/test_cli.py::test_cli_salida_utf8_sin_configurar_el_entorno`).

**Sin cobertura automática (declarado):** la zona horaria real del reloj por defecto (`ahora_local`)
no se prueba, porque depende de la hora de la máquina; todas las pruebas inyectan el reloj. La
concurrencia entre procesos simultáneos está fuera de alcance.
