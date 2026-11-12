import base64

import pytest

from ia import compatible_openai as co


def prueba_data_url_con_tipo_por_extension():
    url = co.imagen_a_data_url(b"\xff\xd8abc", "foto.JPG")
    assert url.startswith("data:image/jpeg;base64,")
    assert base64.b64decode(url.split(",", 1)[1]) == b"\xff\xd8abc"


def prueba_construir_peticion():
    peticion = co.construir_peticion("modelo-x", "Describe", "data:image/jpeg;base64,AAA")
    assert peticion["model"] == "modelo-x"
    contenido = peticion["messages"][0]["content"]
    assert contenido[0] == {"type": "text", "text": "Describe"}
    assert contenido[1]["image_url"]["url"] == "data:image/jpeg;base64,AAA"


def prueba_extraer_texto():
    respuesta = {"choices": [{"message": {"content": "Un perro en la playa"}}]}
    assert co.extraer_texto(respuesta) == "Un perro en la playa"


@pytest.mark.parametrize("respuesta", [{}, {"choices": []}, {"choices": [{"message": {"content": ""}}]}, None])
def prueba_respuesta_sin_texto_es_error(respuesta):
    # La versión 1.0 guardaba "No se encontró contenido..." como descripción de la foto.
    with pytest.raises(co.ErrorIA):
        co.extraer_texto(respuesta)
