"""Conversión entre grados decimales y el formato EXIF de grados, minutos y segundos."""


def decimal_a_dms(decimal):
    """Devuelve ((grados, 1), (minutos, 1), (segundos*100, 100)) del valor absoluto.

    El signo no se guarda aquí: en EXIF va aparte, en la referencia N/S o E/W.
    """
    decimal = abs(decimal)
    grados = int(decimal)
    minutos = int((decimal - grados) * 60)
    segundos = (decimal - grados - minutos / 60) * 3600
    return ((grados, 1), (minutos, 1), (int(segundos * 100), 100))


def dms_a_decimal(dms, referencia):
    """Convierte la tupla EXIF a grados decimales; negativo si la referencia es S o W.

    Devuelve None si la tupla está mal formada (denominador cero, faltan partes...).
    """
    try:
        grados = dms[0][0] / dms[0][1]
        minutos = dms[1][0] / dms[1][1]
        segundos = dms[2][0] / dms[2][1]
    except (IndexError, TypeError, ZeroDivisionError):
        return None
    decimal = grados + minutos / 60 + segundos / 3600
    if referencia in ("S", "W"):
        decimal = -decimal
    return decimal


def referencias(latitud, longitud):
    """Devuelve las letras de referencia EXIF ('N'/'S', 'E'/'W') según el signo."""
    return ("N" if latitud >= 0 else "S", "E" if longitud >= 0 else "W")
