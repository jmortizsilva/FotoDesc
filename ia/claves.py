"""Claves de los servicios, en el almacén del sistema.

En Windows es el Administrador de credenciales; en Mac, el Llavero.
"""
import keyring
import keyring.errors

NOMBRE_EN_ALMACEN = "FotoDesc"


def leer(id_proveedor, almacen=keyring):
    try:
        return almacen.get_password(NOMBRE_EN_ALMACEN, id_proveedor) or ""
    except keyring.errors.KeyringError:
        return ""


def guardar(id_proveedor, clave, almacen=keyring):
    """Guarda la clave; si llega vacía, la borra. Los errores del almacén se propagan."""
    if clave:
        almacen.set_password(NOMBRE_EN_ALMACEN, id_proveedor, clave)
        return
    try:
        almacen.delete_password(NOMBRE_EN_ALMACEN, id_proveedor)
    except keyring.errors.PasswordDeleteError:
        pass


def migrar_clave_antigua(clave_antigua, borrar_antigua, almacen=keyring):
    """La 1.0 guardaba la clave de OpenAI sin cifrar en la configuración.

    La pasa al almacén y solo la borra de la configuración si se guardó bien.
    Devuelve True si migró algo.
    """
    if not clave_antigua:
        return False
    try:
        if not leer("openai", almacen):
            guardar("openai", clave_antigua, almacen)
    except keyring.errors.KeyringError:
        return False
    borrar_antigua()
    return True
