"""Interfaz de consola: `python -m reservas <comando>`.

La CLI no tiene lógica de negocio: traduce argumentos, llama a ServicioReservas y
muestra el resultado. Códigos de salida: 0 = éxito, 1 = operación rechazada,
2 = uso incorrecto de la CLI (argparse).

Variables de entorno:
  RESERVAS_DB          ruta de la base SQLite (por defecto data/reservas.db)
  RESERVAS_INVENTARIO  ruta del inventario JSON (por defecto data/inventario.json)
  RESERVAS_AHORA       fija el "ahora" (YYYY-MM-DDTHH:MM) para pruebas y demos reproducibles

`python -m reservas web` abre la interfaz web local (reservas/web.py) sobre la misma base.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys

from .dominio import ACTIVA, CANCELADA, Disponibilidad, Reserva, ReservaError, ahora_local, formatear_fecha, parsear_fecha
from .inventario import RUTA_INVENTARIO, InventarioInvalido, cargar_inventario
from .repositorio import RUTA_DB, RepositorioSQLite
from .servicio import ServicioReservas

TODAS = "todas"


def _formato_reserva(r: Reserva) -> str:
    linea = f"#{r.id:<4} {r.unidad:<7} {r.estado:<10} {r.inicio_txt} -> {r.fin_txt}  {r.solicitante}"
    if r.cancelada_en:
        linea += f"  (cancelada {r.cancelada_en})"
    return linea


def _formato_disponibilidad(d: Disponibilidad) -> str:
    intervalo = f"{formatear_fecha(d.inicio)} -> {formatear_fecha(d.fin)}"
    if d.disponible:
        return f"{d.unidad:<7} DISPONIBLE  {intervalo}"
    choques = ", ".join(f"#{r.id} {r.inicio_txt}->{r.fin_txt} ({r.solicitante})" for r in d.conflictos)
    return f"{d.unidad:<7} OCUPADA     {intervalo}  conflicto con: {choques}"


def _crear_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m reservas",
        description="Reservas de equipos de laboratorio. Fechas en formato YYYY-MM-DDTHH:MM, hora de Argentina (UTC-3).",
    )
    sub = p.add_subparsers(dest="comando", required=True, metavar="comando")

    sub.add_parser("unidades", help="lista el inventario precargado")

    d = sub.add_parser("disponibilidad", help="consulta si una unidad (o todas) está libre en un intervalo")
    d.add_argument("--unidad", required=True, help=f"ID de unidad o '{TODAS}'")
    d.add_argument("--inicio", required=True)
    d.add_argument("--fin", required=True)

    r = sub.add_parser("reservar", help="crea una reserva")
    r.add_argument("--unidad", required=True)
    r.add_argument("--solicitante", required=True)
    r.add_argument("--inicio", required=True)
    r.add_argument("--fin", required=True)

    c = sub.add_parser("cancelar", help="cancela una reserva conservando su registro")
    c.add_argument("--id", required=True, type=int)

    li = sub.add_parser("listar", help="muestra el historial de reservas (activas y canceladas)")
    li.add_argument("--unidad")
    li.add_argument("--estado", choices=[ACTIVA, CANCELADA])

    rd = sub.add_parser("reiniciar-datos", help="BORRA TODAS las reservas (requiere --confirmar)")
    rd.add_argument("--confirmar", action="store_true", help="confirma el borrado de todas las reservas")

    w = sub.add_parser("web", help="abre la página web local en http://127.0.0.1:<puerto> (Ctrl+C para detener)")
    w.add_argument("--puerto", type=int, default=8000, help="puerto local (por defecto 8000; 0 = uno libre)")
    return p


def _reloj_desde_entorno():
    fijo = os.environ.get("RESERVAS_AHORA")
    if not fijo:
        return ahora_local
    ahora = parsear_fecha(fijo, "RESERVAS_AHORA")
    return lambda: ahora


def _ejecutar(args: argparse.Namespace, servicio: ServicioReservas) -> None:
    if args.comando == "unidades":
        for unidad, equipo in servicio.inventario.items():
            print(f"{unidad:<7} {equipo}")
    elif args.comando == "disponibilidad":
        if args.unidad == TODAS:
            resultados = servicio.consultar_disponibilidad_todas(args.inicio, args.fin)
        else:
            resultados = [servicio.consultar_disponibilidad(args.unidad, args.inicio, args.fin)]
        for d in resultados:
            print(_formato_disponibilidad(d))
    elif args.comando == "reservar":
        r = servicio.crear_reserva(args.unidad, args.solicitante, args.inicio, args.fin)
        print(f"Reserva creada: {_formato_reserva(r)}")
    elif args.comando == "cancelar":
        r = servicio.cancelar_reserva(args.id)
        print(f"Reserva cancelada: {_formato_reserva(r)}")
    elif args.comando == "listar":
        reservas = servicio.listar_reservas(args.unidad, args.estado)
        for r in reservas:
            print(_formato_reserva(r))
        if not reservas:
            print("(sin reservas)")
    elif args.comando == "reiniciar-datos":
        if not args.confirmar:
            raise ReservaError(
                "reiniciar-datos BORRA TODAS las reservas (activas y canceladas). "
                "No se borró nada; repita con --confirmar para hacerlo."
            )
        borradas = servicio.reiniciar_datos(confirmar=True)
        print(f"Datos reiniciados: se borraron {borradas} reservas. El inventario no se modificó.")


def _salida_utf8() -> None:
    """En Windows, con la salida redirigida, Python usa cp1252 y los acentos llegan rotos a
    Git Bash o a un archivo. Se fuerza UTF-8 (defecto hallado en el episodio 2)."""
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")


def _servir_web(puerto: int, ruta_db: str, inventario: dict[str, str], reloj) -> None:
    from .web import crear_servidor

    try:
        servidor = crear_servidor(ruta_db, inventario, reloj, puerto)
    except OSError as exc:  # p. ej. el puerto ya está en uso
        raise ReservaError(f"No se pudo iniciar el servidor en el puerto {puerto}: {exc}") from None
    print(f"Página web en http://127.0.0.1:{servidor.server_address[1]}  (base: {ruta_db}). Ctrl+C para detener.", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
        print("Servidor detenido. Los datos quedan guardados.", flush=True)


def main(argv: list[str] | None = None) -> int:
    _salida_utf8()
    args = _crear_parser().parse_args(argv)
    try:
        inventario = cargar_inventario(os.environ.get("RESERVAS_INVENTARIO") or RUTA_INVENTARIO)
        reloj = _reloj_desde_entorno()
        ruta_db = os.environ.get("RESERVAS_DB") or str(RUTA_DB)
        if args.comando == "web":
            _servir_web(args.puerto, ruta_db, inventario, reloj)
            return 0
        with RepositorioSQLite(ruta_db) as repo:
            _ejecutar(args, ServicioReservas(inventario, repo, reloj))
    except (ReservaError, InventarioInvalido, sqlite3.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
