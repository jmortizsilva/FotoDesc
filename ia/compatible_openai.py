"""Petición de descripción a un servicio con la API de chat de OpenAI."""
import base64
import json
import mimetypes
import urllib.error
import urllib.request

URL_OPENAI = "https://api.openai.com/v1/chat/completions"
MODELO_POR_DEFECTO = "gpt-4o-mini"
PROMPT_POR_DEFECTO = "Describe la imagen de manera detallada."


class ErrorIA(Exception):
    pass


def imagen_a_data_url(contenido, ruta):
    """Codifica los bytes de la imagen como data URL; el tipo se deduce de la extensión."""
    tipo = mimetypes.guess_type(ruta)[0] or "application/octet-stream"
    codificado = base64.b64encode(contenido).decode("utf-8")
    return f"data:{tipo};base64,{codificado}"


def construir_peticion(modelo, prompt, data_url, detalle="high", max_tokens=300):
    return {
        "model": modelo,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url, "detail": detalle}},
                ],
            }
        ],
        "max_tokens": max_tokens,
    }


def extraer_texto(respuesta):
    """Texto de la primera respuesta; ErrorIA si no viene ninguno."""
    try:
        texto = respuesta["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        texto = None
    if not texto:
        raise ErrorIA("No se encontró contenido en la respuesta.")
    return texto


def describir_imagen(clave, ruta, prompt=PROMPT_POR_DEFECTO, modelo=MODELO_POR_DEFECTO,
                     url=URL_OPENAI):
    with open(ruta, "rb") as f:
        data_url = imagen_a_data_url(f.read(), ruta)
    datos = json.dumps(construir_peticion(modelo, prompt, data_url)).encode("utf-8")

    peticion = urllib.request.Request(url, data=datos)
    peticion.add_header("Content-Type", "application/json")
    peticion.add_header("Authorization", "Bearer " + clave)
    try:
        with urllib.request.urlopen(peticion) as respuesta:
            return extraer_texto(json.loads(respuesta.read().decode("utf-8")))
    except urllib.error.HTTPError as e:
        raise ErrorIA("Error en la petición: {} - {}".format(e.code, e.read().decode("utf-8")))
    except ErrorIA:
        raise
    except Exception as e:
        raise ErrorIA("Se produjo un error: " + str(e))
