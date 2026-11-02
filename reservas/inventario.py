"""Lectura del inventario precargado (solo lectura; no se administra)."""

from __future__ import annotations

import json
from pathlib import Path

RUTA_INVENTARIO = Path(__file__).resolve().parent.parent / "data" / "inventario.json"


class InventarioInvalido(Exception):
    """El archivo de inventario no existe o no tiene la estructura esperada."""


def cargar_inventario(ruta: str | Path = RUTA_INVENTARIO) -> dict[str, str]:
    """Devuelve {id_unidad: equipo} en el orden del archivo."""
    ruta = Path(ruta)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise InventarioInvalido(f"No se encontró el inventario en {ruta}.") from None
    except json.JSONDecodeError as exc:
        raise InventarioInvalido(f"El inventario {ruta} no es JSON válido: {exc}") from None

    unidades = datos.get("unidades") if isinstance(datos, dict) else None
    if not isinstance(unidades, list) or not unidades:
        raise InventarioInvalido(f"El inventario {ruta} debe tener una lista 'unidades' no vacía.")

    inventario: dict[str, str] = {}
    for item in unidades:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not isinstance(item.get("equipo"), str):
            raise InventarioInvalido(f"Entrada de inventario inválida: {item!r}.")
        if item["id"] in inventario:
            raise InventarioInvalido(f"ID de unidad duplicado en el inventario: {item['id']}.")
        inventario[item["id"]] = item["equipo"]
    return inventario
