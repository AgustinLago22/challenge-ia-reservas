# Prompt — Episodio 4 (interfaz web local)

Pedido real del humano (2026-11-02): «¿no se podría hacer por web?… Es para comprobarlo más fácil
y que se testee mejor». A partir de eso, el agente redactó esta instrucción y la siguió:

```
Episodio 4. Leé CLAUDE.md, docs/PROGRESO.md y docs/ESPECIFICACION.md (v1.2, CA-14).

Objetivo: una página web local para probar el sistema con clics, sin cambiar ninguna regla.

1. reservas/web.py con http.server (biblioteca estándar, sin dependencias nuevas):
   - escuchar solo en 127.0.0.1; subcomando `python -m reservas web [--puerto N]`;
   - API JSON: GET /api/unidades, GET /api/reservas, GET /api/disponibilidad,
     POST /api/reservas, POST /api/reservas/<id>/cancelar;
   - códigos HTTP: 201 creada, 400 entrada inválida, 404 inexistente, 409 conflicto o ya cancelada;
   - cada pedido abre su propia conexión SQLite; la web NO tiene lógica de negocio,
     solo llama a ServicioReservas;
   - sin endpoint de reinicio de datos.
2. reservas/static/index.html: formularios de disponibilidad, reserva y cancelación, y la tabla del
   historial. Mostrar el texto del usuario con textContent (nunca innerHTML) y no validar en el
   navegador, para que se vean los rechazos del servidor.
3. tests/test_web.py: CA-14 por HTTP real (servidor en un hilo, puerto 0) y un proceso real de
   `python -m reservas web`. Incluir la persistencia al reiniciar el servidor y que la consola vea
   lo que creó la web.
4. Actualizar la matriz de cobertura y verificar con scripts/verificar_matriz.py.

Al terminar: /cerrar-episodio 4.
```

## Qué revisa el humano antes de aceptar

- [ ] Abro `http://127.0.0.1:8000`, reservo MIC-01 de 10 a 11 y veo que 10:30–11:30 se rechaza y 11:00–12:00 se acepta.
- [ ] Cancelo desde la tabla y el horario vuelve a figurar disponible.
- [ ] Corto el servidor (Ctrl+C), lo vuelvo a iniciar y las reservas siguen ahí.
- [ ] `python -m reservas listar` muestra lo mismo que la página.
