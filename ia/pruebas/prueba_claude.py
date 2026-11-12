from types import SimpleNamespace

import anthropic
import pytest

from ia import claude, errores
from ia.errores import ErrorIA


def bloque(texto):
    return SimpleNamespace(type="text", text=texto)


class ClienteFalso:
    def __init__(self, respuesta=None, excepcion=None):
        self.peticiones = []
        cliente = self

        class Mensajes:
            def create(self, **kwargs):
                cliente.peticiones.append(kwargs)
                if excepcion:
                    raise excepcion
                return respuesta

        self.messages = Mensajes()


def error_de(clase):
    # Sin pasar por el constructor: en anthropic 0.x usa httpx y en 1.x httpx2, y aquí
    # solo importa la clase para comprobar a qué tipo de error se traduce.
    error = clase.__new__(clase)
    Exception.__init__(error, "error")
    return error


def prueba_describir_manda_imagen_y_devuelve_texto():
    respuesta = SimpleNamespace(stop_reason="end_turn", content=[bloque("Una playa "), bloque("al atardecer")])
    cliente = ClienteFalso(respuesta)
    assert claude.describir("k", "claude-haiku-5-5", "p", b"\xff\xd8", cliente=cliente) == "Una playa al atardecer"
    contenido = cliente.peticiones[0]["messages"][0]["content"]
    assert contenido[0]["source"]["media_type"] == "image/jpeg"
    assert cliente.peticiones[0]["model"] == "claude-haiku-5-5"


def prueba_rechazo_es_error():
    respuesta = SimpleNamespace(stop_reason="refusal", content=[])
    with pytest.raises(ErrorIA):
        claude.describir("k", "m", "p", b"x", cliente=ClienteFalso(respuesta))


@pytest.mark.parametrize("clase, tipo", [
    (anthropic.AuthenticationError, errores.CLAVE),
    (anthropic.NotFoundError, errores.MODELO),
    (anthropic.RateLimitError, errores.LIMITE),
    # APITimeoutError hereda de APIConnectionError: tiene que ganar el más concreto.
    (anthropic.APITimeoutError, errores.TIEMPO),
    (anthropic.APIConnectionError, errores.CONEXION),
])
def prueba_errores_se_clasifican(clase, tipo):
    with pytest.raises(ErrorIA) as e:
        claude.describir("k", "m", "p", b"x", cliente=ClienteFalso(excepcion=error_de(clase)))
    assert e.value.tipo == tipo
