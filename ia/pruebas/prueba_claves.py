import keyring.errors

from ia import claves


class AlmacenFalso:
    def __init__(self, falla=False):
        self.datos = {}
        self.falla = falla

    def get_password(self, servicio, usuario):
        return self.datos.get((servicio, usuario))

    def set_password(self, servicio, usuario, clave):
        if self.falla:
            raise keyring.errors.PasswordSetError("sin almacén")
        self.datos[(servicio, usuario)] = clave

    def delete_password(self, servicio, usuario):
        if (servicio, usuario) not in self.datos:
            raise keyring.errors.PasswordDeleteError("no existe")
        del self.datos[(servicio, usuario)]


def prueba_guardar_leer_y_borrar():
    almacen = AlmacenFalso()
    claves.guardar("gemini", "abc", almacen)
    assert claves.leer("gemini", almacen) == "abc"
    claves.guardar("gemini", "", almacen)
    assert claves.leer("gemini", almacen) == ""
    claves.guardar("gemini", "", almacen)  # Borrar lo que no existe no falla


def prueba_migracion_mueve_la_clave_y_borra_la_antigua():
    almacen, borradas = AlmacenFalso(), []
    assert claves.migrar_clave_antigua("sk-vieja", lambda: borradas.append(1), almacen)
    assert claves.leer("openai", almacen) == "sk-vieja"
    assert borradas == [1]


def prueba_migracion_no_pisa_una_clave_nueva():
    almacen = AlmacenFalso()
    claves.guardar("openai", "sk-nueva", almacen)
    claves.migrar_clave_antigua("sk-vieja", lambda: None, almacen)
    assert claves.leer("openai", almacen) == "sk-nueva"


def prueba_si_el_almacen_falla_no_se_borra_la_antigua():
    borradas = []
    assert not claves.migrar_clave_antigua("sk-vieja", lambda: borradas.append(1), AlmacenFalso(falla=True))
    assert borradas == []


def prueba_sin_clave_antigua_no_hace_nada():
    assert not claves.migrar_clave_antigua("", lambda: 1 / 0, AlmacenFalso())
