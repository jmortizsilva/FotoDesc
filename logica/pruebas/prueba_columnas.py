import pytest

from logica import columnas
from logica.metadatos import Metadatos


@pytest.mark.parametrize("fecha, esperado", [
    ("16/04/2022", "16 de abril de 2022"),
    ("01/12/2021", "1 de diciembre de 2021"),
    ("", ""),
    ("2022-04-16", "2022-04-16"),
    ("16/13/2022", "16/13/2022"),
])
def prueba_fecha_legible(fecha, esperado):
    assert columnas.fecha_legible(fecha) == esperado


def prueba_ubicacion_con_coma_decimal_y_cuatro_cifras():
    assert columnas.ubicacion_legible((40.812345, -2.103456)) == "40,8123; -2,1035"
    assert columnas.ubicacion_legible(None) == ""


def prueba_valores_fila_en_el_orden_de_las_columnas():
    datos = Metadatos("Río con\nniebla", (40.8, -2.1), "16/04/2022", "10:05:30")
    assert columnas.valores_fila("IMG_1.jpg", datos) == [
        "IMG_1.jpg", "Río con niebla", "16 de abril de 2022", "10:05:30", "40,8000; -2,1000"]
    assert len(columnas.valores_fila("a", Metadatos())) == len(columnas.COLUMNAS)


def prueba_anuncio_nombre_y_valor_o_sin_datos():
    assert columnas.anuncio(2, "16 de abril de 2022") == "Fecha, 16 de abril de 2022"
    assert columnas.anuncio(4, "") == "Ubicación, sin datos"
    assert columnas.anuncio(4, "   ") == "Ubicación, sin datos"


def prueba_mover_avisa_en_los_extremos():
    assert columnas.mover(0, 1) == (1, False)
    assert columnas.mover(0, -1) == (0, True)
    ultima = len(columnas.COLUMNAS) - 1
    assert columnas.mover(ultima, 1) == (ultima, True)


def prueba_ubicacion_prefiere_el_lugar_guardado():
    from logica.lugares import Lugar
    con_lugar = Metadatos(gps=(40.8, -2.1), lugar=Lugar(localidad="Peralejos de las Truchas",
                                                          provincia="Guadalajara", codigo_pais="es"))
    assert columnas.texto_ubicacion(con_lugar) == "Peralejos de las Truchas, Guadalajara"
    solo_gps = Metadatos(gps=(40.8, -2.1))
    assert columnas.texto_ubicacion(solo_gps, buscando=True) == "buscando"
    assert columnas.texto_ubicacion(solo_gps) == "40,8000; -2,1000"
    assert columnas.texto_ubicacion(Metadatos(), buscando=True) == ""
