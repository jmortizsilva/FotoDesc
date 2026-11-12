"""Lectura y modificación de los metadatos EXIF de una foto.

Las funciones que trabajan sobre el diccionario EXIF son puras; solo `leer_exif`,
`guardar_exif` y `leer_metadatos` tocan el disco.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

import piexif
from PIL import Image

from logica.coordenadas import decimal_a_dms, dms_a_decimal, referencias

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


def extraer_metadatos(exif):
    """Saca descripción, GPS, fecha y hora de un diccionario EXIF de piexif."""
    descripcion = exif.get("0th", {}).get(piexif.ImageIFD.ImageDescription, b"")
    descripcion = descripcion.decode("utf-8", errors="ignore")

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

    return Metadatos(descripcion, gps, fecha, hora)


def poner_descripcion(exif, descripcion):
    exif["0th"][piexif.ImageIFD.ImageDescription] = descripcion.encode("utf-8")


def poner_fecha(exif, fecha, hora):
    """Escribe la fecha original si las dos partes son válidas; si no, no toca nada."""
    valor = texto_a_fecha_exif(fecha, hora)
    if valor:
        exif["Exif"][piexif.ExifIFD.DateTimeOriginal] = valor.encode("utf-8")


def leer_coordenada(texto):
    """Convierte '40,4168' o '40.4168' a float; None si no es un número."""
    try:
        return float(texto.strip().replace(",", "."))
    except ValueError:
        return None


def poner_gps(exif, latitud, longitud):
    ref_lat, ref_lon = referencias(latitud, longitud)
    exif["GPS"][piexif.GPSIFD.GPSLatitudeRef] = ref_lat.encode("utf-8")
    exif["GPS"][piexif.GPSIFD.GPSLatitude] = decimal_a_dms(latitud)
    exif["GPS"][piexif.GPSIFD.GPSLongitudeRef] = ref_lon.encode("utf-8")
    exif["GPS"][piexif.GPSIFD.GPSLongitude] = decimal_a_dms(longitud)


# ---------------- Acceso al disco ----------------

def leer_exif(ruta):
    img = Image.open(ruta)
    if "exif" in img.info:
        return piexif.load(img.info["exif"])
    return exif_vacio()


def guardar_exif(ruta, exif):
    img = Image.open(ruta)
    img.save(ruta, "jpeg", exif=piexif.dump(exif))


def leer_metadatos(ruta):
    """Metadatos de la foto; si no se puede leer, devuelve uno vacío."""
    try:
        return extraer_metadatos(leer_exif(ruta))
    except Exception:
        return Metadatos()
