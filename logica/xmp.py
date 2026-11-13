"""Descripción accesible dentro del paquete XMP (XML) de una foto.

Campos que se usan (ver docs en la memoria del proyecto y la prueba con el iPhone):
- Iptc4xmpExt:ArtworkContentDescription, como atributo de rdf:Description. Es donde
  Fotos de iOS guarda la descripción que lee VoiceOver, y la recoge al importar una
  foto (comprobado el 13/11/2026). Apple no lo documenta.
- Iptc4xmpCore:ExtDescrAccessibility, la "descripción extendida" accesible del
  estándar IPTC (2021), para otros programas.
- Iptc4xmpCore:AltTextAccessibility solo se lee.
"""
import xml.etree.ElementTree as ET

NS = {
    "x": "adobe:ns:meta/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "Iptc4xmpExt": "http://iptc.org/std/Iptc4xmpExt/2008-02-29/",
    "Iptc4xmpCore": "http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "xmp": "http://ns.adobe.com/xap/1.0/",
    "photoshop": "http://ns.adobe.com/photoshop/1.0/",
    "exif": "http://ns.adobe.com/exif/1.0/",
    "tiff": "http://ns.adobe.com/tiff/1.0/",
    "xmpMM": "http://ns.adobe.com/xap/1.0/mm/",
}
for _prefijo, _uri in NS.items():
    ET.register_namespace(_prefijo, _uri)

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
APPLE = "{%s}ArtworkContentDescription" % NS["Iptc4xmpExt"]
EXTENDIDA = "{%s}ExtDescrAccessibility" % NS["Iptc4xmpCore"]
ALTERNATIVO = "{%s}AltTextAccessibility" % NS["Iptc4xmpCore"]
DESCRIPTION = "{%s}Description" % NS["rdf"]
RDF = "{%s}RDF" % NS["rdf"]

PAQUETE_VACIO = ('<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
                 'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
                 '<rdf:Description rdf:about=""/></rdf:RDF></x:xmpmeta>')


def _raiz(paquete):
    """Elemento x:xmpmeta del paquete; quita el envoltorio <?xpacket ...?> si lo hay."""
    if isinstance(paquete, bytes):
        paquete = paquete.decode("utf-8", errors="replace")
    inicio = paquete.find("<x:xmpmeta")
    fin = paquete.rfind("</x:xmpmeta>")
    if inicio == -1:
        # Algunos programas escriben el rdf:RDF sin x:xmpmeta alrededor.
        raiz = ET.Element("{%s}xmpmeta" % NS["x"])
        raiz.append(ET.fromstring(paquete[paquete.find("<rdf:RDF"):paquete.rfind("</rdf:RDF>") + 10]))
        return raiz
    return ET.fromstring(paquete[inicio:fin + len("</x:xmpmeta>")])


def _texto_alt(elemento):
    """Texto de una propiedad rdf:Alt (con idiomas): prefiere x-default."""
    textos = elemento.findall(".//{%s}li" % NS["rdf"])
    for li in textos:
        if li.get(XML_LANG) == "x-default" and li.text:
            return li.text
    for li in textos:
        if li.text:
            return li.text
    return elemento.text or ""


def leer_descripcion(paquete):
    """Descripción accesible del XMP, o '' si no hay. Acepta str o bytes."""
    if not paquete:
        return ""
    try:
        raiz = _raiz(paquete)
    except ET.ParseError:
        return ""
    descripciones = raiz.iter(DESCRIPTION)
    candidatos = {APPLE: "", EXTENDIDA: "", ALTERNATIVO: ""}
    for descripcion in descripciones:
        if descripcion.get(APPLE) and not candidatos[APPLE]:
            candidatos[APPLE] = descripcion.get(APPLE)
        for campo in candidatos:
            hijo = descripcion.find(campo)
            if hijo is not None and not candidatos[campo]:
                candidatos[campo] = _texto_alt(hijo) if campo != APPLE else (hijo.text or "")
    for campo in (APPLE, EXTENDIDA, ALTERNATIVO):
        if candidatos[campo].strip():
            return candidatos[campo].strip()
    return ""


def poner_descripcion(paquete, texto):
    """Devuelve el paquete XMP (str) con la descripción puesta, o quitada si texto es ''.

    Conserva el resto de propiedades. `paquete` puede ser None si la foto no tenía XMP.
    """
    raiz = _raiz(paquete) if paquete else ET.fromstring(PAQUETE_VACIO)
    rdf = raiz.find(RDF)
    if rdf is None:
        rdf = ET.SubElement(raiz, RDF)
    descripciones = list(rdf.iter(DESCRIPTION))
    if not descripciones:
        descripciones = [ET.SubElement(rdf, DESCRIPTION, {"{%s}about" % NS["rdf"]: ""})]

    # Se quita de todas partes y se escribe una sola vez: si hubiera dos valores
    # distintos, cada programa podría leer uno diferente.
    for descripcion in descripciones:
        descripcion.attrib.pop(APPLE, None)
        for campo in (APPLE, EXTENDIDA):
            for hijo in descripcion.findall(campo):
                descripcion.remove(hijo)

    texto = texto.strip()
    if texto:
        principal = descripciones[0]
        principal.set(APPLE, texto)
        extendida = ET.SubElement(principal, EXTENDIDA)
        alternativas = ET.SubElement(extendida, "{%s}Alt" % NS["rdf"])
        ET.SubElement(alternativas, "{%s}li" % NS["rdf"], {XML_LANG: "x-default"}).text = texto
    return ET.tostring(raiz, encoding="unicode")
