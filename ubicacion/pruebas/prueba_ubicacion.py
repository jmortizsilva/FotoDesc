import pytest
import requests

from logica.lugares import Lugar
from ubicacion import nominatim
from ubicacion.cache import CacheLugares, obtener_lugar
from ubicacion.nominatim import ErrorUbicacion, Nominatim

RESPUESTA = {"category": "historic", "type": "castle", "name": "Castillo de Molina",
             "address": {"town": "Molina de Aragón", "province": "Guadalajara",
                         "country": "España", "country_code": "es"}}


class Respuesta:
    def __init__(self, estado=200, json_=None):
        self.status_code, self._json = estado, json_

    def json(self):
        return self._json


class Sesion:
    def __init__(self, respuesta=None, excepcion=None):
        self.respuesta, self.excepcion, self.peticiones = respuesta, excepcion, []

    def get(self, url, params, headers, timeout):
        self.peticiones.append((params, headers))
        if self.excepcion:
            raise self.excepcion
        return self.respuesta


class Reloj:
    def __init__(self):
        self.t, self.esperas = 100.0, []

    def ahora(self):
        return self.t

    def esperar(self, segundos):
        self.esperas.append(round(segundos, 2))
        self.t += segundos


def prueba_respeta_un_segundo_entre_peticiones():
    reloj = Reloj()
    cliente = Nominatim(Sesion(Respuesta(json_=RESPUESTA)), reloj.ahora, reloj.esperar)
    cliente.buscar(40.8, -1.8)
    reloj.t += 0.3
    cliente.buscar(40.8, -1.8)
    assert reloj.esperas == [round(nominatim.INTERVALO - 0.3, 2)]


def prueba_se_identifica_y_pide_espanol():
    sesion = Sesion(Respuesta(json_=RESPUESTA))
    Nominatim(sesion).buscar(40.8, -1.8)
    params, cabeceras = sesion.peticiones[0]
    assert cabeceras["User-Agent"].startswith("FotoDesc")
    assert params["accept-language"] == "es" and params["format"] == "jsonv2"


@pytest.mark.parametrize("sesion, motivo", [
    (Sesion(Respuesta(429)), "limite"),
    (Sesion(Respuesta(500)), "otro"),
    (Sesion(excepcion=requests.ConnectionError("sin red")), "conexion"),
])
def prueba_errores(sesion, motivo):
    with pytest.raises(ErrorUbicacion) as e:
        Nominatim(sesion).buscar(1, 1)
    assert e.value.motivo == motivo


def prueba_la_copia_local_evita_repetir_y_sobrevive(tmp_path):
    ruta = tmp_path / "datos" / "lugares.json"
    sesion = Sesion(Respuesta(json_=RESPUESTA))
    cliente = Nominatim(sesion, esperar=lambda s: None)
    cache = CacheLugares(str(ruta))
    lugar = obtener_lugar(40.8361, -1.8853, cache, cliente)
    assert lugar.sitio == "Castillo de Molina"
    # Otra foto a pocos metros: no se pregunta otra vez
    obtener_lugar(40.8364, -1.8851, cache, cliente)
    assert len(sesion.peticiones) == 1
    # Y al abrir la app de nuevo sigue ahí
    assert CacheLugares(str(ruta)).buscar(40.8361, -1.8853) == lugar


def prueba_copia_local_rota_empieza_de_cero(tmp_path):
    ruta = tmp_path / "lugares.json"
    ruta.write_text("{esto no es json")
    assert CacheLugares(str(ruta)).buscar(1, 1) is None


def prueba_sin_resultado_tambien_se_recuerda(tmp_path):
    sesion = Sesion(Respuesta(json_={"error": "Unable to geocode"}))
    cache = CacheLugares(str(tmp_path / "l.json"))
    assert obtener_lugar(0, 0, cache, Nominatim(sesion, esperar=lambda s: None)) == Lugar()
    obtener_lugar(0, 0, cache, Nominatim(sesion, esperar=lambda s: None))
    assert len(sesion.peticiones) == 1
