"""Busca en segundo plano el lugar de las fotos que tienen GPS y lo guarda en ellas."""
import logging
import queue
import threading

from logica import metadatos
from logica.metadatos import Cambios, FormatoNoSoportado
from ubicacion.cache import obtener_lugar
from ubicacion.nominatim import ErrorUbicacion


class BuscadorLugares:
    """Un hilo que va sacando rutas de una cola.

    `al_terminar(ruta, lugar_o_None)` se llama en el hilo de la interfaz (con
    wx.CallAfter, que se inyecta como `en_interfaz`) por cada foto que se intentó.
    """

    def __init__(self, cache, cliente, al_terminar, en_interfaz):
        self.cache = cache
        self.cliente = cliente
        self.al_terminar = al_terminar
        self.en_interfaz = en_interfaz
        self.cola = queue.Queue()
        self.pendientes = set()
        self._hilo = None
        self._sin_servicio = False

    def anadir(self, rutas):
        for ruta in rutas:
            if ruta not in self.pendientes:
                self.pendientes.add(ruta)
                self.cola.put(ruta)
        if self._hilo is None or not self._hilo.is_alive():
            self._hilo = threading.Thread(target=self._trabajar, daemon=True)
            self._hilo.start()

    def vaciar(self):
        """Olvida lo pendiente (al reemplazar la lista de fotos)."""
        self.pendientes.clear()
        try:
            while True:
                self.cola.get_nowait()
        except queue.Empty:
            pass

    def esperar(self, segundos=None):
        """Para las pruebas: espera a que acabe lo encolado."""
        if self._hilo:
            self._hilo.join(segundos)

    def _trabajar(self):
        while True:
            try:
                ruta = self.cola.get_nowait()
            except queue.Empty:
                return
            if ruta not in self.pendientes:
                continue  # Se vació la lista mientras tanto
            lugar = self._procesar(ruta)
            self.pendientes.discard(ruta)
            self.en_interfaz(self.al_terminar, ruta, lugar)

    def _procesar(self, ruta):
        datos = metadatos.leer_metadatos(ruta)
        if not datos.gps:
            return None
        if datos.lugar:
            return datos.lugar
        latitud, longitud = datos.gps
        lugar = self.cache.buscar(latitud, longitud)
        if lugar is None:
            if self._sin_servicio:
                return None
            try:
                lugar = obtener_lugar(latitud, longitud, self.cache, self.cliente)
            except ErrorUbicacion as e:
                # Sin conexión o con el límite superado no tiene sentido seguir
                # preguntando por cada foto en esta sesión.
                logging.warning("Nominatim no disponible (%s): %s", e.motivo, e)
                self._sin_servicio = True
                return None
        if lugar.vacio():
            return None
        try:
            metadatos.guardar_cambios(ruta, Cambios(lugar=lugar))
        except FormatoNoSoportado:
            pass  # Se muestra igualmente; en HEIC aún no se puede guardar
        except OSError:
            logging.exception("No se pudo guardar el lugar en %s", ruta)
        return lugar
