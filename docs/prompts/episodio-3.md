# Prompt — Episodio 3

```
Episodio 3. Leé CLAUDE.md y docs/PROGRESO.md antes de hacer nada.

Objetivo: auditar que la entrega cumple la especificación y documentar la solución.

1. Generá docs/evidencia/matriz-cobertura.md: una tabla con cada CA-01..CA-13 y cada
   regla R1..R15 → prueba(s) que la cubren (archivo::nombre) → resultado observado.
   Marcá explícitamente cualquier CA o regla SIN prueba. No escribas pruebas nuevas todavía:
   primero mostrame la matriz con los huecos.
2. Después de mi OK, agregá solo las pruebas que falten para cerrar los huecos.
3. Redactá la sección "Solución" de README.md: estructura, requisitos previos y versiones,
   instalación, carga inicial y reinicio de datos (advirtiendo que borra reservas),
   comandos de app y de pruebas, un ejemplo real de entrada/salida (ejecutado, no inventado),
   dónde persisten los datos, pendientes y limitaciones.

Al terminar ejecutá /cerrar-episodio 3. No hagas commit sin mi aprobación.
```

## Qué revisa el humano antes de aceptar

- [ ] Cada fila de la matriz apunta a una prueba que existe (lo verifico con `pytest -v`).
- [ ] El ejemplo de entrada/salida del README lo reproduzco yo y da lo mismo.
