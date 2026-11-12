import pytest

from ia import errores, servicio
from ia.errores import ErrorIA
from ia.servicio import Ajustes


def prueba_modelo_vacio_usa_el_primero_del_servicio():
    assert Ajustes("gemini", "  ", "").modelo_efectivo() == "gemini-3.8-flash"


def prueba_la_url_solo_se_cambia_en_servicios_locales():
    assert Ajustes("ollama", "m", "http://otro:11434/v1").url_efectiva() == "http://otro:11434/v1"
    assert Ajustes("ollama", "m", "").url_efectiva() == "http://localhost:11434/v1"
    assert Ajustes("openai", "m", "http://otro").url_efectiva() == "https://api.openai.com/v1"


def prueba_servicio_desconocido_vuelve_al_predeterminado():
    assert Ajustes("no-existe", "", "").proveedor.id == "openai"


def prueba_falta_clave_se_detecta_antes_de_llamar():
    with pytest.raises(ErrorIA) as e:
        servicio.enviar(Ajustes("openai", "m", ""), "", "p", b"x")
    assert e.value.tipo == errores.SIN_CLAVE


def prueba_texto_error_usa_nombre_corto_y_local():
    texto = servicio.texto_error(ErrorIA(errores.CONEXION), Ajustes("ollama", "", ""))
    assert texto == "No se puede conectar con Ollama. Comprueba que está abierto."
