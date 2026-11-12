import pytest

from logica.coordenadas import decimal_a_dms, dms_a_decimal, referencias


@pytest.mark.parametrize("valor, ref", [(40.416775, "N"), (-3.703790, "W"), (0.0, "N")])
def prueba_ida_y_vuelta_conserva_el_valor(valor, ref):
    vuelta = dms_a_decimal(decimal_a_dms(valor), ref)
    assert vuelta == pytest.approx(valor, abs=1e-5)


def prueba_sur_y_oeste_son_negativos():
    dms = ((10, 1), (30, 1), (0, 100))
    assert dms_a_decimal(dms, "S") == pytest.approx(-10.5)
    assert dms_a_decimal(dms, "W") == pytest.approx(-10.5)
    assert dms_a_decimal(dms, "N") == pytest.approx(10.5)


def prueba_tupla_mal_formada_devuelve_none():
    assert dms_a_decimal(((1, 0), (0, 1), (0, 1)), "N") is None
    assert dms_a_decimal(((1, 1),), "N") is None


def prueba_referencias_segun_signo():
    assert referencias(40, -3) == ("N", "W")
    assert referencias(-33, 151) == ("S", "E")
