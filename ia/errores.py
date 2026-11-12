"""Errores de los servicios de IA, ya clasificados, y el texto que se muestra."""

SIN_CLAVE = "sin_clave"
CLAVE = "clave"
TIEMPO = "tiempo"
LIMITE = "limite"
MODELO = "modelo"
CONEXION = "conexion"
OTRO = "otro"


class ErrorIA(Exception):
    def __init__(self, tipo, detalle=""):
        super().__init__(detalle or tipo)
        self.tipo = tipo
        self.detalle = detalle


def tipo_por_estado_http(estado, cuerpo=""):
    """Clasifica una respuesta HTTP fallida."""
    if estado in (401, 403):
        return CLAVE
    # Gemini responde 400 (no 401) cuando la clave no es válida.
    if estado == 400 and "api key" in cuerpo.lower():
        return CLAVE
    if estado == 404:
        return MODELO
    if estado == 429:
        return LIMITE
    if estado in (408, 504):
        return TIEMPO
    return OTRO


def mensaje(error, servicio, modelo, es_local=False):
    """Texto para el usuario. `servicio` es el nombre corto: OpenAI, Google Gemini..."""
    if error.tipo == SIN_CLAVE:
        return f"Falta la clave de {servicio}. Ponla en Configuración, Inteligencia artificial."
    if error.tipo == CLAVE:
        return f"La clave de {servicio} no es válida."
    if error.tipo == TIEMPO:
        return f"{servicio} no responde. Prueba de nuevo dentro de un rato."
    if error.tipo == LIMITE:
        return f"Has llegado al límite de {servicio}. Prueba más tarde o cambia de servicio."
    if error.tipo == MODELO:
        return f"El modelo {modelo} no existe en {servicio}."
    if error.tipo == CONEXION and es_local:
        return f"No se puede conectar con {servicio}. Comprueba que está abierto."
    if error.tipo == CONEXION:
        return f"No se puede conectar con {servicio}. Comprueba la conexión a internet."
    return "No se pudo describir la foto: " + (error.detalle or "error desconocido")
