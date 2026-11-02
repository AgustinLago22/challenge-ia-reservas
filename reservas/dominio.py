"""Reglas de negocio puras: validaciones, formato de fechas y superposición.

Este módulo no conoce la base de datos ni la consola. Ver docs/ESPECIFICACION.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

FORMATO_FECHA = "%Y-%m-%dT%H:%M"
FORMATO_MARCA = "%Y-%m-%dT%H:%M:%S"
ZONA_HORARIA = timezone(timedelta(hours=-3), name="UTC-03")

ACTIVA = "ACTIVA"
CANCELADA = "CANCELADA"
ESTADOS = (ACTIVA, CANCELADA)


class ReservaError(Exception):
    """Base de todos los rechazos de negocio. El mensaje es apto para el usuario."""


class ErrorValidacion(ReservaError):
    """Entrada inválida (R1–R5)."""


class ConflictoError(ReservaError):
    """El intervalo se superpone con reservas activas de la misma unidad (R7)."""

    def __init__(self, conflictos: list[Reserva]):
        self.conflictos = conflictos
        ids = ", ".join(f"#{r.id} ({r.inicio_txt}->{r.fin_txt})" for r in conflictos)
        super().__init__(f"La unidad {conflictos[0].unidad} ya está reservada en ese intervalo: {ids}")


class ReservaNoEncontrada(ReservaError):
    """No existe una reserva con ese ID (R12)."""


class ReservaYaCancelada(ReservaError):
    """La reserva ya estaba cancelada (R12)."""


@dataclass(frozen=True)
class Reserva:
    id: int
    unidad: str
    solicitante: str
    inicio: datetime
    fin: datetime
    estado: str
    creada_en: str
    cancelada_en: str | None = None

    @property
    def inicio_txt(self) -> str:
        return formatear_fecha(self.inicio)

    @property
    def fin_txt(self) -> str:
        return formatear_fecha(self.fin)

    @property
    def activa(self) -> bool:
        return self.estado == ACTIVA


@dataclass(frozen=True)
class Disponibilidad:
    unidad: str
    inicio: datetime
    fin: datetime
    conflictos: tuple[Reserva, ...]

    @property
    def disponible(self) -> bool:
        return not self.conflictos


def se_superponen(a_inicio: datetime, a_fin: datetime, b_inicio: datetime, b_fin: datetime) -> bool:
    """Única regla de superposición del sistema (R6).

    Intervalos semiabiertos [inicio, fin): 10:00–11:00 y 11:00–12:00 NO se superponen (R8).
    """
    return a_inicio < b_fin and b_inicio < a_fin


def parsear_fecha(valor: object, campo: str) -> datetime:
    """Convierte 'YYYY-MM-DDTHH:MM' en datetime (R3). Rechaza cualquier otro formato."""
    if not isinstance(valor, str) or not valor.strip():
        raise ErrorValidacion(f"La fecha de {campo} es obligatoria (formato YYYY-MM-DDTHH:MM).")
    try:
        return datetime.strptime(valor.strip(), FORMATO_FECHA)
    except ValueError:
        raise ErrorValidacion(
            f"Fecha de {campo} inválida: {valor!r}. Use el formato YYYY-MM-DDTHH:MM, p. ej. 2026-11-02T10:00."
        ) from None


def formatear_fecha(valor: datetime) -> str:
    return valor.strftime(FORMATO_FECHA)


def validar_intervalo(inicio_txt: object, fin_txt: object) -> tuple[datetime, datetime]:
    """Parsea ambas fechas y exige inicio estrictamente anterior al fin (R3, R4)."""
    inicio = parsear_fecha(inicio_txt, "inicio")
    fin = parsear_fecha(fin_txt, "fin")
    if not inicio < fin:
        raise ErrorValidacion(
            f"El inicio ({formatear_fecha(inicio)}) debe ser estrictamente anterior al fin ({formatear_fecha(fin)})."
        )
    return inicio, fin


def validar_unidad(unidad: object, inventario: dict[str, str]) -> str:
    """La unidad debe existir en el inventario, con comparación exacta (R1)."""
    if not isinstance(unidad, str) or unidad not in inventario:
        conocidas = ", ".join(sorted(inventario))
        raise ErrorValidacion(f"Unidad desconocida: {unidad!r}. Unidades válidas: {conocidas}.")
    return unidad


def validar_solicitante(solicitante: object) -> str:
    """No vacío ni compuesto solo por espacios; se guarda sin espacios extremos (R2)."""
    if not isinstance(solicitante, str) or not solicitante.strip():
        raise ErrorValidacion("El solicitante no puede estar vacío ni contener solo espacios.")
    return solicitante.strip()


def ahora_local() -> datetime:
    """Reloj por defecto: hora actual del laboratorio (UTC−3), sin zona, truncada al minuto."""
    return datetime.now(ZONA_HORARIA).replace(tzinfo=None, second=0, microsecond=0)
