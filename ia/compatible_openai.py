"""Servicios con la API de chat de OpenAI: OpenAI, Gemini, Groq, OpenRouter, Ollama..."""
import base64

import requests

from ia import errores
from ia.errores import ErrorIA


def data_url_jpeg(datos):
    return "data:image/jpeg;base64," + base64.b64encode(datos).decode("ascii")


def construir_peticion(modelo, prompt, datos_jpeg):
    # Sin max_tokens: los modelos con razonamiento (gpt-5, gpt-6...) lo rechazan o
    # gastan el límite pensando y devuelven texto vacío. La longitud la marca el prompt.
    return {
        "model": modelo,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url_jpeg(datos_jpeg)}},
                ],
            }
        ],
    }


def extraer_texto(respuesta):
    """Texto de la primera respuesta; ErrorIA si no viene ninguno."""
    try:
        texto = respuesta["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        texto = None
    if not texto or not texto.strip():
        raise ErrorIA(errores.OTRO, "la respuesta llegó vacía.")
    return texto.strip()


def describir(url_base, clave, modelo, prompt, datos_jpeg, timeout=60, sesion=requests):
    cabeceras = {"Content-Type": "application/json"}
    if clave:
        cabeceras["Authorization"] = "Bearer " + clave
    try:
        respuesta = sesion.post(url_base.rstrip("/") + "/chat/completions",
                                json=construir_peticion(modelo, prompt, datos_jpeg),
                                headers=cabeceras, timeout=timeout)
    except requests.Timeout:
        raise ErrorIA(errores.TIEMPO)
    except requests.ConnectionError as e:
        raise ErrorIA(errores.CONEXION, str(e))

    if respuesta.status_code != 200:
        cuerpo = respuesta.text
        raise ErrorIA(errores.tipo_por_estado_http(respuesta.status_code, cuerpo),
                      f"código {respuesta.status_code}. {cuerpo[:300]}")
    try:
        return extraer_texto(respuesta.json())
    except ValueError:
        raise ErrorIA(errores.OTRO, "la respuesta no se pudo leer.")
