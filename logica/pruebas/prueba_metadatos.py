import piexif
import pytest
from PIL import Image

from logica import jpeg, metadatos, xmp
from logica.metadatos import Cambios
from logica.pruebas.datos_apple import XMP_SOLO_DESCRIPCION


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


def prueba_la_descripcion_de_apple_manda_sobre_la_antigua():
    exif = metadatos.exif_vacio()
    exif["0th"][piexif.ImageIFD.ImageDescription] = "Escrita con la 1.0".encode()
    assert metadatos.extraer_metadatos(exif).descripcion == "Escrita con la 1.0"
    assert metadatos.extraer_metadatos(exif, XMP_SOLO_DESCRIPCION).descripcion == \
        "Un cielo al atardecer sobre el mar."


# ---------- Con archivos reales ----------

def foto(tmp_path, nombre="foto.jpg", descripcion_antigua=None, xmp_inicial=None):
    ruta = tmp_path / nombre
    exif = metadatos.exif_vacio()
    if descripcion_antigua:
        exif["0th"][piexif.ImageIFD.ImageDescription] = descripcion_antigua.encode()
    Image.new("RGB", (64, 64), "red").save(ruta, "jpeg", quality=95, exif=piexif.dump(exif))
    if xmp_inicial:
        ruta.write_bytes(jpeg.poner_xmp(ruta.read_bytes(), xmp_inicial))
    return ruta


def imagen_de(ruta):
    contenido = ruta.read_bytes()
    return contenido[contenido.index(b"\xff\xda"):]


def prueba_guardar_descripcion_va_a_xmp_y_quita_la_antigua(tmp_path):
    ruta = foto(tmp_path, descripcion_antigua="Escrita con la 1.0")
    assert metadatos.leer_metadatos(str(ruta)).descripcion == "Escrita con la 1.0"

    metadatos.guardar_cambios(str(ruta), Cambios(descripcion="Una prueba con eñe"))
    assert metadatos.leer_metadatos(str(ruta)).descripcion == "Una prueba con eñe"
    datos = ruta.read_bytes()
    # Fotos de Apple convierte EXIF ImageDescription también en pie de foto
    assert piexif.ImageIFD.ImageDescription not in piexif.load(datos)["0th"]
    assert xmp.leer_descripcion(jpeg.leer_xmp(datos)) == "Una prueba con eñe"


def prueba_sobre_una_foto_de_apple_conserva_su_xmp(tmp_path):
    ruta = foto(tmp_path, xmp_inicial=XMP_SOLO_DESCRIPCION)
    metadatos.guardar_cambios(str(ruta), Cambios(descripcion="Nueva"))
    paquete = jpeg.leer_xmp(ruta.read_bytes()).decode()
    assert "2026-11-11T10:56:28" in paquete
    assert metadatos.leer_metadatos(str(ruta)).descripcion == "Nueva"


def prueba_guardar_no_recomprime_la_imagen(tmp_path):
    ruta = foto(tmp_path)
    antes = imagen_de(ruta)
    for texto in ("primera", "segunda", "tercera"):
        metadatos.guardar_cambios(str(ruta), Cambios(descripcion=texto))
    metadatos.guardar_cambios(str(ruta), Cambios(fecha="16/04/2022", hora="10:05:30", gps=(40.8, -2.1)))
    assert imagen_de(ruta) == antes
    datos = metadatos.leer_metadatos(str(ruta))
    assert datos.descripcion == "tercera"
    assert (datos.fecha, datos.hora) == ("16/04/2022", "10:05:30")
    assert datos.gps == pytest.approx((40.8, -2.1), abs=1e-5)


def prueba_cambiar_solo_la_fecha_no_toca_la_descripcion(tmp_path):
    ruta = foto(tmp_path, xmp_inicial=XMP_SOLO_DESCRIPCION)
    metadatos.guardar_cambios(str(ruta), Cambios(fecha="01/01/2020", hora="12:00:00"))
    assert metadatos.leer_metadatos(str(ruta)).descripcion == "Un cielo al atardecer sobre el mar."


def prueba_png_se_rechaza_sin_tocar_el_archivo(tmp_path):
    ruta = tmp_path / "captura.png"
    Image.new("RGB", (8, 8), "white").save(ruta, "png")
    original = ruta.read_bytes()
    with pytest.raises(metadatos.FormatoNoSoportado):
        metadatos.guardar_cambios(str(ruta), Cambios(descripcion="x"))
    assert ruta.read_bytes() == original
    assert [p.name for p in tmp_path.iterdir()] == ["captura.png"]


def prueba_archivo_que_no_es_imagen_devuelve_vacio(tmp_path):
    ruta = tmp_path / "nota.jpg"
    ruta.write_text("no soy una foto")
    assert metadatos.leer_metadatos(str(ruta)) == metadatos.Metadatos()


def prueba_guardar_y_leer_el_lugar(tmp_path):
    from logica.lugares import Lugar
    ruta = foto(tmp_path, xmp_inicial=XMP_SOLO_DESCRIPCION)
    antes = imagen_de(ruta)
    lugar = Lugar("Faro de Cádiz", "Cádiz", "Cádiz", "España", "es")
    metadatos.guardar_cambios(str(ruta), Cambios(lugar=lugar))
    datos = metadatos.leer_metadatos(str(ruta))
    assert datos.lugar == lugar
    assert datos.descripcion == "Un cielo al atardecer sobre el mar."
    assert imagen_de(ruta) == antes
