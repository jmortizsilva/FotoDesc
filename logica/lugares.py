"""Lugar legible a partir de las coordenadas: sitio o monumento, localidad, provincia, país."""
from dataclasses import asdict, dataclass

# Categorías y tipos de OpenStreetMap cuyo nombre interesa como "sitio": monumentos,
# parajes, iglesias... No los bares ni las tiendas.
SITIOS = {
    "tourism": None,  # None: cualquier tipo
    "historic": None,
    "natural": None,
    "leisure": {"park", "garden", "nature_reserve", "beach_resort"},
    "man_made": {"lighthouse", "tower", "bridge", "windmill", "watermill"},
    "amenity": {"place_of_worship"},
    "building": {"cathedral", "church", "chapel", "mosque", "synagogue", "temple", "castle"},
    "waterway": {"waterfall"},
}


@dataclass
class Lugar:
    sitio: str = ""
    localidad: str = ""
    provincia: str = ""
    pais: str = ""
    codigo_pais: str = ""  # ISO de dos letras, en minúsculas

    def vacio(self):
        return not (self.sitio or self.localidad or self.provincia or self.pais)

    def a_dict(self):
        return asdict(self)

    @classmethod
    def desde_dict(cls, datos):
        return cls(**{k: datos.get(k, "") for k in cls.__dataclass_fields__})


def desde_nominatim(respuesta):
    """Lugar a partir de la respuesta de /reverse (format=jsonv2, addressdetails=1)."""
    if not respuesta or "error" in respuesta:
        return Lugar()
    direccion = respuesta.get("address", {})
    sitio = ""
    categoria, tipo = respuesta.get("category", ""), respuesta.get("type", "")
    tipos = SITIOS.get(categoria, set())
    if respuesta.get("name") and categoria in SITIOS and (tipos is None or tipo in tipos):
        sitio = respuesta["name"]
    localidad = next((direccion[c] for c in ("city", "town", "village", "hamlet", "municipality")
                      if direccion.get(c)), "")
    provincia = next((direccion[c] for c in ("province", "county", "state_district", "state")
                      if direccion.get(c)), "")
    return Lugar(sitio, localidad, provincia, direccion.get("country", ""),
                 direccion.get("country_code", "").lower())


def texto(lugar, pais_propio="es"):
    """'Catedral de Burgos, Burgos' o 'Tromsø, Troms, Noruega'. El país solo si es otro."""
    partes = [lugar.sitio, lugar.localidad, lugar.provincia]
    if lugar.codigo_pais and lugar.codigo_pais != pais_propio:
        partes.append(lugar.pais)
    resultado = []
    for parte in partes:
        parte = parte.strip()
        # "Burgos, Burgos" no aporta: localidad y provincia se llaman igual a menudo.
        if parte and parte.lower() not in (p.lower() for p in resultado):
            resultado.append(parte)
    return ", ".join(resultado)


def clave(latitud, longitud):
    """Clave para reutilizar resultados: tres decimales, unos 100 metros."""
    return f"{latitud:.3f},{longitud:.3f}"
