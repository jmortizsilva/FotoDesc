"""Consulta de lugares a Nominatim (OpenStreetMap).

Política de uso: https://operations.osmfoundation.org/policies/nominatim/
- Como máximo una petición por segundo, contando toda la aplicación.
- Identificarse con un User-Agent propio.
- Guardar los resultados para no repetir consultas (ver ubicacion/cache.py).
Vale para un uso personal; si FotoDesc lo usara mucha gente habría que cambiar de
servicio o montar uno propio.
"""
import threading
import time

import requests

URL = "https://nominatim.openstreetmap.org/reverse"
AGENTE = "FotoDesc/2 (https://github.com/jmortizsilva/FotoDesc)"
INTERVALO = 1.1  # Algo más de un segundo, por margen


class ErrorUbicacion(Exception):
    def __init__(self, motivo, detalle=""):
        super().__init__(detalle or motivo)
        self.motivo = motivo  # "conexion", "limite" u "otro"


class Nominatim:
    def __init__(self, sesion=requests, ahora=time.monotonic, esperar=time.sleep):
        self.sesion = sesion
        self.ahora = ahora
        self.esperar = esperar
        self._ultima = None
        self._cerrojo = threading.Lock()

    def buscar(self, latitud, longitud):
        """Respuesta JSON de /reverse para esas coordenadas, en español."""
        with self._cerrojo:
            if self._ultima is not None:
                falta = self._ultima + INTERVALO - self.ahora()
                if falta > 0:
                    self.esperar(falta)
            parametros = {"format": "jsonv2", "lat": f"{latitud:.6f}", "lon": f"{longitud:.6f}",
                          "zoom": 18, "addressdetails": 1, "accept-language": "es"}
            try:
                respuesta = self.sesion.get(URL, params=parametros, headers={"User-Agent": AGENTE},
                                            timeout=15)
            except requests.RequestException as e:
                raise ErrorUbicacion("conexion", str(e))
            finally:
                self._ultima = self.ahora()
        if respuesta.status_code in (429, 403):
            raise ErrorUbicacion("limite", f"código {respuesta.status_code}")
        if respuesta.status_code != 200:
            raise ErrorUbicacion("otro", f"código {respuesta.status_code}")
        try:
            return respuesta.json()
        except ValueError:
            raise ErrorUbicacion("otro", "respuesta ilegible")
