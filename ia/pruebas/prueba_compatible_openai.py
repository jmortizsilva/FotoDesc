import base64

import pytest
import requests

from ia import compatible_openai as co
from ia import errores
from ia.errores import ErrorIA


class RespuestaFalsa:
    def __init__(self, estado, json_=None, texto=""):
        self.status_code = estado
        self._json = json_
        self.text = texto

    def json(self):
        if self._json is None:
            raise ValueError("no es JSON")
        return self._json


class SesionFalsa:
    def __init__(self, respuesta=None, excepcion=None):
        self.respuesta = respuesta
        self.excepcion = excepcion
        self.llamadas = []

    def post(self, url, json, headers, timeout):
        self.llamadas.append((url, json, headers))
        if self.excepcion:
            raise self.excepcion
        return self.respuesta


def respuesta_con(texto):
    return RespuestaFalsa(200, {"choices": [{"message": {"content": texto}}]})


def prueba_peticion_lleva_la_imagen_en_jpeg_y_sin_max_tokens():
    peticion = co.construir_peticion("modelo-x", "Describe", b"\xff\xd8abc")
    assert peticion["model"] == "modelo-x"
    assert "max_tokens" not in peticion
    contenido = peticion["messages"][0]["content"]
    assert contenido[0] == {"type": "text", "text": "Describe"}
    url = contenido[1]["image_url"]["url"]
    assert url.startswith("data:image/jpeg;base64,")
    assert base64.b64decode(url.split(",", 1)[1]) == b"\xff\xd8abc"


def prueba_describir_usa_la_url_y_la_clave():
    sesion = SesionFalsa(respuesta_con("  Un perro en la playa \n"))
    texto = co.describir("https://ejemplo/v1/", "k", "m", "p", b"x", sesion=sesion)
    assert texto == "Un perro en la playa"
    url, _, cabeceras = sesion.llamadas[0]
    assert url == "https://ejemplo/v1/chat/completions"
    assert cabeceras["Authorization"] == "Bearer k"


def prueba_sin_clave_no_manda_cabecera_de_autorizacion():
    sesion = SesionFalsa(respuesta_con("ok"))
    co.describir("http://localhost:11434/v1", "", "m", "p", b"x", sesion=sesion)
    assert "Authorization" not in sesion.llamadas[0][2]


@pytest.mark.parametrize("estado, cuerpo, tipo", [
    (401, "", errores.CLAVE),
    (400, '{"error": "API key not valid"}', errores.CLAVE),
    (404, "", errores.MODELO),
    (429, "", errores.LIMITE),
    (500, "fallo", errores.OTRO),
])
def prueba_errores_http_se_clasifican(estado, cuerpo, tipo):
    sesion = SesionFalsa(RespuestaFalsa(estado, texto=cuerpo))
    with pytest.raises(ErrorIA) as e:
        co.describir("u", "k", "m", "p", b"x", sesion=sesion)
    assert e.value.tipo == tipo


@pytest.mark.parametrize("excepcion, tipo", [
    (requests.Timeout(), errores.TIEMPO),
    (requests.ConnectionError("rechazada"), errores.CONEXION),
])
def prueba_errores_de_red_se_clasifican(excepcion, tipo):
    with pytest.raises(ErrorIA) as e:
        co.describir("u", "k", "m", "p", b"x", sesion=SesionFalsa(excepcion=excepcion))
    assert e.value.tipo == tipo


@pytest.mark.parametrize("respuesta", [{}, {"choices": []}, {"choices": [{"message": {"content": "  "}}]}, None])
def prueba_respuesta_sin_texto_es_error(respuesta):
    # La versión 1.0 guardaba "No se encontró contenido..." como descripción de la foto.
    with pytest.raises(ErrorIA):
        co.extraer_texto(respuesta)
