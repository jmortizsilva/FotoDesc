"""Columnas de la lista de fotos: qué se muestra y qué se anuncia al recorrerlas."""
from logica import lugares

COLUMNAS = ["Nombre", "Descripción", "Fecha", "Hora", "Ubicación"]

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_legible(fecha):
    """'16/04/2022' -> '16 de abril de 2022'. Si no encaja, la devuelve tal cual."""
    partes = fecha.split("/")
    if len(partes) != 3:
        return fecha
    try:
        dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
    except ValueError:
        return fecha
    if not 1 <= mes <= 12 or not 1 <= dia <= 31:
        return fecha
    return f"{dia} de {MESES[mes - 1]} de {anio}"


def ubicacion_legible(gps):
    """(40.812345, -2.103456) -> '40,8123; -2,1035'. Sin coordenadas, cadena vacía."""
    if not gps:
        return ""
    return "; ".join(f"{valor:.4f}".replace(".", ",") for valor in gps)


def texto_ubicacion(datos, buscando=False):
    """El lugar guardado en la foto; si no lo hay, 'buscando' o las coordenadas."""
    if datos.lugar and not datos.lugar.vacio():
        return lugares.texto(datos.lugar)
    if datos.gps and buscando:
        return "buscando"
    return ubicacion_legible(datos.gps)


def valores_fila(nombre, datos, buscando=False):
    """Textos de las columnas, en el orden de COLUMNAS. `datos` es un Metadatos."""
    # La lista solo muestra una línea por celda: los saltos de línea se leerían pegados.
    descripcion = " ".join(datos.descripcion.split())
    return [nombre, descripcion, fecha_legible(datos.fecha), datos.hora,
            texto_ubicacion(datos, buscando)]


def anuncio(columna, valor):
    """Lo que se dice al llegar a una celda: 'Fecha, 16 de abril de 2022'."""
    return f"{COLUMNAS[columna]}, {valor.strip() or 'sin datos'}"


def mover(actual, paso, total=len(COLUMNAS)):
    """Devuelve (columna nueva, si se ha intentado salir por un extremo)."""
    nueva = actual + paso
    if nueva < 0 or nueva >= total:
        return actual, True
    return nueva, False
