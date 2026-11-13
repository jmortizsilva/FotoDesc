"""Bloques de metadatos de un JPEG, sin tocar los datos de la imagen."""

CABECERA_XMP = b"http://ns.adobe.com/xap/1.0/\x00"
MAXIMO_SEGMENTO = 65533  # El campo de longitud es de 16 bits e incluye sus 2 bytes


class XmpDemasiadoGrande(Exception):
    pass


def es_jpeg(datos):
    return datos[:2] == b"\xff\xd8"


def segmentos(datos):
    """Recorre los segmentos de cabecera: (marca, inicio, fin). Se detiene en la imagen (SOS)."""
    i = 2
    while i + 4 <= len(datos) and datos[i] == 0xFF:
        marca = datos[i + 1]
        if marca == 0xDA:  # A partir de aquí, la imagen comprimida
            return
        largo = int.from_bytes(datos[i + 2:i + 4], "big")
        yield marca, i, i + 2 + largo
        i += 2 + largo


def leer_xmp(datos):
    """Paquete XMP (bytes) del JPEG, o None."""
    for marca, inicio, fin in segmentos(datos):
        cuerpo = datos[inicio + 4:fin]
        if marca == 0xE1 and cuerpo.startswith(CABECERA_XMP):
            return cuerpo[len(CABECERA_XMP):]
    return None


def poner_xmp(datos, paquete):
    """Devuelve el JPEG con el XMP sustituido o, si no tenía, añadido tras APP0/EXIF."""
    if isinstance(paquete, str):
        paquete = paquete.encode("utf-8")
    cuerpo = CABECERA_XMP + paquete
    if len(cuerpo) + 2 > MAXIMO_SEGMENTO:
        raise XmpDemasiadoGrande("La descripción es demasiado larga para guardarla en la foto.")
    segmento = b"\xff\xe1" + (len(cuerpo) + 2).to_bytes(2, "big") + cuerpo

    punto_insercion = 2
    for marca, inicio, fin in segmentos(datos):
        if marca == 0xE1 and datos[inicio + 4:fin].startswith(CABECERA_XMP):
            return datos[:inicio] + segmento + datos[fin:]
        if marca in (0xE0, 0xE1):  # JFIF y EXIF van primero; el XMP detrás
            punto_insercion = fin
        else:
            break
    return datos[:punto_insercion] + segmento + datos[punto_insercion:]
