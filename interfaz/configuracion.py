"""Ajustes que no son secretos, en wx.Config (registro en Windows, preferencias en Mac)."""
import wx

from ia import proveedores
from ia.servicio import Ajustes

CONFIG_APP = "FotodescApp"


def config():
    return wx.Config(CONFIG_APP)


def leer_ajustes():
    return leer_ajustes_de(config().Read("Servicio", proveedores.PREDETERMINADO))


def leer_ajustes_de(id_proveedor):
    c = config()
    return Ajustes(id_proveedor, c.Read("Modelo_" + id_proveedor, ""), c.Read("Direccion_" + id_proveedor, ""))


def guardar_ajustes(ajustes, activar=True):
    """Guarda modelo y dirección del servicio; con activar, lo deja como el servicio en uso."""
    c = config()
    if activar:
        c.Write("Servicio", ajustes.id_proveedor)
    c.Write("Modelo_" + ajustes.id_proveedor, ajustes.modelo)
    c.Write("Direccion_" + ajustes.id_proveedor, ajustes.url)
    c.Flush()
