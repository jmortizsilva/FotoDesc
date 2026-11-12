import piexif
import pytest
from PIL import Image

from logica import metadatos


def prueba_fecha_exif_a_texto():
    assert metadatos.fecha_exif_a_texto("2022:04:16 10:05:30") == ("16/04/2022", "10:05:30")


@pytest.mark.parametrize("valor", ["", "2022:04:16", "2022-04-16 10:05:30", "basura con espacios"])
def prueba_fecha_exif_mal_formada(valor):
    assert metadatos.fecha_exif_a_texto(valor) == ("", "")


def prueba_texto_a_fecha_exif():
    assert metadatos.texto_a_fecha_exif("16/04/2022", "10:05:30") == "2022:04:16 10:05:30"
    assert metadatos.texto_a_fecha_exif("16/04/2022", "") is None
    assert metadatos.texto_a_fecha_exif("16-04-2022", "10:05:30") is None


@pytest.mark.parametrize("texto, esperado", [("40,5", 40.5), (" -3.25 ", -3.25), ("", None), ("norte", None)])
def prueba_leer_coordenada(texto, esperado):
    assert metadatos.leer_coordenada(texto) == esperado


def prueba_extraer_de_exif_vacio():
    assert metadatos.extraer_metadatos(metadatos.exif_vacio()) == metadatos.Metadatos()


def prueba_escribir_y_leer_en_el_diccionario():
    exif = metadatos.exif_vacio()
    metadatos.poner_descripcion(exif, "Barranco del río Tajo, con niebla")
    metadatos.poner_fecha(exif, "16/04/2022", "10:05:30")
    metadatos.poner_gps(exif, 40.8, -2.1)
    datos = metadatos.extraer_metadatos(exif)
    assert datos.descripcion == "Barranco del río Tajo, con niebla"
    assert (datos.fecha, datos.hora) == ("16/04/2022", "10:05:30")
    assert datos.gps == pytest.approx((40.8, -2.1), abs=1e-5)


def prueba_fecha_incompleta_no_toca_la_existente():
    exif = metadatos.exif_vacio()
    metadatos.poner_fecha(exif, "16/04/2022", "10:05:30")
    metadatos.poner_fecha(exif, "", "")
    assert exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2022:04:16 10:05:30"


def prueba_guardar_y_leer_un_jpeg_real(tmp_path):
    ruta = tmp_path / "foto.jpg"
    Image.new("RGB", (32, 32), "green").save(ruta, "jpeg")
    assert metadatos.leer_metadatos(str(ruta)) == metadatos.Metadatos()

    exif = metadatos.leer_exif(str(ruta))
    metadatos.poner_descripcion(exif, "Una prueba con eñe")
    metadatos.guardar_exif(str(ruta), exif)
    assert metadatos.leer_metadatos(str(ruta)).descripcion == "Una prueba con eñe"


def prueba_archivo_que_no_es_imagen_devuelve_vacio(tmp_path):
    ruta = tmp_path / "nota.jpg"
    ruta.write_text("no soy una foto")
    assert metadatos.leer_metadatos(str(ruta)) == metadatos.Metadatos()


def prueba_guardar_no_recomprime_la_imagen(tmp_path):
    ruta = tmp_path / "foto.jpg"
    Image.new("RGB", (64, 64), "red").save(ruta, "jpeg", quality=95)

    def datos_de_imagen():
        # Lo que va después del EXIF: si cambia, se ha recomprimido.
        contenido = ruta.read_bytes()
        return contenido[contenido.index(b"\xff\xdb"):]

    antes = datos_de_imagen()
    for texto in ("primera", "segunda", "tercera"):
        exif = metadatos.leer_exif(str(ruta))
        metadatos.poner_descripcion(exif, texto)
        metadatos.guardar_exif(str(ruta), exif)
    assert datos_de_imagen() == antes
    assert metadatos.leer_metadatos(str(ruta)).descripcion == "tercera"


def prueba_png_se_rechaza_sin_tocar_el_archivo(tmp_path):
    ruta = tmp_path / "captura.png"
    Image.new("RGB", (8, 8), "white").save(ruta, "png")
    original = ruta.read_bytes()
    with pytest.raises(metadatos.FormatoNoSoportado):
        metadatos.guardar_exif(str(ruta), metadatos.exif_vacio())
    assert ruta.read_bytes() == original
    assert [p.name for p in tmp_path.iterdir()] == ["captura.png"]
