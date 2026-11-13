"""Lugares ya consultados, guardados en el ordenador para no repetir consultas.

No sustituye a lo que se guarda en la foto: solo evita preguntar dos veces por el
mismo sitio (dos fotos a menos de unos 100 metros comparten resultado).
"""
import json
import os
import tempfile
import threading

from logica import lugares
from logica.lugares import Lugar


class CacheLugares:
    def __init__(self, ruta):
        self.ruta = ruta
        self._datos = {}
        self._cerrojo = threading.Lock()
        try:
            with open(ruta, encoding="utf-8") as f:
                self._datos = json.load(f)
        except (OSError, ValueError):
            self._datos = {}

    def buscar(self, latitud, longitud):
        """Lugar guardado para esas coordenadas, o None si no se ha consultado nunca."""
        datos = self._datos.get(lugares.clave(latitud, longitud))
        return Lugar.desde_dict(datos) if datos is not None else None

    def guardar(self, latitud, longitud, lugar):
        with self._cerrojo:
            self._datos[lugares.clave(latitud, longitud)] = lugar.a_dict()
            carpeta = os.path.dirname(os.path.abspath(self.ruta))
            os.makedirs(carpeta, exist_ok=True)
            descriptor, temporal = tempfile.mkstemp(dir=carpeta, suffix=".tmp")
            with os.fdopen(descriptor, "w", encoding="utf-8") as f:
                json.dump(self._datos, f, ensure_ascii=False)
            os.replace(temporal, self.ruta)


def obtener_lugar(latitud, longitud, cache, cliente):
    """Lugar de las coordenadas: de la copia local o, si no está, de Nominatim.

    Lanza ErrorUbicacion si hay que preguntar y falla. Un "no hay nada aquí" (en
    medio del mar, por ejemplo) también se guarda, para no volver a preguntar.
    """
    lugar = cache.buscar(latitud, longitud)
    if lugar is None:
        lugar = lugares.desde_nominatim(cliente.buscar(latitud, longitud))
        cache.guardar(latitud, longitud, lugar)
    return lugar
