import xml.etree.ElementTree as ET

from logica import xmp
from logica.pruebas.datos_apple import XMP_CON_PIE_DE_FOTO, XMP_SOLO_DESCRIPCION


def prueba_lee_el_campo_de_apple():
    assert xmp.leer_descripcion(XMP_SOLO_DESCRIPCION) == "Un cielo al atardecer sobre el mar."
    assert xmp.leer_descripcion(XMP_CON_PIE_DE_FOTO.encode()) == "Un barco atracado en el puerto"


def prueba_lee_los_campos_accesibles_del_estandar_iptc():
    paquete = xmp.poner_descripcion(None, "Texto del estándar")
    # Se borra el campo de Apple para comprobar que se lee el de IPTC
    raiz = ET.fromstring(paquete)
    for d in raiz.iter(xmp.DESCRIPTION):
        d.attrib.pop(xmp.APPLE, None)
    assert xmp.leer_descripcion(ET.tostring(raiz, encoding="unicode")) == "Texto del estándar"


def prueba_sin_xmp_o_roto_no_hay_descripcion():
    assert xmp.leer_descripcion(None) == ""
    assert xmp.leer_descripcion("<x:xmpmeta esto no es xml") == ""


def prueba_escribe_en_apple_y_en_iptc():
    paquete = xmp.poner_descripcion(None, "Río con niebla & pinos <al fondo>")
    raiz = ET.fromstring(paquete)
    descripcion = next(raiz.iter(xmp.DESCRIPTION))
    assert descripcion.get(xmp.APPLE) == "Río con niebla & pinos <al fondo>"
    li = descripcion.find(xmp.EXTENDIDA).find(".//{%s}li" % xmp.NS["rdf"])
    assert li.text == "Río con niebla & pinos <al fondo>"
    assert li.get(xmp.XML_LANG) == "x-default"


def prueba_sustituye_sin_perder_lo_demas():
    paquete = xmp.poner_descripcion(XMP_SOLO_DESCRIPCION, "Nueva descripción")
    assert xmp.leer_descripcion(paquete) == "Nueva descripción"
    assert "Un cielo al atardecer" not in paquete
    assert "2026-11-11T10:56:28" in paquete  # La fecha de Apple sigue ahí
    # Una sola vez cada campo, aunque se guarde dos veces
    paquete = xmp.poner_descripcion(paquete, "Otra más")
    raiz = ET.fromstring(paquete)
    assert len(raiz.findall(".//" + xmp.EXTENDIDA)) == 1
    assert xmp.leer_descripcion(paquete) == "Otra más"


def prueba_no_toca_el_pie_de_foto():
    paquete = xmp.poner_descripcion(XMP_CON_PIE_DE_FOTO, "Descripción nueva")
    raiz = ET.fromstring(paquete)
    pie = raiz.find(".//{%s}description" % xmp.NS["dc"])
    assert pie is not None


def prueba_descripcion_vacia_la_quita():
    paquete = xmp.poner_descripcion(XMP_SOLO_DESCRIPCION, "  ")
    assert xmp.leer_descripcion(paquete) == ""
    assert "ArtworkContentDescription" not in paquete
