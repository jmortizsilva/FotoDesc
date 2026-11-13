import piexif
from PIL import Image

from interfaz.buscador_lugares import BuscadorLugares
from logica import metadatos
from logica.lugares import Lugar
from ubicacion.cache import CacheLugares
from ubicacion.nominatim import ErrorUbicacion

RESPUESTA = {"category": "historic", "type": "castle", "name": "Castillo de Molina",
             "address": {"town": "Molina de Aragón", "province": "Guadalajara",
                         "country": "España", "country_code": "es"}}


class Cliente:
    def __init__(self, falla=False):
        self.falla, self.llamadas = falla, 0

    def buscar(self, latitud, longitud):
        self.llamadas += 1
        if self.falla:
            raise ErrorUbicacion("conexion", "sin red")
        return RESPUESTA


def foto_con_gps(tmp_path, nombre, gps=(40.8361, -1.8853)):
    ruta = tmp_path / nombre
    exif = metadatos.exif_vacio()
    Image.new("RGB", (16, 16)).save(ruta, "jpeg", exif=piexif.dump(exif))
    if gps:
        metadatos.guardar_cambios(str(ruta), metadatos.Cambios(gps=gps))
    return str(ruta)


def buscador(tmp_path, cliente):
    resultados = {}
    b = BuscadorLugares(CacheLugares(str(tmp_path / "cache.json")), cliente,
                        lambda ruta, lugar: resultados.__setitem__(ruta, lugar),
                        lambda funcion, *args: funcion(*args))
    return b, resultados


def prueba_busca_guarda_en_la_foto_y_avisa(tmp_path):
    rutas = [foto_con_gps(tmp_path, "a.jpg"), foto_con_gps(tmp_path, "b.jpg")]
    cliente = Cliente()
    b, resultados = buscador(tmp_path, cliente)
    b.anadir(rutas)
    b.esperar(5)
    assert cliente.llamadas == 1  # La segunda foto, en el mismo sitio, sale de la copia local
    for ruta in rutas:
        assert resultados[ruta].sitio == "Castillo de Molina"
        assert metadatos.leer_metadatos(ruta).lugar.localidad == "Molina de Aragón"
    assert not b.pendientes


def prueba_sin_conexion_deja_de_preguntar(tmp_path):
    rutas = [foto_con_gps(tmp_path, "a.jpg", (40.1, -3.1)), foto_con_gps(tmp_path, "b.jpg", (41.1, -4.1))]
    cliente = Cliente(falla=True)
    b, resultados = buscador(tmp_path, cliente)
    b.anadir(rutas)
    b.esperar(5)
    assert cliente.llamadas == 1
    assert resultados == {rutas[0]: None, rutas[1]: None}
    assert metadatos.leer_metadatos(rutas[0]).lugar is None


def prueba_foto_que_ya_tiene_lugar_no_se_consulta(tmp_path):
    ruta = foto_con_gps(tmp_path, "a.jpg")
    metadatos.guardar_cambios(ruta, metadatos.Cambios(lugar=Lugar(localidad="Soria")))
    cliente = Cliente()
    b, resultados = buscador(tmp_path, cliente)
    b.anadir([ruta])
    b.esperar(5)
    assert cliente.llamadas == 0
    assert resultados[ruta].localidad == "Soria"
