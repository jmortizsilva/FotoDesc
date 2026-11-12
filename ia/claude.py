"""Claude, con la librería oficial de Anthropic."""
import base64

import anthropic

from ia import errores
from ia.errores import ErrorIA


def construir_mensajes(prompt, datos_jpeg):
    return [{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                         "data": base64.standard_b64encode(datos_jpeg).decode("ascii")}},
            {"type": "text", "text": prompt},
        ],
    }]


def extraer_texto(respuesta):
    if respuesta.stop_reason == "refusal":
        raise ErrorIA(errores.OTRO, "el servicio no ha querido describir esta foto.")
    texto = "".join(b.text for b in respuesta.content if b.type == "text").strip()
    if not texto:
        raise ErrorIA(errores.OTRO, "la respuesta llegó vacía.")
    return texto


def describir(clave, modelo, prompt, datos_jpeg, timeout=60, cliente=None):
    cliente = cliente or anthropic.Anthropic(api_key=clave, timeout=timeout, max_retries=1)
    try:
        # max_tokens incluye lo que el modelo razona antes de contestar: con poco margen
        # la respuesta se corta.
        respuesta = cliente.messages.create(
            model=modelo, max_tokens=4000, messages=construir_mensajes(prompt, datos_jpeg))
    except anthropic.AuthenticationError:
        raise ErrorIA(errores.CLAVE)
    except anthropic.PermissionDeniedError:
        raise ErrorIA(errores.CLAVE)
    except anthropic.NotFoundError:
        raise ErrorIA(errores.MODELO)
    except anthropic.RateLimitError:
        raise ErrorIA(errores.LIMITE)
    except anthropic.APITimeoutError:  # Antes que APIConnectionError, que es su padre
        raise ErrorIA(errores.TIEMPO)
    except anthropic.APIConnectionError as e:
        raise ErrorIA(errores.CONEXION, str(e))
    except anthropic.APIStatusError as e:
        raise ErrorIA(errores.OTRO, f"código {e.status_code}. {e.message}")
    return extraer_texto(respuesta)
