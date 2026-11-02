from datetime import datetime

import pytest

from reservas.inventario import cargar_inventario
from reservas.repositorio import RepositorioSQLite
from reservas.servicio import ServicioReservas

# Escenario base de los criterios de aceptación: "ahora" fijo, nunca la fecha real.
AHORA = datetime(2026, 11, 1, 8, 0)
DIA = "2026-11-02"


def t(hora: str, dia: str = DIA) -> str:
    """Atajo: t("10:00") -> "2026-11-02T10:00"."""
    return f"{dia}T{hora}"


@pytest.fixture(autouse=True)
def _aislar_base_real(tmp_path, monkeypatch):
    """Ninguna prueba puede tocar data/reservas.db: la variable apunta a un archivo temporal."""
    monkeypatch.setenv("RESERVAS_DB", str(tmp_path / "aislada.db"))


@pytest.fixture
def ruta_db(tmp_path):
    return tmp_path / "reservas.db"


@pytest.fixture
def inventario():
    return cargar_inventario()


@pytest.fixture
def repo(ruta_db):
    r = RepositorioSQLite(ruta_db)
    yield r
    r.cerrar()


@pytest.fixture
def servicio(inventario, repo):
    return ServicioReservas(inventario, repo, reloj=lambda: AHORA)


@pytest.fixture
def mic01_10a11(servicio):
    """Escenario del enunciado: MIC-01 reservado de 10:00 a 11:00."""
    return servicio.crear_reserva("MIC-01", "Ana Prueba", t("10:00"), t("11:00"))
