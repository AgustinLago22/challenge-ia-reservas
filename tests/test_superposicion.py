"""Pruebas unitarias de la única regla de superposición (R6, R8)."""

from datetime import datetime

import pytest

from reservas.dominio import se_superponen


def h(hhmm: str) -> datetime:
    return datetime.strptime(f"2026-11-02T{hhmm}", "%Y-%m-%dT%H:%M")


BASE = (h("10:00"), h("11:00"))


@pytest.mark.parametrize(
    "inicio, fin, esperado, caso",
    [
        ("10:30", "11:30", True, "solapa el final"),
        ("09:30", "10:30", True, "solapa el inicio"),
        ("10:15", "10:45", True, "contenido"),
        ("09:00", "12:00", True, "contiene"),
        ("10:00", "11:00", True, "idéntico"),
        ("10:59", "11:00", True, "último minuto"),
        ("11:00", "12:00", False, "consecutivo posterior"),
        ("09:00", "10:00", False, "consecutivo anterior"),
        ("12:00", "13:00", False, "disjunto"),
    ],
)
def test_se_superponen(inicio, fin, esperado, caso):
    assert se_superponen(h(inicio), h(fin), *BASE) is esperado, caso
    # La relación es simétrica.
    assert se_superponen(*BASE, h(inicio), h(fin)) is esperado, caso
