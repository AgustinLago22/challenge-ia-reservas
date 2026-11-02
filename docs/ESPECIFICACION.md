# Especificación — Sistema de reservas de equipos de laboratorio

> Versión inicial (v1). Los cambios significativos se registran en la sección
> [Historial de cambios](#historial-de-cambios) y quedan recuperables en Git.

## 1. Problema

La coordinación de un laboratorio registra pedidos de equipos en mensajes y una
planilla. Esto produce dos fallas: se confirma la misma unidad para horarios
superpuestos, y una cancelación sigue bloqueando el horario. Se necesita una
herramienta local para **consultar disponibilidad, reservar y cancelar sin perder
el historial**.

## 2. Alcance

**Incluido**

- Leer el inventario precargado (`data/inventario.json`). No se administra el inventario.
- Consultar disponibilidad de una unidad (o de todas) en un intervalo.
- Crear una reserva: una unidad, un solicitante ficticio, inicio y fin.
- Cancelar una reserva conservando su identificador y sus datos.
- Listar reservas (historial), incluidas las canceladas, con filtros por unidad y estado y con **orden**
  elegible: por creación o por fecha de la reserva, ascendente o descendente (desde v1.3).
- Persistir reservas y estados entre reinicios de la aplicación.
- Dos interfaces sobre las **mismas reglas**: consola (`python -m reservas …`) y una página web
  **local** (`python -m reservas web`, solo en `127.0.0.1`) con una API JSON. La web no tiene
  lógica propia: todas las decisiones las toma el mismo servicio que usa la consola. Desde v1.2.

**Fuera de alcance**: autenticación y roles, notificaciones, pagos, integraciones
externas, despliegue, acceso desde otras máquinas, frente gráfico complejo, concurrencia
distribuida y escalabilidad. El **reinicio de datos no se ofrece en la web** (solo en la consola,
con `--confirmar`) para que no se pueda borrar todo con un clic.
Tampoco se editan reservas: para cambiar un horario se cancela y se crea otra.

## 3. Inventario

| ID     | Equipo                 |
|--------|------------------------|
| MIC-01 | Microscopio digital    |
| MIC-02 | Microscopio digital    |
| OSC-01 | Osciloscopio           |
| MUL-01 | Multímetro             |
| FUE-01 | Fuente de alimentación |

Cada ID es una unidad física distinta. MIC-01 y MIC-02 son el mismo tipo de equipo
pero se reservan por separado.

## 4. Reglas de negocio

| Regla | Descripción |
|-------|-------------|
| R1 | La unidad debe existir en el inventario (comparación exacta del ID, p. ej. `MIC-01`). |
| R2 | El solicitante no puede estar vacío ni ser solo espacios. Se guarda sin espacios al inicio/fin. |
| R3 | Inicio y fin deben ser fechas-hora válidas en el formato `YYYY-MM-DDTHH:MM` (p. ej. `2026-11-02T10:00`). |
| R4 | El inicio debe ser **estrictamente anterior** al fin. |
| R5 | El inicio no puede estar en el pasado respecto del momento de la solicitud. |
| R6 | Los intervalos son **semiabiertos** `[inicio, fin)`. Dos intervalos A y B se superponen si y solo si `A.inicio < B.fin` y `B.inicio < A.fin`. |
| R7 | Se rechaza una reserva si se superpone con otra reserva **ACTIVA de la misma unidad**. |
| R8 | Los límites consecutivos están permitidos: 10:00–11:00 y 11:00–12:00 no se superponen. |
| R9 | Reservas simultáneas de **unidades distintas** están permitidas. |
| R10 | Una reserva **CANCELADA no bloquea** disponibilidad. |
| R11 | Cancelar cambia el estado de ACTIVA a CANCELADA y registra el momento de la cancelación. El ID y los datos se conservan; **nunca se borra** una reserva. |
| R12 | No se puede cancelar una reserva inexistente o ya cancelada. |
| R13 | La consulta de disponibilidad usa **exactamente las mismas reglas** (R1, R3, R4, R6, R7, R10) que la creación de reservas. |
| R14 | Una operación rechazada no modifica los datos guardados. |
| R15 | Cada reserva tiene un ID entero, único y autoincremental que no se reutiliza. |

## 5. Supuestos

| Supuesto | Decisión |
|----------|----------|
| Zona horaria | Única y fija: hora de Argentina, implementada como desfase fijo **UTC−3** (`datetime.timezone(timedelta(hours=-3))`; Argentina no aplica horario de verano desde 2009). Todas las horas ingresadas y guardadas son hora local del laboratorio. Ver cambio v1.1. |
| Formato de fecha | `YYYY-MM-DDTHH:MM` (ISO 8601, precisión de minutos). Cualquier otro formato se rechaza. Se usa `T` para no tener que escribir comillas en la consola. |
| Fechas pasadas | No se puede **crear** una reserva cuyo inicio sea anterior a "ahora" truncado al minuto (una reserva que empieza en el minuto actual se acepta). Sí se puede **consultar** disponibilidad de intervalos pasados y **cancelar** reservas activas aunque ya hayan pasado (registro administrativo). |
| Duración y anticipación | Sin máximo de duración ni de anticipación. Una reserva puede abarcar varios días. |
| Reloj | El "ahora" se obtiene de un reloj inyectable para que las pruebas sean deterministas. |
| Solicitante | Texto libre ficticio (sin validar identidad, sin autenticación). |
| Concurrencia | Un solo proceso a la vez (uso local). La verificación de conflicto y la inserción ocurren en una misma transacción. |
| Reinicio de datos | Existe un comando explícito que **borra todas las reservas** (activas y canceladas) y requiere confirmación. El inventario no se modifica. |

## 6. Criterios de aceptación

Cada criterio debe quedar cubierto por al menos una prueba automática (salvo que
se indique un procedimiento manual). Escenario base: ahora = `2026-11-01T08:00`.

| ID | Criterio | Reglas |
|----|----------|--------|
| CA-01 | Crear una reserva válida (MIC-01, "Ana Prueba", 2026-11-02 10:00–11:00) devuelve un ID, estado ACTIVA y los datos ingresados. | R1–R5, R15 |
| CA-02 | Con MIC-01 reservado 10:00–11:00, se rechaza 10:30–11:30, 09:30–10:30, 10:15–10:45, 09:00–12:00 y 10:00–11:00. | R6, R7 |
| CA-03 | Con MIC-01 reservado 10:00–11:00, se permite 11:00–12:00 y 09:00–10:00. | R8 |
| CA-04 | Con MIC-01 reservado 10:00–11:00, se permite MIC-02 10:00–11:00. | R9 |
| CA-05 | Se rechaza una unidad desconocida (`XYZ-99`, `mic-01`, vacío). | R1 |
| CA-06 | Se rechaza un solicitante vacío o compuesto solo por espacios/tabulaciones. | R2 |
| CA-07 | Se rechazan fechas mal formadas o inexistentes (`2026-02-30T10:00`, `2026-11-02T25:00`, `02/11/2026 10:00`, texto) e inicio igual o posterior al fin. | R3, R4 |
| CA-08 | Se rechaza una reserva cuyo inicio es anterior a "ahora". | R5 |
| CA-09 | La consulta de disponibilidad informa "no disponible" (con la reserva en conflicto) para un intervalo superpuesto, y "disponible" para un intervalo consecutivo o de otra unidad. | R13 |
| CA-10 | Cancelar una reserva activa conserva ID y datos, pasa a CANCELADA, y después el mismo intervalo puede reservarse y figura disponible. | R10, R11 |
| CA-11 | Cancelar una reserva inexistente o ya cancelada se rechaza sin cambios. | R12, R14 |
| CA-12 | Tras detener y reiniciar la aplicación (nuevo proceso sobre el mismo archivo de datos), se recuperan reservas activas y canceladas con sus estados, y las activas siguen bloqueando. | R11 + persistencia |
| CA-13 | Una solicitud rechazada no crea registros ni altera los existentes. | R14 |
| CA-14 | La web local aplica las mismas reglas que la consola: el ejemplo del enunciado da el mismo resultado por HTTP (201 creada / 409 superposición / 400 entrada inválida / 404 inexistente). Las reservas creadas por la web se ven desde la consola y viceversa, y persisten al reiniciar el servidor. | R1–R15 |

## Historial de cambios

| Versión | Fecha | Cambio | Motivo |
|---------|-------|--------|--------|
| v1 | 2026-10-26 | Versión inicial, redactada en la sesión de preparación del agente. | Punto de partida para los episodios de delegación. |
| v1.1 | 2026-11-02 | Zona horaria: de `ZoneInfo("America/Argentina/Buenos_Aires")` a desfase fijo UTC−3. Se aclara que "ahora" se trunca al minuto. | Comprobado en el episodio 1: en Windows `ZoneInfo(...)` lanza `ZoneInfoNotFoundError` sin el paquete `tzdata`. El desfase fijo da el mismo resultado para Argentina sin agregar dependencias. El truncado evita rechazar una reserva del minuto en curso por los segundos. |
| v1.2 | 2026-11-02 | Se agrega la interfaz web local (alcance §2 y CA-14). La web no ofrece el reinicio de datos. | Pedido del autor: «para comprobarlo más fácil». La consigna no la exige y no suma puntos por sí misma; se acepta porque facilita la verificación humana manual y no cambia ninguna regla. |
| v1.3 | 2026-11-02 | Orden elegible del historial (`creacion`, `creacion_desc`, `fecha`, `fecha_desc`); por defecto, el de creación. | Pedido del autor tras probar la web: «un filtro para ver de más recientes a más viejas». No cambia ninguna regla de reserva. |
