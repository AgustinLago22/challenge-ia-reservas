# Prompt — Episodio 1 (pegar tal cual en una sesión nueva de Claude Code)

```
Episodio 1. Leé CLAUDE.md, docs/PROGRESO.md y docs/ESPECIFICACION.md antes de hacer nada.

Objetivo: implementar el núcleo del sistema de reservas (sin CLI todavía).

1. Paquete reservas/ con:
   - carga del inventario desde data/inventario.json,
   - validaciones R1–R5 con mensajes de error claros en español,
   - la función se_superponen exactamente como dice CLAUDE.md,
   - un repositorio SQLite (ruta por parámetro) con el procedimiento de persistencia de CLAUDE.md,
   - un servicio con: consultar_disponibilidad, crear_reserva, cancelar_reserva, listar_reservas.
     El "ahora" entra por un reloj inyectable.
2. Pruebas pytest en tests/ que cubran CA-01 a CA-11 y CA-13, cada una citando su CA.
   Base de datos siempre en tmp_path.
3. Agregá una prueba de reapertura: crear reservas, cancelar una, cerrar, abrir una
   instancia nueva sobre el mismo archivo y verificar estados (anticipo de CA-12).

Antes de escribir código, mostrame en 5–10 líneas el diseño (módulos y funciones) y esperá mi OK.
Al terminar ejecutá /cerrar-episodio 1. No hagas commit sin mi aprobación.
```

## Qué revisa el humano antes de aceptar

- [ ] `se_superponen` usa `<` estricto y es la única que decide la superposición.
- [ ] Crear y consultar llaman a la misma función de búsqueda de conflictos.
- [ ] No hay `DELETE` fuera del reinicio de datos.
- [ ] Las pruebas usan `tmp_path` y no tocan `data/reservas.db`.
- [ ] La salida de pytest en `docs/evidencia/episodio-1-pytest.txt` coincide con lo que veo al correrlo yo.
