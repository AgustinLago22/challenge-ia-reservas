# Prompt — Episodio 2

```
Episodio 2. Leé CLAUDE.md y docs/PROGRESO.md antes de hacer nada.

Objetivo: interfaz de consola y verificación de persistencia tras reinicio (CA-12).

1. reservas/__main__.py con argparse y subcomandos:
   - unidades
   - disponibilidad --unidad <ID|todas> --inicio <YYYY-MM-DDTHH:MM> --fin <...>
   - reservar --unidad <ID> --solicitante <texto> --inicio <...> --fin <...>
   - cancelar --id <N>
   - listar [--unidad <ID>] [--estado ACTIVA|CANCELADA]
   - reiniciar-datos --confirmar   (borra todas las reservas; sin --confirmar no hace nada)
   Base de datos: variable de entorno RESERVAS_DB o data/reservas.db por defecto.
   Código de salida 0 si la operación fue exitosa y 1 si fue rechazada, con el mensaje en stderr.
   La CLI no debe tener lógica de negocio propia: solo llama al servicio.
2. Pruebas de extremo a extremo con subprocess (RESERVAS_DB apuntando a tmp_path):
   reservar, cancelar, terminar el proceso, ejecutar un proceso NUEVO con "listar" y
   verificar activas y canceladas; y que la activa siga bloqueando (CA-12).
3. Escribí docs/evidencia/persistencia-manual.md: procedimiento manual reproducible
   (comandos exactos, resultado esperado). Ejecutalo vos y pegá la salida observada real.

Al terminar ejecutá /cerrar-episodio 2. No hagas commit sin mi aprobación.
```

## Qué revisa el humano antes de aceptar

- [ ] Ejecuto yo mismo el procedimiento manual en una consola nueva y comparo con lo registrado.
- [ ] `reiniciar-datos` sin `--confirmar` no borra nada.
- [ ] La CLI no recalcula superposiciones por su cuenta.
