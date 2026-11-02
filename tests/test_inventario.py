import json

import pytest

from reservas.inventario import InventarioInvalido, cargar_inventario


def test_inventario_precargado_tiene_las_cinco_unidades():
    assert cargar_inventario() == {
        "MIC-01": "Microscopio digital",
        "MIC-02": "Microscopio digital",
        "OSC-01": "Osciloscopio",
        "MUL-01": "Multímetro",
        "FUE-01": "Fuente de alimentación",
    }


@pytest.mark.parametrize(
    "contenido",
    [
        "no es json",
        json.dumps({"unidades": []}),
        json.dumps({"otra": 1}),
        json.dumps({"unidades": [{"id": "A"}]}),
        json.dumps({"unidades": [{"id": "A", "equipo": "x"}, {"id": "A", "equipo": "y"}]}),
    ],
)
def test_inventario_invalido(tmp_path, contenido):
    ruta = tmp_path / "inv.json"
    ruta.write_text(contenido, encoding="utf-8")
    with pytest.raises(InventarioInvalido):
        cargar_inventario(ruta)


def test_inventario_inexistente(tmp_path):
    with pytest.raises(InventarioInvalido):
        cargar_inventario(tmp_path / "no-existe.json")
