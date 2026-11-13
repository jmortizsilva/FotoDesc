from logica import lugares
from logica.lugares import Lugar


def respuesta(categoria="highway", tipo="residential", nombre="Calle Mayor", **direccion):
    base = {"country": "España", "country_code": "es"}
    base.update(direccion)
    return {"category": categoria, "type": tipo, "name": nombre, "address": base}


def prueba_monumento_localidad_y_provincia():
    lugar = lugares.desde_nominatim(respuesta("amenity", "place_of_worship", "Catedral de Burgos",
                                              city="Burgos", province="Burgos"))
    assert lugar.sitio == "Catedral de Burgos"
    assert lugares.texto(lugar) == "Catedral de Burgos, Burgos"


def prueba_una_calle_no_es_un_sitio():
    lugar = lugares.desde_nominatim(respuesta(village="Peralejos de las Truchas", province="Guadalajara"))
    assert lugar.sitio == ""
    assert lugares.texto(lugar) == "Peralejos de las Truchas, Guadalajara"


def prueba_un_bar_tampoco():
    lugar = lugares.desde_nominatim(respuesta("amenity", "bar", "Bar Pepe", town="Molina", province="Guadalajara"))
    assert lugar.sitio == ""


def prueba_en_el_extranjero_se_anade_el_pais():
    lugar = lugares.desde_nominatim({
        "category": "place", "type": "city", "name": "Tromsø",
        "address": {"city": "Tromsø", "county": "Troms", "country": "Noruega", "country_code": "NO"}})
    assert lugar.codigo_pais == "no"
    assert lugares.texto(lugar) == "Tromsø, Troms, Noruega"


def prueba_sin_resultado():
    assert lugares.desde_nominatim({"error": "Unable to geocode"}).vacio()
    assert lugares.desde_nominatim(None).vacio()
    assert lugares.texto(Lugar()) == ""


def prueba_ida_y_vuelta_por_diccionario():
    lugar = Lugar("Faro", "Cádiz", "Cádiz", "España", "es")
    assert Lugar.desde_dict(lugar.a_dict()) == lugar
    assert Lugar.desde_dict({"localidad": "Soria"}) == Lugar(localidad="Soria")


def prueba_clave_agrupa_fotos_cercanas():
    assert lugares.clave(40.81234, -2.10345) == lugares.clave(40.81199, -2.10301)
    assert lugares.clave(40.812, -2.103) != lugares.clave(40.822, -2.103)
