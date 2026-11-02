"""Persistencia en SQLite. Procedimiento fijado en CLAUDE.md:

- el esquema se crea con CREATE TABLE IF NOT EXISTS (abrir una base existente no pierde datos);
- cancelar es un UPDATE de estado, nunca un DELETE;
- el único DELETE está en borrar_todo(), usado solo por el reinicio explícito de datos.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .dominio import ACTIVA, CANCELADA, FORMATO_FECHA, Reserva, formatear_fecha

RUTA_DB = Path(__file__).resolve().parent.parent / "data" / "reservas.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS reservas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    unidad       TEXT NOT NULL,
    solicitante  TEXT NOT NULL CHECK (length(trim(solicitante)) > 0),
    inicio       TEXT NOT NULL,
    fin          TEXT NOT NULL,
    estado       TEXT NOT NULL CHECK (estado IN ('ACTIVA', 'CANCELADA')),
    creada_en    TEXT NOT NULL,
    cancelada_en TEXT,
    CHECK (inicio < fin)
);
CREATE INDEX IF NOT EXISTS idx_reservas_unidad_estado ON reservas (unidad, estado);
"""

_COLUMNAS = "id, unidad, solicitante, inicio, fin, estado, creada_en, cancelada_en"

# Órdenes del historial. El ID desempata porque es único y crece con la creación (R15).
ORDENES = {
    "creacion": "id",  # por defecto: orden de creación
    "creacion_desc": "id DESC",
    "fecha": "inicio, id",  # por fecha de la reserva, más antigua primero
    "fecha_desc": "inicio DESC, id DESC",  # por fecha de la reserva, más reciente primero
}


def _a_reserva(fila: sqlite3.Row) -> Reserva:
    return Reserva(
        id=fila["id"],
        unidad=fila["unidad"],
        solicitante=fila["solicitante"],
        inicio=datetime.strptime(fila["inicio"], FORMATO_FECHA),
        fin=datetime.strptime(fila["fin"], FORMATO_FECHA),
        estado=fila["estado"],
        creada_en=fila["creada_en"],
        cancelada_en=fila["cancelada_en"],
    )


class RepositorioSQLite:
    def __init__(self, ruta: str | Path = RUTA_DB):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        # isolation_level=None: las transacciones se controlan a mano con BEGIN IMMEDIATE.
        self._con = sqlite3.connect(self.ruta, isolation_level=None)
        self._con.row_factory = sqlite3.Row
        self._con.executescript(ESQUEMA)

    def cerrar(self) -> None:
        self._con.close()

    def __enter__(self) -> RepositorioSQLite:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.cerrar()

    @contextmanager
    def transaccion(self) -> Iterator[None]:
        """Bloquea la base para escritura: verificar conflicto + insertar es atómico (R14)."""
        self._con.execute("BEGIN IMMEDIATE")
        try:
            yield
        except BaseException:
            self._con.execute("ROLLBACK")
            raise
        else:
            self._con.execute("COMMIT")

    def insertar(self, unidad: str, solicitante: str, inicio: datetime, fin: datetime, creada_en: str) -> Reserva:
        cur = self._con.execute(
            "INSERT INTO reservas (unidad, solicitante, inicio, fin, estado, creada_en) VALUES (?, ?, ?, ?, ?, ?)",
            (unidad, solicitante, formatear_fecha(inicio), formatear_fecha(fin), ACTIVA, creada_en),
        )
        return self.obtener(cur.lastrowid)

    def obtener(self, id_reserva: int) -> Reserva | None:
        fila = self._con.execute(f"SELECT {_COLUMNAS} FROM reservas WHERE id = ?", (id_reserva,)).fetchone()
        return _a_reserva(fila) if fila else None

    def marcar_cancelada(self, id_reserva: int, cancelada_en: str) -> Reserva:
        self._con.execute(
            "UPDATE reservas SET estado = ?, cancelada_en = ? WHERE id = ? AND estado = ?",
            (CANCELADA, cancelada_en, id_reserva, ACTIVA),
        )
        return self.obtener(id_reserva)

    def activas_de_unidad(self, unidad: str) -> list[Reserva]:
        filas = self._con.execute(
            f"SELECT {_COLUMNAS} FROM reservas WHERE unidad = ? AND estado = ? ORDER BY inicio, id",
            (unidad, ACTIVA),
        ).fetchall()
        return [_a_reserva(f) for f in filas]

    def listar(self, unidad: str | None = None, estado: str | None = None, orden: str = "creacion") -> list[Reserva]:
        """orden: una clave de ORDENES (validada en el servicio). Nunca se arma SQL con texto del usuario."""
        condiciones, parametros = [], []
        if unidad is not None:
            condiciones.append("unidad = ?")
            parametros.append(unidad)
        if estado is not None:
            condiciones.append("estado = ?")
            parametros.append(estado)
        where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
        filas = self._con.execute(
            f"SELECT {_COLUMNAS} FROM reservas {where} ORDER BY {ORDENES[orden]}", parametros
        ).fetchall()
        return [_a_reserva(f) for f in filas]

    def borrar_todo(self) -> int:
        """Reinicio explícito de datos: borra TODAS las reservas. Devuelve cuántas borró."""
        with self.transaccion():
            return self._con.execute("DELETE FROM reservas").rowcount
