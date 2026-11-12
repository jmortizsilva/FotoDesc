"""Elige el conector según el servicio configurado y prepara la foto."""
from dataclasses import dataclass

from PIL import Image

from ia import claude, compatible_openai, errores, imagen, proveedores
from ia.errores import ErrorIA

PROMPT = ("Describe esta foto en español para una persona ciega: qué se ve, dónde "
          "parece estar hecha y, si hay personas, qué hacen. Sin frases introductorias. "
          "Como máximo, cinco frases.")
PROMPT_PRUEBA = "Responde solo con la palabra OK."


@dataclass
class Ajustes:
    id_proveedor: str
    modelo: str
    url: str  # Solo cuenta para servicios con dirección editable (Ollama)

    @property
    def proveedor(self):
        return proveedores.buscar(self.id_proveedor)

    def url_efectiva(self):
        proveedor = self.proveedor
        if proveedor.es_local and self.url.strip():
            return self.url.strip()
        return proveedor.url

    def modelo_efectivo(self):
        return self.modelo.strip() or self.proveedor.modelos[0]


def enviar(ajustes, clave, prompt, datos_jpeg):
    proveedor = ajustes.proveedor
    if proveedor.necesita_clave and not clave:
        raise ErrorIA(errores.SIN_CLAVE)
    if proveedor.tipo == proveedores.ANTHROPIC:
        return claude.describir(clave, ajustes.modelo_efectivo(), prompt, datos_jpeg)
    return compatible_openai.describir(ajustes.url_efectiva(), clave,
                                       ajustes.modelo_efectivo(), prompt, datos_jpeg)


def describir_foto(ajustes, clave, ruta):
    try:
        datos = imagen.leer_y_preparar(ruta)
    except OSError as e:
        raise ErrorIA(errores.OTRO, f"no se pudo abrir la foto ({e}).")
    return enviar(ajustes, clave, PROMPT, datos)


def probar(ajustes, clave):
    """Envía una imagen mínima: comprueba clave, modelo y que el modelo acepta imágenes."""
    datos = imagen.preparar_jpeg(Image.new("RGB", (64, 64), "white"))
    return enviar(ajustes, clave, PROMPT_PRUEBA, datos)


def texto_error(error, ajustes):
    proveedor = ajustes.proveedor
    return errores.mensaje(error, proveedor.nombre_corto, ajustes.modelo_efectivo(),
                           es_local=proveedor.es_local)
