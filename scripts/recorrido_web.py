"""Recorrido manual de la web: arranca el proceso real, hace los pedidos que hace la página, lo detiene y lo reinicia.

Uso: .venv/Scripts/python scripts/recorrido_web.py [ruta-db-temporal]   (usa una base aparte, nunca data/reservas.db)
"""
import json, os, subprocess, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
db = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.environ.get("TEMP", "."), "recorrido-web.db")
from pathlib import Path
if Path(db).resolve() == (Path(__file__).resolve().parent.parent / "data" / "reservas.db"):
    sys.exit("Este recorrido usa una base temporal propia; no se ejecuta sobre data/reservas.db.")
if os.path.exists(db):
    os.remove(db)  # base temporal propia del recorrido: empezar siempre vacía para que sea reproducible
entorno = {**os.environ, "RESERVAS_DB": db, "RESERVAS_AHORA": "2026-11-01T08:00", "PYTHONIOENCODING": "utf-8"}

def arrancar():
    p = subprocess.Popen([sys.executable, "-m", "reservas", "web", "--puerto", "0"], env=entorno,
                         stdout=subprocess.PIPE, text=True, encoding="utf-8")
    linea = p.stdout.readline().strip(); print("[servidor]", linea)
    return p, linea.split()[3]

def pedir(base, metodo, ruta, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(base + ruta, data=datos, method=metodo, headers={"Content-Type": "application/json"} if datos else {})
    try:
        with urllib.request.urlopen(req) as r: estado, txt = r.status, r.read().decode()
    except urllib.error.HTTPError as e: estado, txt = e.code, e.read().decode()
    cuerpo_txt = f" {json.dumps(cuerpo, ensure_ascii=False)}" if cuerpo is not None else ""
    print(f"{metodo} {ruta}{cuerpo_txt}\n  -> HTTP {estado} {txt}")

p, base = arrancar()
pedir(base, "POST", "/api/reservas", {"unidad": "MIC-01", "solicitante": "Ana Prueba", "inicio": "2026-11-02T10:00", "fin": "2026-11-02T11:00"})
pedir(base, "POST", "/api/reservas", {"unidad": "MIC-01", "solicitante": "Beto Ficticio", "inicio": "2026-11-02T10:30", "fin": "2026-11-02T11:30"})
pedir(base, "POST", "/api/reservas", {"unidad": "MIC-01", "solicitante": "Beto Ficticio", "inicio": "2026-11-02T11:00", "fin": "2026-11-02T12:00"})
pedir(base, "POST", "/api/reservas", {"unidad": "MIC-02", "solicitante": "   ", "inicio": "2026-11-02T10:00", "fin": "2026-11-02T11:00"})
pedir(base, "POST", "/api/reservas/1/cancelar", {})
pedir(base, "GET", "/api/disponibilidad?unidad=MIC-01&inicio=2026-11-02T10:00&fin=2026-11-02T11:00")
p.terminate(); p.wait(); print("[servidor detenido]\n")
p, base = arrancar()
pedir(base, "GET", "/api/reservas")
p.terminate(); p.wait(); print("[servidor detenido]")
