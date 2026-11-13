import io

import piexif
import pytest
from PIL import Image

from logica import jpeg


def jpeg_de_prueba(con_exif=False):
    salida = io.BytesIO()
    imagen = Image.new("RGB", (16, 16), "blue")
    if con_exif:
        exif = piexif.dump({"0th": {piexif.ImageIFD.Make: b"Prueba"}, "Exif": {}, "GPS": {},
                            "Interop": {}, "1st": {}, "thumbnail": None})
        imagen.save(salida, "jpeg", exif=exif)
    else:
        imagen.save(salida, "jpeg")
    return salida.getvalue()


def imagen_de(datos):
    return datos[datos.index(b"\xff\xda"):]


@pytest.mark.parametrize("con_exif", [False, True])
def prueba_anade_y_sustituye_el_xmp_sin_tocar_la_imagen(con_exif):
    original = jpeg_de_prueba(con_exif)
    assert jpeg.leer_xmp(original) is None

    con_xmp = jpeg.poner_xmp(original, "<x:xmpmeta xmlns:x='adobe:ns:meta/'>uno</x:xmpmeta>")
    assert b"uno" in jpeg.leer_xmp(con_xmp)
    otra = jpeg.poner_xmp(con_xmp, "<x:xmpmeta xmlns:x='adobe:ns:meta/'>dos</x:xmpmeta>")
    assert b"dos" in jpeg.leer_xmp(otra) and b"uno" not in otra

    assert imagen_de(otra) == imagen_de(original)
    Image.open(io.BytesIO(otra)).load()
    if con_exif:
        assert piexif.load(otra)["0th"][piexif.ImageIFD.Make] == b"Prueba"


def prueba_xmp_va_detras_del_exif():
    datos = jpeg.poner_xmp(jpeg_de_prueba(con_exif=True), "<x/>")
    posicion_exif = datos.index(b"Exif\x00\x00")
    posicion_xmp = datos.index(jpeg.CABECERA_XMP)
    assert posicion_exif < posicion_xmp


def prueba_xmp_demasiado_grande():
    with pytest.raises(jpeg.XmpDemasiadoGrande):
        jpeg.poner_xmp(jpeg_de_prueba(), "x" * 70000)
