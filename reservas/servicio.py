"""Casos de uso: consultar disponibilidad, reservar, cancelar, listar y reiniciar datos.

Reservar y consultar usan la MISMA función _buscar_conflictos (R13), que a su vez
usa la única regla de superposición dominio.se_superponen (R6).
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from .dominio import (
    ESTADOS,
    FORMATO_MARCA,
    ConflictoError,
    Disponibilidad,
    ErrorValidacion,
    Reserva,
    ReservaNoEncontrada,
    ReservaYaCancelada,
    ahora_local,
    formatear_fecha,
    se_superponen,
    validar_intervalo,
    validar_solicitante,
    validar_unidad,
)
from .repositorio import RepositorioSQLite

Reloj = Callable[[], datetime]


class ServicioReservas:
    def __init__(self, inventario: dict[str, str], repositorio: RepositorioSQLite, reloj: Reloj = ahora_local):
        self.inventario = inventario
        self.repo = repositorio
        self._reloj = reloj

    def _ahora(self) -> datetime:
        return self._reloj().replace(second=0, microsecond=0)

    def _buscar_conflictos(self, unidad: str, inicio: datetime, fin: datetime) -> list[Reserva]:
        """Reservas ACTIVAS de la misma unidad que se superponen con [inicio, fin) (R7, R10)."""
        return [r for r in self.repo.activas_de_unidad(unidad) if se_superponen(inicio, fin, r.inicio, r.fin)]

    def consultar_disponibilidad(self, unidad: str, inicio: str, fin: str) -> Disponibilidad:
        unidad = validar_unidad(unidad, self.inventario)
        ini, fi = validar_intervalo(inicio, fin)
        return Disponibilidad(unidad, ini, fi, tuple(self._buscar_conflictos(unidad, ini, fi)))

    def consultar_disponibilidad_todas(self, inicio: str, fin: str) -> list[Disponibilidad]:
        return [self.consultar_disponibilidad(unidad, inicio, fin) for unidad in self.inventario]

    def crear_reserva(self, unidad: str, solicitante: str, inicio: str, fin: str) -> Reserva:
        unidad = validar_unidad(unidad, self.inventario)
        solicitante = validar_solicitante(solicitante)
        ini, fi = validar_intervalo(inicio, fin)
        ahora = self._ahora()
        if ini < ahora:
            raise ErrorValidacion(
                f"El inicio ({formatear_fecha(ini)}) ya pasó: no se pueden crear reservas en el pasado "
                f"(ahora: {formatear_fecha(ahora)})."
            )
        with self.repo.transaccion():
            conflictos = self._buscar_conflictos(unidad, ini, fi)
            if conflictos:
                raise ConflictoError(conflictos)
            return self.repo.insertar(unidad, solicitante, ini, fi, ahora.strftime(FORMATO_MARCA))

    def cancelar_reserva(self, id_reserva: int) -> Reserva:
        if isinstance(id_reserva, bool) or not isinstance(id_reserva, int):
            raise ErrorValidacion(f"ID de reserva inválido: {id_reserva!r}.")
        with self.repo.transaccion():
            reserva = self.repo.obtener(id_reserva)
            if reserva is None:
                raise ReservaNoEncontrada(f"No existe la reserva #{id_reserva}.")
            if not reserva.activa:
                raise ReservaYaCancelada(f"La reserva #{id_reserva} ya estaba cancelada (desde {reserva.cancelada_en}).")
            return self.repo.marcar_cancelada(id_reserva, self._ahora().strftime(FORMATO_MARCA))

    def listar_reservas(self, unidad: str | None = None, estado: str | None = None) -> list[Reserva]:
        if unidad is not None:
            validar_unidad(unidad, self.inventario)
        if estado is not None and estado not in ESTADOS:
            raise ErrorValidacion(f"Estado inválido: {estado!r}. Use {' o '.join(ESTADOS)}.")
        return self.repo.listar(unidad, estado)

    def reiniciar_datos(self, confirmar: bool) -> int:
        """Borra TODAS las reservas (activas y canceladas). Exige confirmación explícita."""
        if confirmar is not True:
            raise ErrorValidacion("El reinicio borra todas las reservas: hay que confirmarlo explícitamente.")
        return self.repo.borrar_todo()
