"""Pruebas de extremo a extremo: cada llamada es un PROCESO NUEVO de `python -m reservas`.

CA-12: detener y reiniciar la aplicación (cada subprocess termina) conserva reservas
activas y canceladas, y las activas siguen bloqueando.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
AHORA = "2026-11-01T08:00"


@pytest.fixture
def cli(tmp_path):
    db = tmp_path / "cli.db"
    entorno = {**os.environ, "RESERVAS_DB": str(db), "RESERVAS_AHORA": AHORA, "PYTHONIOENCODING": "utf-8"}

    def ejecutar(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "reservas", *args],
            cwd=RAIZ,
            env=entorno,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )

    ejecutar.db = db
    return ejecutar


def reservar(cli, unidad, inicio, fin, solicitante="Ana Prueba"):
    return cli("reservar", "--unidad", unidad, "--solicitante", solicitante, "--inicio", inicio, "--fin", fin)


def test_ca12_persistencia_tras_reiniciar_en_proceso_nuevo(cli):
    # Proceso 1 y 2: crear dos reservas. Proceso 3: cancelar una.
    assert reservar(cli, "MIC-01", "2026-11-02T10:00", "2026-11-02T11:00").returncode == 0
    assert reservar(cli, "OSC-01", "2026-11-02T14:00", "2026-11-02T15:00", "Beto Ficticio").returncode == 0
    assert cli("cancelar", "--id", "2").returncode == 0
    assert cli.db.exists()

    # Proceso 4 (nuevo): el historial tiene ambas con su estado.
    listado = cli("listar")
    assert listado.returncode == 0
    lineas = listado.stdout.splitlines()
    assert len(lineas) == 2
    assert lineas[0].startswith("#1") and "MIC-01" in lineas[0] and "ACTIVA" in lineas[0]
    assert lineas[1].startswith("#2") and "OSC-01" in lineas[1] and "CANCELADA" in lineas[1]
    assert "Beto Ficticio" in lineas[1] and "cancelada 2026-11-01T08:00:00" in lineas[1]

    # Proceso 5 y 6 (nuevos): la activa sigue bloqueando; la cancelada no.
    rechazo = reservar(cli, "MIC-01", "2026-11-02T10:30", "2026-11-02T11:30", "Carla Inventada")
    assert rechazo.returncode == 1 and "#1" in rechazo.stderr
    assert reservar(cli, "OSC-01", "2026-11-02T14:00", "2026-11-02T15:00", "Carla Inventada").returncode == 0


def test_cli_ejemplo_del_enunciado(cli):
    assert reservar(cli, "MIC-01", "2026-11-02T10:00", "2026-11-02T11:00").returncode == 0

    rechazada = reservar(cli, "MIC-01", "2026-11-02T10:30", "2026-11-02T11:30", "Beto Ficticio")
    assert rechazada.returncode == 1
    assert rechazada.stderr.startswith("Error: La unidad MIC-01 ya está reservada")
    assert rechazada.stdout == ""

    consecutiva = reservar(cli, "MIC-01", "2026-11-02T11:00", "2026-11-02T12:00", "Beto Ficticio")
    assert consecutiva.returncode == 0 and consecutiva.stdout.startswith("Reserva creada: #2")

    otra_unidad = reservar(cli, "MIC-02", "2026-11-02T10:00", "2026-11-02T11:00", "Carla Inventada")
    assert otra_unidad.returncode == 0


def test_cli_disponibilidad(cli):
    reservar(cli, "MIC-01", "2026-11-02T10:00", "2026-11-02T11:00")

    ocupada = cli("disponibilidad", "--unidad", "MIC-01", "--inicio", "2026-11-02T10:30", "--fin", "2026-11-02T11:30")
    assert ocupada.returncode == 0
    assert "OCUPADA" in ocupada.stdout and "#1" in ocupada.stdout

    libre = cli("disponibilidad", "--unidad", "MIC-01", "--inicio", "2026-11-02T11:00", "--fin", "2026-11-02T12:00")
    assert "DISPONIBLE" in libre.stdout

    todas = cli("disponibilidad", "--unidad", "todas", "--inicio", "2026-11-02T10:00", "--fin", "2026-11-02T11:00")
    estados = dict(linea.split()[:2] for linea in todas.stdout.splitlines())
    assert estados == {"MIC-01": "OCUPADA", "MIC-02": "DISPONIBLE", "OSC-01": "DISPONIBLE",
                       "MUL-01": "DISPONIBLE", "FUE-01": "DISPONIBLE"}


@pytest.mark.parametrize(
    "unidad, solicitante, inicio, fin, mensaje",
    [
        ("XYZ-99", "Ana Prueba", "2026-11-02T10:00", "2026-11-02T11:00", "Unidad desconocida"),
        ("MIC-01", "   ", "2026-11-02T10:00", "2026-11-02T11:00", "solicitante"),
        ("MIC-01", "Ana Prueba", "2026-02-30T10:00", "2026-11-02T11:00", "Fecha de inicio inválida"),
        ("MIC-01", "Ana Prueba", "2026-11-02T11:00", "2026-11-02T10:00", "estrictamente anterior"),
        ("MIC-01", "Ana Prueba", "2026-10-01T10:00", "2026-10-01T11:00", "ya pasó"),
    ],
)
def test_cli_entradas_invalidas(cli, unidad, solicitante, inicio, fin, mensaje):
    resultado = reservar(cli, unidad, inicio, fin, solicitante)
    assert resultado.returncode == 1
    assert mensaje in resultado.stderr
    assert cli("listar").stdout.strip() == "(sin reservas)"


def test_cli_cancelar_errores(cli):
    assert cli("cancelar", "--id", "99").returncode == 1
    assert cli("cancelar", "--id", "abc").returncode == 2  # error de uso (argparse)
    reservar(cli, "MIC-01", "2026-11-02T10:00", "2026-11-02T11:00")
    assert cli("cancelar", "--id", "1").returncode == 0
    segunda = cli("cancelar", "--id", "1")
    assert segunda.returncode == 1 and "ya estaba cancelada" in segunda.stderr


def test_cli_listar_filtros(cli):
    reservar(cli, "MIC-01", "2026-11-02T10:00", "2026-11-02T11:00")
    reservar(cli, "OSC-01", "2026-11-02T10:00", "2026-11-02T11:00")
    cli("cancelar", "--id", "2")
    assert len(cli("listar", "--estado", "ACTIVA").stdout.splitlines()) == 1
    assert "OSC-01" in cli("listar", "--estado", "CANCELADA").stdout
    assert "MIC-01" in cli("listar", "--unidad", "MIC-01").stdout
    assert cli("listar", "--unidad", "XYZ-99").returncode == 1


def test_cli_reiniciar_datos_sin_confirmar_no_borra(cli):
    reservar(cli, "MIC-01", "2026-11-02T10:00", "2026-11-02T11:00")
    sin_confirmar = cli("reiniciar-datos")
    assert sin_confirmar.returncode == 1 and "No se borró nada" in sin_confirmar.stderr
    assert "MIC-01" in cli("listar").stdout

    confirmado = cli("reiniciar-datos", "--confirmar")
    assert confirmado.returncode == 0 and "se borraron 1 reservas" in confirmado.stdout
    assert cli("listar").stdout.strip() == "(sin reservas)"
    assert "MIC-01" in cli("unidades").stdout  # el inventario no se toca


def test_cli_unidades(cli):
    salida = cli("unidades").stdout
    assert salida.splitlines()[0].split()[0] == "MIC-01"
    assert "Multímetro" in salida and len(salida.splitlines()) == 5


def test_cli_ahora_invalido(cli):
    resultado = subprocess.run(
        [sys.executable, "-m", "reservas", "listar"],
        cwd=RAIZ,
        env={**os.environ, "RESERVAS_DB": str(cli.db), "RESERVAS_AHORA": "ayer"},
        capture_output=True,
        text=True,
    )
    assert resultado.returncode == 1 and "RESERVAS_AHORA" in resultado.stderr


def test_cli_salida_utf8_sin_configurar_el_entorno(tmp_path):
    """Defecto encontrado en el procedimiento manual del episodio 2: en Windows, con la salida
    redirigida, Python usaba cp1252 y Git Bash mostraba 'est�' en lugar de 'está'.
    Esta prueba NO fija PYTHONIOENCODING y decodifica los bytes como UTF-8."""
    entorno = {k: v for k, v in os.environ.items() if k not in ("PYTHONIOENCODING", "PYTHONUTF8")}
    entorno["RESERVAS_DB"] = str(tmp_path / "utf8.db")
    resultado = subprocess.run(
        [sys.executable, "-m", "reservas", "reservar", "--unidad", "XYZ-99", "--solicitante", "Ana Prueba",
         "--inicio", "2030-01-01T10:00", "--fin", "2030-01-01T11:00"],
        cwd=RAIZ, env=entorno, capture_output=True,
    )
    assert "Unidades válidas" in resultado.stderr.decode("utf-8")
    unidades = subprocess.run([sys.executable, "-m", "reservas", "unidades"], cwd=RAIZ, env=entorno, capture_output=True)
    assert "Multímetro" in unidades.stdout.decode("utf-8")
