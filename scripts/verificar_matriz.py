"""Comprueba que cada prueba citada en docs/evidencia/matriz-cobertura.md existe y pasa.

Uso: .venv/Scripts/python scripts/verificar_matriz.py
Sale con código 1 si alguna referencia no existe o alguna prueba falla.
"""
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # mismo defecto de cp1252 que la CLI (D-16)

RAIZ = Path(__file__).resolve().parent.parent
MATRIZ = RAIZ / "docs" / "evidencia" / "matriz-cobertura.md"

referencias = sorted(set(re.findall(r"tests/test_\w+\.py::\w+", MATRIZ.read_text(encoding="utf-8"))))
recolectadas = subprocess.run(
    [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
    cwd=RAIZ, capture_output=True, text=True,
).stdout
existentes = {linea.split("[")[0] for linea in recolectadas.splitlines() if "::" in linea}

faltantes = [ref for ref in referencias if ref not in existentes]
print(f"Referencias en la matriz: {len(referencias)} | funciones de prueba existentes: {len(existentes)}")
print(f"Referencias inexistentes: {faltantes or 'ninguna'}")
sin_citar = sorted(existentes - set(referencias))
print(f"Pruebas no citadas en la matriz: {sin_citar or 'ninguna'}")

ejecucion = subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *referencias],
    cwd=RAIZ, capture_output=True, text=True,
)
print("Ejecución de las pruebas citadas:", ejecucion.stdout.strip().splitlines()[-1])
sys.exit(1 if faltantes or ejecucion.returncode else 0)
