"""Verificación por mutaciones: introduce fallas a propósito y comprueba que las pruebas las detectan.

Uso: .venv/Scripts/python scripts/verificar_mutaciones.py
Cada mutación se revierte al terminar, aunque pytest falle.
"""
import subprocess, sys
from pathlib import Path
MUTACIONES = [
    ("M1: '<' por '<=' en se_superponen (rompe R8)", "reservas/dominio.py",
     "return a_inicio < b_fin and b_inicio < a_fin", "return a_inicio <= b_fin and b_inicio <= a_fin"),
    ("M2: las CANCELADAS tambien bloquean (rompe R10)", "reservas/repositorio.py",
     'WHERE unidad = ? AND estado = ? ORDER BY inicio, id",\n            (unidad, ACTIVA),',
     'WHERE unidad = ? AND estado != ? ORDER BY inicio, id",\n            (unidad, "X"),'),
]
for nombre, archivo, original, mutado in MUTACIONES:
    p = Path(archivo); texto = p.read_text(encoding="utf-8")
    assert texto.count(original) == 1, nombre
    p.write_text(texto.replace(original, mutado), encoding="utf-8")
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], capture_output=True, text=True)
        fallidas = [l.split(" - ")[0] for l in r.stdout.splitlines() if l.startswith("FAILED")]
        print(f"== {nombre}\n   resumen: {r.stdout.strip().splitlines()[-1]}")
        for f in fallidas: print("   ", f)
    finally:
        p.write_text(texto, encoding="utf-8")
