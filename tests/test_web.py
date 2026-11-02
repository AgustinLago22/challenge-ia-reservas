"""CA-14: la interfaz web local aplica las mismas reglas que la consola.

Se prueba por HTTP real: un servidor en un hilo con puerto libre (puerto=0) y, en una prueba,
el proceso real `python -m reservas web`.
"""

import json
import os
import subprocess
import sys
import threading
import urllib.error
import urllib.request

import pytest

from reservas.web import PAGINA, crear_servidor

from .conftest import AHORA, t

RAIZ = PAGINA.parent.parent.parent


class Cliente:
    def __init__(self, servidor):
        self.servidor = servidor
        self.base = f"http://127.0.0.1:{servidor.server_address[1]}"

    def pedir(self, metodo, ruta, cuerpo=None, encabezados=None, crudo=None):
        datos = crudo if crudo is not None else (json.dumps(cuerpo).encode() if cuerpo is not None else None)
        enc = {"Content-Type": "application/json"} if datos is not None else {}
        enc.update(encabezados or {})
        pedido = urllib.request.Request(self.base + ruta, data=datos, method=metodo, headers=enc)
        try:
            with urllib.request.urlopen(pedido, timeout=10) as r:
                estado, tipo, texto = r.status, r.headers["Content-Type"], r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            estado, tipo, texto = e.code, e.headers["Content-Type"], e.read().decode("utf-8")
        return estado, (json.loads(texto) if tipo.startswith("application/json") else texto)

    def reservar(self, unidad, inicio, fin, solicitante="Ana Prueba"):
        return self.pedir("POST", "/api/reservas", {"unidad": unidad, "solicitante": solicitante, "inicio": inicio, "fin": fin})


def _iniciar(ruta_db, inventario):
    servidor = crear_servidor(ruta_db, inventario, reloj=lambda: AHORA, puerto=0)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return servidor


def _detener(servidor):
    servidor.shutdown()
    servidor.server_close()


@pytest.fixture
def web(ruta_db, inventario):
    servidor = _iniciar(ruta_db, inventario)
    yield Cliente(servidor)
    _detener(servidor)


def test_ca14_solo_escucha_en_localhost(web):
    assert web.servidor.server_address[0] == "127.0.0.1"


def test_ca14_pagina_principal(web):
    estado, html = web.pedir("GET", "/")
    assert estado == 200
    assert "<title>Reservas de laboratorio</title>" in html and 'id="form-reserva"' in html


def test_ca14_la_pagina_no_inserta_html_del_usuario():
    """La página muestra el texto con textContent; usar innerHTML permitiría inyectar HTML con el solicitante."""
    assert "innerHTML" not in PAGINA.read_text(encoding="utf-8")


def test_ca14_info_y_unidades(web):
    assert web.pedir("GET", "/api/info")[1]["ahora"] == "2026-11-01T08:00"
    estado, unidades = web.pedir("GET", "/api/unidades")
    assert estado == 200 and [u["id"] for u in unidades] == ["MIC-01", "MIC-02", "OSC-01", "MUL-01", "FUE-01"]


def test_ca14_ejemplo_del_enunciado_por_http(web):
    estado, r1 = web.reservar("MIC-01", t("10:00"), t("11:00"))
    assert estado == 201 and r1["id"] == 1 and r1["estado"] == "ACTIVA" and r1["solicitante"] == "Ana Prueba"

    estado, error = web.reservar("MIC-01", t("10:30"), t("11:30"), "Beto Ficticio")
    assert estado == 409
    assert "ya está reservada" in error["error"] and [c["id"] for c in error["conflictos"]] == [1]

    assert web.reservar("MIC-01", t("11:00"), t("12:00"), "Beto Ficticio")[0] == 201  # consecutivo
    assert web.reservar("MIC-02", t("10:00"), t("11:00"), "Carla Inventada")[0] == 201  # otra unidad


@pytest.mark.parametrize(
    "unidad, solicitante, inicio, fin, mensaje",
    [
        ("XYZ-99", "Ana Prueba", t("10:00"), t("11:00"), "Unidad desconocida"),
        ("MIC-01", "   ", t("10:00"), t("11:00"), "solicitante"),
        ("MIC-01", None, t("10:00"), t("11:00"), "solicitante"),
        ("MIC-01", "Ana Prueba", "2026-02-30T10:00", t("11:00"), "Fecha de inicio inválida"),
        ("MIC-01", "Ana Prueba", "", t("11:00"), "obligatoria"),
        ("MIC-01", "Ana Prueba", t("11:00"), t("10:00"), "estrictamente anterior"),
        ("MIC-01", "Ana Prueba", t("10:00"), t("10:00"), "estrictamente anterior"),
        ("MIC-01", "Ana Prueba", "2026-10-01T10:00", "2026-10-01T11:00", "ya pasó"),
    ],
)
def test_ca14_entradas_invalidas_devuelven_400(web, unidad, solicitante, inicio, fin, mensaje):
    estado, error = web.reservar(unidad, inicio, fin, solicitante)
    assert estado == 400 and mensaje in error["error"]
    assert web.pedir("GET", "/api/reservas")[1] == []  # CA-13: el rechazo no guardó nada


@pytest.mark.parametrize(
    "crudo, encabezados, estado_esperado",
    [
        (b"esto no es json", None, 400),
        (b"[1, 2]", None, 400),
        (b"\xff\xfe", None, 400),
        (b'{"unidad": "MIC-01"}', {"Content-Type": "text/plain"}, 415),
    ],
)
def test_ca14_cuerpos_invalidos(web, crudo, encabezados, estado_esperado):
    estado, error = web.pedir("POST", "/api/reservas", crudo=crudo, encabezados=encabezados)
    assert estado == estado_esperado and "error" in error


def test_ca14_disponibilidad(web):
    web.reservar("MIC-01", t("10:00"), t("11:00"))
    q = "/api/disponibilidad?unidad={}&inicio={}&fin={}"

    estado, [ocupada] = web.pedir("GET", q.format("MIC-01", t("10:30"), t("11:30")))
    assert estado == 200 and ocupada["disponible"] is False and ocupada["conflictos"][0]["id"] == 1

    assert web.pedir("GET", q.format("MIC-01", t("11:00"), t("12:00")))[1][0]["disponible"] is True

    todas = web.pedir("GET", q.format("todas", t("10:00"), t("11:00")))[1]
    assert {d["unidad"]: d["disponible"] for d in todas} == {
        "MIC-01": False, "MIC-02": True, "OSC-01": True, "MUL-01": True, "FUE-01": True,
    }

    assert web.pedir("GET", q.format("XYZ-99", t("10:00"), t("11:00")))[0] == 400
    assert web.pedir("GET", q.format("MIC-01", t("11:00"), t("10:00")))[0] == 400
    assert web.pedir("GET", "/api/disponibilidad?unidad=MIC-01")[0] == 400  # faltan las fechas


def test_ca14_cancelar(web):
    web.reservar("MIC-01", t("10:00"), t("11:00"))

    estado, cancelada = web.pedir("POST", "/api/reservas/1/cancelar", {})
    assert estado == 200 and cancelada["estado"] == "CANCELADA" and cancelada["cancelada_en"] == "2026-11-01T08:00:00"
    assert cancelada["solicitante"] == "Ana Prueba" and cancelada["inicio"] == t("10:00")

    assert web.pedir("POST", "/api/reservas/1/cancelar", {})[0] == 409  # ya cancelada
    assert web.pedir("POST", "/api/reservas/99/cancelar", {})[0] == 404  # inexistente
    assert web.pedir("POST", "/api/reservas/1/cancelar", crudo=b"{}", encabezados={"Content-Type": "text/plain"})[0] == 415

    # El horario quedó libre y el historial conserva el registro.
    assert web.reservar("MIC-01", t("10:00"), t("11:00"), "Beto Ficticio")[0] == 201
    assert [(r["id"], r["estado"]) for r in web.pedir("GET", "/api/reservas")[1]] == [(1, "CANCELADA"), (2, "ACTIVA")]


def test_ca14_listar_con_filtros(web):
    web.reservar("MIC-01", t("10:00"), t("11:00"))
    web.reservar("OSC-01", t("10:00"), t("11:00"))
    web.pedir("POST", "/api/reservas/2/cancelar", {})
    assert [r["id"] for r in web.pedir("GET", "/api/reservas?estado=ACTIVA")[1]] == [1]
    assert [r["id"] for r in web.pedir("GET", "/api/reservas?estado=CANCELADA")[1]] == [2]
    assert [r["id"] for r in web.pedir("GET", "/api/reservas?unidad=OSC-01&estado=")[1]] == [2]
    assert web.pedir("GET", "/api/reservas?estado=BORRADA")[0] == 400


def test_ca14_rutas_inexistentes_y_sin_reinicio_de_datos(web):
    assert web.pedir("GET", "/api/nada")[0] == 404
    assert web.pedir("POST", "/api/reiniciar-datos", {})[0] == 404
    assert web.pedir("POST", "/api/reservas/abc/cancelar", {})[0] == 404


def test_ca14_rechaza_host_ajeno(web):
    estado, error = web.pedir("GET", "/api/unidades", encabezados={"Host": "sitio-ajeno.example"})
    assert estado == 400 and "solo local" in error["error"]
    assert web.pedir("GET", "/api/unidades", encabezados={"Host": f"localhost:{web.servidor.server_address[1]}"})[0] == 200


def test_ca14_persistencia_al_reiniciar_el_servidor(ruta_db, inventario):
    primero = Cliente(_iniciar(ruta_db, inventario))
    primero.reservar("MIC-01", t("10:00"), t("11:00"))
    primero.reservar("OSC-01", t("14:00"), t("15:00"), "Beto Ficticio")
    primero.pedir("POST", "/api/reservas/2/cancelar", {})
    _detener(primero.servidor)

    segundo = Cliente(_iniciar(ruta_db, inventario))
    try:
        assert [(r["id"], r["estado"]) for r in segundo.pedir("GET", "/api/reservas")[1]] == [(1, "ACTIVA"), (2, "CANCELADA")]
        assert segundo.reservar("MIC-01", t("10:30"), t("11:30"))[0] == 409  # la activa sigue bloqueando
        assert segundo.reservar("OSC-01", t("14:00"), t("15:00"))[0] == 201  # la cancelada no
    finally:
        _detener(segundo.servidor)


def test_ca14_web_y_consola_comparten_los_datos(web, ruta_db):
    entorno = {**os.environ, "RESERVAS_DB": str(ruta_db), "RESERVAS_AHORA": "2026-11-01T08:00", "PYTHONIOENCODING": "utf-8"}

    def consola(*args):
        return subprocess.run([sys.executable, "-m", "reservas", *args], cwd=RAIZ, env=entorno,
                              capture_output=True, text=True, encoding="utf-8", timeout=30)

    web.reservar("MIC-01", t("10:00"), t("11:00"), "Desde La Web")
    assert "Desde La Web" in consola("listar").stdout

    assert consola("reservar", "--unidad", "MIC-01", "--solicitante", "Desde Consola",
                   "--inicio", t("10:30"), "--fin", t("11:30")).returncode == 1  # bloqueada por la de la web
    consola("reservar", "--unidad", "MIC-02", "--solicitante", "Desde Consola", "--inicio", t("10:00"), "--fin", t("11:00"))
    assert [r["solicitante"] for r in web.pedir("GET", "/api/reservas")[1]] == ["Desde La Web", "Desde Consola"]


def test_ca14_proceso_real_python_m_reservas_web(tmp_path):
    entorno = {**os.environ, "RESERVAS_DB": str(tmp_path / "proceso.db"), "PYTHONIOENCODING": "utf-8"}
    proceso = subprocess.Popen([sys.executable, "-m", "reservas", "web", "--puerto", "0"], cwd=RAIZ, env=entorno,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    try:
        linea = proceso.stdout.readline()
        assert linea.startswith("Página web en http://127.0.0.1:"), linea + proceso.stderr.read()
        url = linea.split()[3]
        with urllib.request.urlopen(url + "/api/unidades", timeout=10) as r:
            assert r.status == 200 and len(json.loads(r.read())) == 5
    finally:
        proceso.terminate()
        proceso.wait(timeout=10)


def test_ca14_puerto_ocupado_da_error_claro(web):
    puerto = web.servidor.server_address[1]
    resultado = subprocess.run([sys.executable, "-m", "reservas", "web", "--puerto", str(puerto)], cwd=RAIZ,
                               capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert resultado.returncode == 1 and "No se pudo iniciar el servidor" in resultado.stderr


def test_ca14_historial_ordenado(web):
    for unidad, dia in [("MIC-01", "2026-11-03"), ("OSC-01", "2026-11-02"), ("MUL-01", "2026-11-04"), ("FUE-01", "2026-11-02")]:
        web.reservar(unidad, t("10:00", dia), t("11:00", dia))
    ids = lambda orden: [r["id"] for r in web.pedir("GET", f"/api/reservas?orden={orden}")[1]]
    assert ids("fecha_desc") == [3, 1, 4, 2]
    assert ids("creacion_desc") == [4, 3, 2, 1]
    assert [r["id"] for r in web.pedir("GET", "/api/reservas")[1]] == [1, 2, 3, 4]  # sin orden: creación
    assert web.pedir("GET", "/api/reservas?orden=cualquiera")[0] == 400


@pytest.mark.parametrize(
    "ruta, encabezados, estado_esperado",
    [
        ("/api/reservas/1/cancelar", {"Content-Type": "application/json"}, 404),  # la ruta de cancelar no usa el cuerpo
        ("/api/reservas/1/cancelar", {"Content-Type": "text/plain"}, 415),
        ("/api/nada", None, 404),
        ("/api/reservas", {"Host": "sitio-ajeno.example"}, 400),
    ],
)
def test_ca14_rechazos_con_cuerpo_responden_sin_cortar_la_conexion(web, ruta, encabezados, estado_esperado):
    """D-24: el servidor lee el cuerpo antes de responder, también en los rechazos tempranos."""
    for _ in range(30):
        assert web.pedir("POST", ruta, crudo=b'{"x": "' + b"y" * 3000 + b'"}', encabezados=encabezados)[0] == estado_esperado


def test_ca14_cuerpo_demasiado_grande(web):
    estado, error = web.pedir("POST", "/api/reservas", crudo=b"{" + b" " * 20_000 + b"}")
    assert estado == 400 and "demasiado grande" in error["error"]
