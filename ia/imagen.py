"""Prepara una foto para enviarla a un servicio de IA."""
import io

from PIL import Image, ImageOps

# Registra el lector de HEIC si pillow-heif está instalado.
import logica.metadatos  # noqa: F401

# Los servicios reducen la imagen por su cuenta a un tamaño parecido; mandar la foto
# entera solo hace la petición más lenta y puede pasar del límite de tamaño.
LADO_MAXIMO = 1568


def preparar_jpeg(imagen, lado_maximo=LADO_MAXIMO, calidad=85):
    """Devuelve bytes JPEG: girada según el EXIF, en RGB y con el lado mayor limitado.

    Sirve para HEIC, PNG con transparencia, etc., que no todos los servicios aceptan.
    """
    imagen = ImageOps.exif_transpose(imagen)
    if imagen.mode != "RGB":
        fondo = Image.new("RGB", imagen.size, "white")
        if imagen.mode in ("RGBA", "LA") or (imagen.mode == "P" and "transparency" in imagen.info):
            imagen = imagen.convert("RGBA")
            fondo.paste(imagen, mask=imagen.split()[-1])
            imagen = fondo
        else:
            imagen = imagen.convert("RGB")
    imagen.thumbnail((lado_maximo, lado_maximo))
    salida = io.BytesIO()
    imagen.save(salida, "jpeg", quality=calidad)
    return salida.getvalue()


def leer_y_preparar(ruta):
    with Image.open(ruta) as imagen:
        return preparar_jpeg(imagen)
