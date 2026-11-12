import pytest

from ia import errores
from ia.errores import ErrorIA


@pytest.mark.parametrize("tipo, esperado", [
    (errores.SIN_CLAVE, "Falta la clave de OpenAI. Ponla en Configuración, Inteligencia artificial."),
    (errores.CLAVE, "La clave de OpenAI no es válida."),
    (errores.TIEMPO, "OpenAI no responde. Prueba de nuevo dentro de un rato."),
    (errores.LIMITE, "Has llegado al límite de OpenAI. Prueba más tarde o cambia de servicio."),
    (errores.MODELO, "El modelo gpt-6-luna no existe en OpenAI."),
    (errores.CONEXION, "No se puede conectar con OpenAI. Comprueba la conexión a internet."),
])
def prueba_textos_de_error(tipo, esperado):
    assert errores.mensaje(ErrorIA(tipo), "OpenAI", "gpt-6-luna") == esperado


def prueba_conexion_con_servicio_local():
    texto = errores.mensaje(ErrorIA(errores.CONEXION), "Ollama", "m", es_local=True)
    assert texto == "No se puede conectar con Ollama. Comprueba que está abierto."


def prueba_otro_error_lleva_el_detalle():
    texto = errores.mensaje(ErrorIA(errores.OTRO, "la respuesta llegó vacía."), "OpenAI", "m")
    assert texto == "No se pudo describir la foto: la respuesta llegó vacía."
