"""Anuncios directos al lector de pantalla, con accessible_output2.

Habla con NVDA, JAWS y otros lectores. Si no hay ninguno activo usa la voz del
sistema (SAPI en Windows): con Narrador, que accessible_output2 no conoce, se oirá
esa voz en lugar de la de Narrador.
"""
import logging

_salidas = None


def _iniciar():
    global _salidas
    if _salidas is None:
        try:
            from accessible_output2.outputs.auto import Auto
            _salidas = Auto()
        except Exception:
            logging.exception("accessible_output2 no está disponible; no habrá anuncios")
            _salidas = False
    return _salidas


def anunciar(texto):
    """Dice el texto (y lo manda a braille si el lector lo admite). Devuelve si se pudo."""
    salidas = _iniciar()
    if not salidas:
        return False
    lector = salidas.get_first_available_output()
    if lector is None:
        return False
    # Auto.output() de accessible_output2 0.17 solo manda voz; output() del lector
    # concreto manda voz y braille.
    try:
        lector.output(texto, interrupt=True)
    except Exception:
        try:
            lector.speak(texto, interrupt=True)
        except Exception:
            logging.exception("No se pudo anunciar")
            return False
    return True
