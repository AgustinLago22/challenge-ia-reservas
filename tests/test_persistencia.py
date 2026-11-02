"""Persistencia por reapertura de la base en una instancia nueva (anticipo de CA-12).

La versión con un proceso nuevo del sistema operativo está en tests/test_cli.py.
"""

from reservas.dominio import ACTIVA, CANCELADA
from reservas.repositorio import RepositorioSQLite
from reservas.servicio import ServicioReservas

from .conftest import AHORA, t


def _abrir(inventario, ruta_db):
    return ServicioReservas(inventario, RepositorioSQLite(ruta_db), reloj=lambda: AHORA)


def test_ca12_reabrir_recupera_activas_y_canceladas(inventario, ruta_db):
    s1 = _abrir(inventario, ruta_db)
    activa = s1.crear_reserva("MIC-01", "Ana Prueba", t("10:00"), t("11:00"))
    cancelada = s1.crear_reserva("OSC-01", "Beto Ficticio", t("14:00"), t("15:00"))
    cancelada = s1.cancelar_reserva(cancelada.id)
    s1.repo.cerrar()

    s2 = _abrir(inventario, ruta_db)
    try:
        assert s2.listar_reservas() == [activa, cancelada]
        assert [r.estado for r in s2.listar_reservas()] == [ACTIVA, CANCELADA]
        # La activa sigue bloqueando y la cancelada no.
        assert not s2.consultar_disponibilidad("MIC-01", t("10:30"), t("11:30")).disponible
        assert s2.consultar_disponibilidad("OSC-01", t("14:00"), t("15:00")).disponible
        # Los IDs siguen sin reutilizarse tras reabrir.
        nueva = s2.crear_reserva("MUL-01", "Carla Inventada", t("10:00"), t("11:00"))
        assert nueva.id > cancelada.id
    finally:
        s2.repo.cerrar()


def test_abrir_base_existente_no_pierde_datos(inventario, ruta_db):
    s1 = _abrir(inventario, ruta_db)
    s1.crear_reserva("MIC-01", "Ana Prueba", t("10:00"), t("11:00"))
    s1.repo.cerrar()
    for _ in range(3):  # CREATE TABLE IF NOT EXISTS repetido
        RepositorioSQLite(ruta_db).cerrar()
    s2 = _abrir(inventario, ruta_db)
    try:
        assert len(s2.listar_reservas()) == 1
    finally:
        s2.repo.cerrar()
