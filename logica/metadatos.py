"""Lectura y modificación de los metadatos de una foto.

- La descripción accesible va en XMP (ver logica/xmp.py).
- Fecha y GPS van en EXIF.
- EXIF ImageDescription es donde escribía la versión 1.0: se lee para no perder esas
  descripciones, pero no se escribe, porque Fotos de Apple lo convierte también en
  pie de foto. Al guardar una descripción nueva se quita.

`aplicar_cambios` trabaja sobre bytes y no toca el disco; `guardar_cambios` y
`leer_metadatos` son la parte que lee y escribe archivos.
"""
import io
import os
import tempfile
from dataclasses import dataclass
from typing import Optional, Tuple

import piexif
from PIL import Image

from logica import jpeg, xmp
from logica.lugares import Lugar
from logica.coordenadas import decimal_a_dms, dms_a_decimal, referencias
from logica.jpeg import es_jpeg  # noqa: F401  (lo usa la interfaz)

# Registrar el lector de HEIF/HEIC si pillow-heif está instalado.
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    pass


@dataclass
class Metadatos:
    descripcion: str = ""
    gps: Optional[Tuple[float, float]] = None
    fecha: str = ""  # DD/MM/AAAA
    hora: str = ""   # HH:MM:SS
    lugar: Optional[Lugar] = None  # Lo guardado en la foto; None si no tiene


@dataclass
class Cambios:
    """Lo que se quiere cambiar; None en un campo significa no tocarlo."""
    descripcion: Optional[str] = None
    fecha: Optional[str] = None
    hora: Optional[str] = None
    gps: Optional[Tuple[float, float]] = None
    lugar: Optional[Lugar] = None


class FormatoNoSoportado(Exception):
    """Solo se escriben metadatos en JPEG; en otros formatos se rechaza antes de tocar el archivo."""

    def __init__(self):
        super().__init__("Por ahora solo se pueden guardar datos en fotos JPG.")


def exif_vacio():
    return {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}


# ---------------- Funciones puras ----------------

def fecha_exif_a_texto(valor):
    """'AAAA:MM:DD HH:MM:SS' -> ('DD/MM/AAAA', 'HH:MM:SS'). Si no encaja, ('', '')."""
    partes = valor.split(" ")
    if len(partes) != 2:
        return "", ""
    trozos_fecha = partes[0].split(":")
    if len(trozos_fecha) != 3:
        return "", ""
    anio, mes, dia = trozos_fecha
    return f"{dia}/{mes}/{anio}", partes[1]


def texto_a_fecha_exif(fecha, hora):
    """('DD/MM/AAAA', 'HH:MM:SS') -> 'AAAA:MM:DD HH:MM:SS', o None si falta algo."""
    if not fecha or not hora:
        return None
    partes = fecha.split("/")
    if len(partes) != 3:
        return None
    dia, mes, anio = partes
    return f"{anio}:{mes}:{dia} {hora}"


def leer_coordenada(texto):
    """Convierte '40,4168' o '40.4168' a float; None si no es un número."""
    try:
        return float(texto.strip().replace(",", "."))
    except ValueError:
        return None


def extraer_metadatos(exif, paquete_xmp=None):
    """Saca descripción, GPS, fecha y hora del EXIF (dict de piexif) y del XMP."""
    descripcion = xmp.leer_descripcion(paquete_xmp)
    if not descripcion:
        antigua = exif.get("0th", {}).get(piexif.ImageIFD.ImageDescription, b"")
        descripcion = antigua.decode("utf-8", errors="ignore").strip()

    gps = None
    datos_gps = exif.get("GPS", {})
    latitud_dms = datos_gps.get(piexif.GPSIFD.GPSLatitude)
    longitud_dms = datos_gps.get(piexif.GPSIFD.GPSLongitude)
    if latitud_dms and longitud_dms:
        ref_lat = datos_gps.get(piexif.GPSIFD.GPSLatitudeRef, b"N").decode("utf-8")
        ref_lon = datos_gps.get(piexif.GPSIFD.GPSLongitudeRef, b"E").decode("utf-8")
        latitud = dms_a_decimal(latitud_dms, ref_lat)
        longitud = dms_a_decimal(longitud_dms, ref_lon)
        if latitud is not None and longitud is not None:
            gps = (latitud, longitud)

    fecha, hora = "", ""
    original = exif.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
    if original:
        fecha, hora = fecha_exif_a_texto(original.decode("utf-8", errors="ignore"))

    campos_lugar = xmp.leer_lugar(paquete_xmp)
    lugar = Lugar.desde_dict(campos_lugar) if campos_lugar else None
    return Metadatos(descripcion, gps, fecha, hora, lugar)


def _cambiar_exif(exif, cambios):
    """Aplica fecha, GPS y la retirada del campo antiguo. Devuelve si cambió algo."""
    cambiado = False
    if cambios.descripcion is not None and piexif.ImageIFD.ImageDescription in exif["0th"]:
        del exif["0th"][piexif.ImageIFD.ImageDescription]
        cambiado = True
    valor = texto_a_fecha_exif(cambios.fecha or "", cambios.hora or "")
    if valor:
        exif["Exif"][piexif.ExifIFD.DateTimeOriginal] = valor.encode("utf-8")
        cambiado = True
    if cambios.gps:
        latitud, longitud = cambios.gps
        ref_lat, ref_lon = referencias(latitud, longitud)
        exif["GPS"][piexif.GPSIFD.GPSLatitudeRef] = ref_lat.encode("utf-8")
        exif["GPS"][piexif.GPSIFD.GPSLatitude] = decimal_a_dms(latitud)
        exif["GPS"][piexif.GPSIFD.GPSLongitudeRef] = ref_lon.encode("utf-8")
        exif["GPS"][piexif.GPSIFD.GPSLongitude] = decimal_a_dms(longitud)
        cambiado = True
    return cambiado


def aplicar_cambios(datos, cambios):
    """Devuelve los bytes del JPEG con los cambios, sin tocar la imagen.

    La versión 1.0 guardaba con Image.save(), que recomprimía la foto con calidad 75
    y quitaba el perfil de color en cada guardado.
    """
    if not jpeg.es_jpeg(datos):
        raise FormatoNoSoportado()

    exif = piexif.load(datos)
    for grupo, valor in exif_vacio().items():
        exif.setdefault(grupo, valor)
    if _cambiar_exif(exif, cambios):
        # El EXIF solo se reescribe si cambia: piexif.dump falla con algunos EXIF
        # raros de cámara, y así una descripción se puede guardar igualmente.
        flujo = io.BytesIO()
        piexif.insert(piexif.dump(exif), datos, flujo)
        datos = flujo.getvalue()

    if cambios.descripcion is not None or cambios.lugar is not None:
        paquete = jpeg.leer_xmp(datos)
        if cambios.descripcion is not None:
            paquete = xmp.poner_descripcion(paquete, cambios.descripcion)
        if cambios.lugar is not None:
            paquete = xmp.poner_lugar(paquete, cambios.lugar.a_dict())
        datos = jpeg.poner_xmp(datos, paquete)
    return datos


# ---------------- Acceso al disco ----------------

def escribir_de_una_vez(ruta, datos):
    # Se escribe en un temporal y se sustituye de una vez: si algo falla a medias
    # (disco lleno, iCloud sincronizando), la foto original queda intacta.
    carpeta = os.path.dirname(os.path.abspath(ruta))
    descriptor, temporal = tempfile.mkstemp(dir=carpeta, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "wb") as f:
            f.write(datos)
        os.replace(temporal, ruta)
    except BaseException:
        if os.path.exists(temporal):
            os.remove(temporal)
        raise


def guardar_cambios(ruta, cambios):
    with open(ruta, "rb") as f:
        datos = aplicar_cambios(f.read(), cambios)
    escribir_de_una_vez(ruta, datos)


def leer_metadatos(ruta):
    """Metadatos de la foto; si no se puede leer, devuelve uno vacío."""
    try:
        with Image.open(ruta) as img:
            exif = piexif.load(img.info["exif"]) if "exif" in img.info else exif_vacio()
            paquete = img.info.get("xmp")
        return extraer_metadatos(exif, paquete)
    except Exception:
        return Metadatos()
