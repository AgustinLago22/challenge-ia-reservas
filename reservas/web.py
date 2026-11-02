"""Interfaz web local: una página estática y una API JSON sobre ServicioReservas.

Como la CLI, no tiene lógica de negocio: traduce HTTP <-> servicio. Cada pedido abre su
propia conexión SQLite (el servidor atiende en hilos y una conexión no se comparte entre hilos).

Rutas:
  GET  /                              página (reservas/static/index.html)
  GET  /api/info                      "ahora" del servidor y ruta de la base
  GET  /api/unidades                  inventario
  GET  /api/reservas?unidad=&estado=&orden=  historial (orden: creacion, creacion_desc, fecha, fecha_desc)
  GET  /api/disponibilidad?unidad=<ID|todas>&inicio=&fin=
  POST /api/reservas                  {"unidad", "solicitante", "inicio", "fin"} -> 201
  POST /api/reservas/<id>/cancelar    -> 200
Errores: 400 entrada inválida, 404 inexistente, 409 conflicto o ya cancelada,
415 POST sin JSON. No hay ruta de reinicio de datos (solo en la consola).
"""

from __future__ import annotations

import json
import re
import socket
import sqlite3
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

from .dominio import (
    ConflictoError,
    Disponibilidad,
    ErrorValidacion,
    Reserva,
    ReservaError,
    ReservaNoEncontrada,
    ReservaYaCancelada,
    ahora_local,
    formatear_fecha,
)
from .repositorio import RepositorioSQLite
from .servicio import Reloj, ServicioReservas

HOST = "127.0.0.1"
PAGINA = Path(__file__).resolve().parent / "static" / "index.html"
TODAS = "todas"
MAX_CUERPO = 10_000
_RUTA_CANCELAR = re.compile(r"^/api/reservas/(\d+)/cancelar$")


def reserva_a_json(r: Reserva) -> dict:
    return {
        "id": r.id,
        "unidad": r.unidad,
        "solicitante": r.solicitante,
        "inicio": r.inicio_txt,
        "fin": r.fin_txt,
        "estado": r.estado,
        "creada_en": r.creada_en,
        "cancelada_en": r.cancelada_en,
    }


def disponibilidad_a_json(d: Disponibilidad) -> dict:
    return {
        "unidad": d.unidad,
        "inicio": formatear_fecha(d.inicio),
        "fin": formatear_fecha(d.fin),
        "disponible": d.disponible,
        "conflictos": [reserva_a_json(r) for r in d.conflictos],
    }


def estado_http(exc: ReservaError) -> HTTPStatus:
    if isinstance(exc, (ConflictoError, ReservaYaCancelada)):
        return HTTPStatus.CONFLICT
    if isinstance(exc, ReservaNoEncontrada):
        return HTTPStatus.NOT_FOUND
    return HTTPStatus.BAD_REQUEST


class ServidorLocal(ThreadingHTTPServer):
    """En Windows, SO_REUSEADDR (activado por defecto en http.server) deja que un segundo servidor
    se enlace a un puerto YA EN USO sin dar error (comprobado en el episodio 4). Se pide uso exclusivo."""

    daemon_threads = True
    allow_reuse_address = sys.platform != "win32"

    def server_bind(self) -> None:
        if sys.platform == "win32":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def _parametro(consulta: dict[str, list[str]], nombre: str) -> str | None:
    valores = consulta.get(nombre)
    return valores[0] if valores else None


def crear_servidor(
    ruta_db: str | Path,
    inventario: dict[str, str],
    reloj: Reloj = ahora_local,
    puerto: int = 8000,
    host: str = HOST,
) -> ServidorLocal:
    """Crea (sin iniciar) el servidor. puerto=0 elige uno libre; ver servidor.server_address."""

    class Manejador(BaseHTTPRequestHandler):
        server_version = "ReservasLab/1.0"

        # --- respuestas ---------------------------------------------------------------
        def _enviar(self, estado: int, cuerpo: bytes, tipo: str) -> None:
            self.send_response(estado)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(cuerpo)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(cuerpo)

        def _json(self, estado: int, datos: object) -> None:
            self._enviar(estado, json.dumps(datos, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

        def _error(self, estado: int, mensaje: str, **extra: object) -> None:
            self._json(estado, {"error": mensaje, **extra})

        # --- controles ----------------------------------------------------------------
        def _host_valido(self) -> bool:
            """Solo uso local: rechaza pedidos con un Host ajeno (protección contra DNS rebinding)."""
            puerto_real = self.server.server_address[1]
            return self.headers.get("Host") in {f"127.0.0.1:{puerto_real}", f"localhost:{puerto_real}"}

        def _leer_cuerpo(self) -> bytes:
            """Lee SIEMPRE el cuerpo antes de responder. Si el servidor cierra la conexión con datos sin
            leer, Windows puede cortarla (RST) antes de que el cliente lea la respuesta: se vio una vez como
            ConnectionAbortedError en las pruebas (D-24)."""
            try:
                largo = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                largo = -1
            if largo < 0:
                raise ErrorValidacion("Content-Length inválido.")
            if largo > MAX_CUERPO:
                restante = min(largo, 1_000_000)  # descartar (con tope) para cerrar la conexión limpiamente
                while restante > 0 and (bloque := self.rfile.read(min(restante, 65_536))):
                    restante -= len(bloque)
                raise ErrorValidacion("El pedido es demasiado grande.")
            return self.rfile.read(largo)

        def _leer_json(self) -> dict:
            try:
                datos = json.loads(self._cuerpo.decode("utf-8") or "null")
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise ErrorValidacion("El cuerpo del pedido no es JSON válido.") from None
            if not isinstance(datos, dict):
                raise ErrorValidacion("El cuerpo debe ser un objeto JSON con unidad, solicitante, inicio y fin.")
            return datos

        def _con_servicio(self, accion: Callable[[ServicioReservas], tuple[int, object]]) -> None:
            try:
                with RepositorioSQLite(ruta_db) as repo:
                    estado, datos = accion(ServicioReservas(inventario, repo, reloj))
            except ConflictoError as exc:
                self._error(estado_http(exc), str(exc), conflictos=[reserva_a_json(r) for r in exc.conflictos])
            except ReservaError as exc:
                self._error(estado_http(exc), str(exc))
            except sqlite3.Error as exc:
                self._error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Error de base de datos: {exc}")
            else:
                self._json(estado, datos)

        # --- rutas --------------------------------------------------------------------
        def do_GET(self) -> None:
            if not self._host_valido():
                return self._error(HTTPStatus.BAD_REQUEST, "Host no permitido: el servidor es solo local.")
            url = urlparse(self.path)
            q = parse_qs(url.query)
            if url.path in ("/", "/index.html"):
                self._enviar(HTTPStatus.OK, PAGINA.read_bytes(), "text/html; charset=utf-8")
            elif url.path == "/api/info":
                self._json(HTTPStatus.OK, {"ahora": formatear_fecha(reloj()), "base": str(ruta_db)})
            elif url.path == "/api/unidades":
                self._json(HTTPStatus.OK, [{"id": u, "equipo": e} for u, e in inventario.items()])
            elif url.path == "/api/reservas":
                self._con_servicio(
                    lambda s: (
                        HTTPStatus.OK,
                        [
                            reserva_a_json(r)
                            for r in s.listar_reservas(
                                _parametro(q, "unidad") or None,
                                _parametro(q, "estado") or None,
                                _parametro(q, "orden") or "creacion",
                            )
                        ],
                    )
                )
            elif url.path == "/api/disponibilidad":
                unidad, inicio, fin = (_parametro(q, k) for k in ("unidad", "inicio", "fin"))

                def consultar(s: ServicioReservas) -> tuple[int, object]:
                    if unidad == TODAS:
                        resultados = s.consultar_disponibilidad_todas(inicio, fin)
                    else:
                        resultados = [s.consultar_disponibilidad(unidad, inicio, fin)]
                    return HTTPStatus.OK, [disponibilidad_a_json(d) for d in resultados]

                self._con_servicio(consultar)
            else:
                self._error(HTTPStatus.NOT_FOUND, f"Ruta inexistente: {url.path}")

        def do_POST(self) -> None:
            try:
                self._cuerpo = self._leer_cuerpo()
            except ErrorValidacion as exc:
                return self._error(HTTPStatus.BAD_REQUEST, str(exc))
            if not self._host_valido():
                return self._error(HTTPStatus.BAD_REQUEST, "Host no permitido: el servidor es solo local.")
            url = urlparse(self.path)
            cancelar = _RUTA_CANCELAR.match(url.path)
            if url.path != "/api/reservas" and not cancelar:
                return self._error(HTTPStatus.NOT_FOUND, f"Ruta inexistente: {url.path}")
            # Exigir JSON obliga al navegador a una verificación previa (CORS) que este servidor
            # no responde: otra página web no puede crear ni cancelar reservas en segundo plano.
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Use Content-Type: application/json.")
            if cancelar:
                self._con_servicio(lambda s: (HTTPStatus.OK, reserva_a_json(s.cancelar_reserva(int(cancelar.group(1))))))
            else:

                def crear(s: ServicioReservas) -> tuple[int, object]:
                    d = self._leer_json()
                    r = s.crear_reserva(d.get("unidad"), d.get("solicitante"), d.get("inicio"), d.get("fin"))
                    return HTTPStatus.CREATED, reserva_a_json(r)

                self._con_servicio(crear)

    return ServidorLocal((host, puerto), Manejador)
