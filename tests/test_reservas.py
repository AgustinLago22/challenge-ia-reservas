"""Criterios de aceptación CA-01 a CA-11 y CA-13 (docs/ESPECIFICACION.md §6)."""

import pytest

from reservas.dominio import (
    ACTIVA,
    CANCELADA,
    ConflictoError,
    ErrorValidacion,
    ReservaNoEncontrada,
    ReservaYaCancelada,
)

from .conftest import t


def test_ca01_crear_reserva_valida(servicio):
    r = servicio.crear_reserva("MIC-01", "Ana Prueba", t("10:00"), t("11:00"))

    assert isinstance(r.id, int)
    assert (r.unidad, r.solicitante, r.inicio_txt, r.fin_txt) == ("MIC-01", "Ana Prueba", t("10:00"), t("11:00"))
    assert r.estado == ACTIVA
    assert r.cancelada_en is None
    assert servicio.listar_reservas() == [r]


def test_ca01_ids_unicos_y_crecientes(servicio):
    """R15: cada reserva tiene un ID propio que no se reutiliza."""
    a = servicio.crear_reserva("MIC-01", "Ana Prueba", t("10:00"), t("11:00"))
    b = servicio.crear_reserva("OSC-01", "Beto Ficticio", t("10:00"), t("11:00"))
    servicio.cancelar_reserva(b.id)
    c = servicio.crear_reserva("OSC-01", "Beto Ficticio", t("10:00"), t("11:00"))
    assert a.id < b.id < c.id


def test_ca01_solicitante_se_guarda_sin_espacios_extremos(servicio):
    r = servicio.crear_reserva("MIC-01", "  Ana Prueba  ", t("10:00"), t("11:00"))
    assert r.solicitante == "Ana Prueba"


@pytest.mark.parametrize(
    "inicio, fin",
    [("10:30", "11:30"), ("09:30", "10:30"), ("10:15", "10:45"), ("09:00", "12:00"), ("10:00", "11:00")],
)
def test_ca02_rechaza_superposicion_misma_unidad(servicio, mic01_10a11, inicio, fin):
    with pytest.raises(ConflictoError) as exc:
        servicio.crear_reserva("MIC-01", "Beto Ficticio", t(inicio), t(fin))
    assert exc.value.conflictos == [mic01_10a11]
    assert f"#{mic01_10a11.id}" in str(exc.value)


@pytest.mark.parametrize("inicio, fin", [("11:00", "12:00"), ("09:00", "10:00")])
def test_ca03_limites_consecutivos_permitidos(servicio, mic01_10a11, inicio, fin):
    r = servicio.crear_reserva("MIC-01", "Beto Ficticio", t(inicio), t(fin))
    assert r.estado == ACTIVA


def test_ca03_encadenar_tres_turnos_consecutivos(servicio, mic01_10a11):
    servicio.crear_reserva("MIC-01", "Beto Ficticio", t("09:00"), t("10:00"))
    servicio.crear_reserva("MIC-01", "Carla Inventada", t("11:00"), t("12:00"))
    assert len(servicio.listar_reservas(unidad="MIC-01", estado=ACTIVA)) == 3


def test_ca04_unidades_distintas_simultaneas(servicio, mic01_10a11):
    r = servicio.crear_reserva("MIC-02", "Beto Ficticio", t("10:00"), t("11:00"))
    assert r.unidad == "MIC-02"
    # Todas las demás unidades también, en el mismo horario.
    for unidad in ("OSC-01", "MUL-01", "FUE-01"):
        servicio.crear_reserva(unidad, "Carla Inventada", t("10:00"), t("11:00"))
    assert len(servicio.listar_reservas(estado=ACTIVA)) == 5


@pytest.mark.parametrize("unidad", ["XYZ-99", "mic-01", "MIC-01 ", "", None])
def test_ca05_rechaza_unidad_desconocida(servicio, unidad):
    with pytest.raises(ErrorValidacion, match="Unidad desconocida"):
        servicio.crear_reserva(unidad, "Ana Prueba", t("10:00"), t("11:00"))


@pytest.mark.parametrize("solicitante", ["", " ", "     ", "\t", " \t \n ", None])
def test_ca06_rechaza_solicitante_vacio_o_solo_espacios(servicio, solicitante):
    with pytest.raises(ErrorValidacion, match="solicitante"):
        servicio.crear_reserva("MIC-01", solicitante, t("10:00"), t("11:00"))


@pytest.mark.parametrize(
    "valor",
    [
        "2026-02-30T10:00",  # día inexistente
        "2026-11-02T25:00",  # hora inexistente
        "2026-11-02T10:60",  # minuto inexistente
        "2026-13-02T10:00",  # mes inexistente
        "02/11/2026 10:00",  # otro formato
        "2026-11-02 10:00",  # sin la T
        "2026-11-02T10:00:00",  # con segundos
        "2026-11-02",  # sin hora
        "mañana a las diez",
        "",
        None,
    ],
)
def test_ca07_rechaza_fechas_invalidas(servicio, valor):
    with pytest.raises(ErrorValidacion, match="(?i)fecha"):
        servicio.crear_reserva("MIC-01", "Ana Prueba", valor, t("11:00"))
    with pytest.raises(ErrorValidacion, match="(?i)fecha"):
        servicio.crear_reserva("MIC-01", "Ana Prueba", t("10:00"), valor)


@pytest.mark.parametrize("inicio, fin", [("11:00", "11:00"), ("11:00", "10:00"), ("10:00", "09:59")])
def test_ca07_rechaza_inicio_no_anterior_al_fin(servicio, inicio, fin):
    with pytest.raises(ErrorValidacion, match="estrictamente anterior"):
        servicio.crear_reserva("MIC-01", "Ana Prueba", t(inicio), t(fin))


def test_ca07_reserva_de_varios_dias_es_valida(servicio):
    """Supuesto: sin límite de duración."""
    r = servicio.crear_reserva("FUE-01", "Ana Prueba", t("18:00"), t("09:00", dia="2026-11-04"))
    assert r.estado == ACTIVA


def test_ca08_rechaza_inicio_en_el_pasado(servicio):
    # AHORA = 2026-11-01T08:00
    with pytest.raises(ErrorValidacion, match="ya pasó"):
        servicio.crear_reserva("MIC-01", "Ana Prueba", "2026-11-01T07:59", "2026-11-01T09:00")


def test_ca08_permite_inicio_en_el_minuto_actual(servicio):
    r = servicio.crear_reserva("MIC-01", "Ana Prueba", "2026-11-01T08:00", "2026-11-01T09:00")
    assert r.estado == ACTIVA


def test_ca08_los_segundos_del_reloj_no_rechazan_el_minuto_actual(inventario, repo):
    from datetime import datetime

    from reservas.servicio import ServicioReservas

    servicio = ServicioReservas(inventario, repo, reloj=lambda: datetime(2026, 11, 1, 8, 0, 45))
    r = servicio.crear_reserva("MIC-01", "Ana Prueba", "2026-11-01T08:00", "2026-11-01T09:00")
    assert r.creada_en == "2026-11-01T08:00:00"


def test_ca08_se_puede_consultar_disponibilidad_en_el_pasado(servicio):
    d = servicio.consultar_disponibilidad("MIC-01", "2026-10-01T10:00", "2026-10-01T11:00")
    assert d.disponible


def test_ca09_disponibilidad_usa_las_mismas_reglas(servicio, mic01_10a11):
    ocupado = servicio.consultar_disponibilidad("MIC-01", t("10:30"), t("11:30"))
    assert not ocupado.disponible
    assert ocupado.conflictos == (mic01_10a11,)

    assert servicio.consultar_disponibilidad("MIC-01", t("11:00"), t("12:00")).disponible
    assert servicio.consultar_disponibilidad("MIC-01", t("09:00"), t("10:00")).disponible
    assert servicio.consultar_disponibilidad("MIC-02", t("10:00"), t("11:00")).disponible


@pytest.mark.parametrize(
    "inicio, fin",
    [("10:30", "11:30"), ("09:30", "10:30"), ("11:00", "12:00"), ("09:00", "10:00"), ("10:00", "11:00")],
)
def test_ca09_consulta_y_creacion_coinciden(servicio, mic01_10a11, inicio, fin):
    """R13: si la consulta dice 'disponible', crear funciona; si dice 'ocupado', crear se rechaza."""
    disponible = servicio.consultar_disponibilidad("MIC-01", t(inicio), t(fin)).disponible
    try:
        servicio.crear_reserva("MIC-01", "Beto Ficticio", t(inicio), t(fin))
        creada = True
    except ConflictoError:
        creada = False
    assert disponible == creada


def test_ca09_disponibilidad_valida_entradas(servicio):
    with pytest.raises(ErrorValidacion, match="Unidad desconocida"):
        servicio.consultar_disponibilidad("XYZ-99", t("10:00"), t("11:00"))
    with pytest.raises(ErrorValidacion, match="estrictamente anterior"):
        servicio.consultar_disponibilidad("MIC-01", t("11:00"), t("10:00"))
    with pytest.raises(ErrorValidacion, match="(?i)fecha"):
        servicio.consultar_disponibilidad("MIC-01", "2026-02-30T10:00", t("11:00"))


def test_ca09_disponibilidad_de_todas_las_unidades(servicio, mic01_10a11):
    resultado = {d.unidad: d.disponible for d in servicio.consultar_disponibilidad_todas(t("10:00"), t("11:00"))}
    assert resultado == {"MIC-01": False, "MIC-02": True, "OSC-01": True, "MUL-01": True, "FUE-01": True}


def test_ca10_cancelar_conserva_datos_y_libera_horario(servicio, mic01_10a11):
    cancelada = servicio.cancelar_reserva(mic01_10a11.id)

    assert cancelada.id == mic01_10a11.id
    assert (cancelada.unidad, cancelada.solicitante, cancelada.inicio, cancelada.fin) == (
        mic01_10a11.unidad,
        mic01_10a11.solicitante,
        mic01_10a11.inicio,
        mic01_10a11.fin,
    )
    assert cancelada.estado == CANCELADA
    assert cancelada.cancelada_en == "2026-11-01T08:00:00"
    assert cancelada.creada_en == mic01_10a11.creada_en

    # El historial conserva el registro...
    assert servicio.listar_reservas(estado=CANCELADA) == [cancelada]
    # ...y el horario quedó libre para consultar y reservar.
    assert servicio.consultar_disponibilidad("MIC-01", t("10:00"), t("11:00")).disponible
    nueva = servicio.crear_reserva("MIC-01", "Beto Ficticio", t("10:00"), t("11:00"))
    assert nueva.id != cancelada.id
    assert len(servicio.listar_reservas()) == 2


def test_ca10_cancelar_solo_libera_esa_reserva(servicio, mic01_10a11):
    otra = servicio.crear_reserva("MIC-01", "Beto Ficticio", t("11:00"), t("12:00"))
    servicio.cancelar_reserva(mic01_10a11.id)
    assert not servicio.consultar_disponibilidad("MIC-01", t("11:30"), t("12:30")).disponible
    assert servicio.listar_reservas(estado=ACTIVA) == [otra]


def test_ca11_cancelar_inexistente_se_rechaza(servicio, mic01_10a11):
    with pytest.raises(ReservaNoEncontrada):
        servicio.cancelar_reserva(9999)
    assert servicio.listar_reservas() == [mic01_10a11]


def test_ca11_cancelar_dos_veces_se_rechaza_sin_cambios(servicio, mic01_10a11):
    primera = servicio.cancelar_reserva(mic01_10a11.id)
    with pytest.raises(ReservaYaCancelada):
        servicio.cancelar_reserva(mic01_10a11.id)
    assert servicio.listar_reservas() == [primera]


@pytest.mark.parametrize("id_invalido", ["1", 1.0, None, True])
def test_ca11_cancelar_con_id_invalido(servicio, mic01_10a11, id_invalido):
    with pytest.raises(ErrorValidacion):
        servicio.cancelar_reserva(id_invalido)
    assert servicio.listar_reservas() == [mic01_10a11]


def test_ca13_rechazos_no_modifican_datos(servicio, mic01_10a11):
    antes = servicio.listar_reservas()
    intentos = [
        ("MIC-01", "Beto Ficticio", t("10:30"), t("11:30")),  # superposición
        ("XYZ-99", "Beto Ficticio", t("10:00"), t("11:00")),  # unidad desconocida
        ("MIC-02", "   ", t("10:00"), t("11:00")),  # solicitante vacío
        ("MIC-02", "Beto Ficticio", "2026-02-30T10:00", t("11:00")),  # fecha inválida
        ("MIC-02", "Beto Ficticio", t("11:00"), t("10:00")),  # inicio >= fin
        ("MIC-02", "Beto Ficticio", "2026-10-01T10:00", "2026-10-01T11:00"),  # pasado
    ]
    for intento in intentos:
        with pytest.raises(Exception):
            servicio.crear_reserva(*intento)
    assert servicio.listar_reservas() == antes


def test_ca13_conflicto_no_deja_la_transaccion_abierta(servicio, mic01_10a11):
    """Después de un rechazo dentro de la transacción, la base sigue aceptando escrituras."""
    with pytest.raises(ConflictoError):
        servicio.crear_reserva("MIC-01", "Beto Ficticio", t("10:30"), t("11:30"))
    assert servicio.crear_reserva("MIC-01", "Beto Ficticio", t("11:00"), t("12:00")).estado == ACTIVA


def test_listar_valida_filtros(servicio):
    with pytest.raises(ErrorValidacion):
        servicio.listar_reservas(unidad="XYZ-99")
    with pytest.raises(ErrorValidacion):
        servicio.listar_reservas(estado="BORRADA")


def test_reiniciar_datos_exige_confirmacion(servicio, mic01_10a11):
    with pytest.raises(ErrorValidacion):
        servicio.reiniciar_datos(confirmar=False)
    assert servicio.listar_reservas() == [mic01_10a11]
    assert servicio.reiniciar_datos(confirmar=True) == 1
    assert servicio.listar_reservas() == []
