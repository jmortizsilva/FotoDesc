import pytest
from PIL import Image

wx = pytest.importorskip("wx")

from interfaz.ventana_principal import VentanaPrincipal  # noqa: E402


@pytest.fixture(scope="module")
def app():
    aplicacion = wx.App(False)
    yield aplicacion
    aplicacion.Destroy()


@pytest.fixture
def ventana(app):
    v = VentanaPrincipal(None)
    yield v
    v.Destroy()


@pytest.fixture
def fotos(tmp_path):
    rutas = []
    for i in range(4):
        ruta = tmp_path / f"foto{i}.jpg"
        Image.new("RGB", (8, 8)).save(ruta, "jpeg")
        rutas.append(str(ruta))
    return rutas


def prueba_anadir_varias_fotos_monta_la_lista_una_vez(ventana, fotos, monkeypatch):
    montajes = []
    original = ventana.refrescar_lista
    monkeypatch.setattr(ventana, "refrescar_lista", lambda: (montajes.append(1), original()))
    ventana.anadir_imagenes(fotos + fotos[:1])  # La repetida no se duplica
    assert montajes == [1]
    assert ventana.list_ctrl.GetItemCount() == 4


def prueba_no_pide_el_foco_con_la_lista_oculta(ventana, fotos, monkeypatch):
    # En Windows, pedir el foco para un control oculto saca
    # "'SetFocus' failed with error 0x00000057" y el foco no va a ningún sitio.
    peticiones = []
    monkeypatch.setattr(ventana.list_ctrl, "SetFocus", lambda: peticiones.append(1))
    ventana.Show()
    assert not ventana.list_panel.IsShown()
    ventana.anadir_imagenes(fotos)
    assert peticiones == []


class DialogoFalso:
    def __init__(self, resultado=None, error=None):
        self.resultado, self.error, self.destruido = resultado, error, False

    def ShowModal(self):
        if self.error:
            raise self.error
        return self.resultado

    def Destroy(self):
        self.destruido = True


def prueba_abrir_modal_devuelve_el_foco_siempre(ventana, monkeypatch):
    # En Windows, al cerrar el diálogo de IA el foco no volvía a la ventana principal.
    recuperaciones = []
    monkeypatch.setattr(ventana, "recuperar_foco", lambda foco=None: recuperaciones.append(1))
    dlg = DialogoFalso(resultado=wx.ID_OK)
    assert ventana.abrir_modal(dlg) == wx.ID_OK
    dlg_roto = DialogoFalso(error=RuntimeError("fallo"))
    with pytest.raises(RuntimeError):
        ventana.abrir_modal(dlg_roto)
    assert dlg.destruido and dlg_roto.destruido
    assert recuperaciones == [1, 1]


def prueba_recorrer_columnas_anuncia_nombre_y_valor(ventana, fotos, monkeypatch):
    dichos, pitidos = [], []
    monkeypatch.setattr("interfaz.voz.anunciar", lambda texto: dichos.append(texto))
    monkeypatch.setattr(wx, "Bell", lambda: pitidos.append(1))
    ventana.anadir_imagenes(fotos[:1])
    ventana.list_ctrl.Select(0)

    ventana.mover_columna(1)
    ventana.mover_columna(1)
    assert dichos == ["Descripción, sin datos", "Fecha, sin datos"]

    ventana.leer_columna(0)
    assert dichos[-1] == "Nombre, foto0.jpg"
    ventana.mover_columna(-1)  # Ya en la primera: pitido y nada más
    assert pitidos == [1] and len(dichos) == 3


def prueba_los_avisos_tienen_padre_y_devuelven_el_foco(ventana, monkeypatch):
    # En Windows, tras "Descripción guardada" el foco no volvía a la lista.
    llamadas, recuperaciones = [], []
    monkeypatch.setattr(wx, "MessageBox", lambda *args: llamadas.append(args))
    monkeypatch.setattr(ventana, "recuperar_foco", lambda foco=None: recuperaciones.append(1))
    ventana.avisar("Descripción guardada, a.jpg", "Confirmación", wx.OK)
    assert llamadas[0][3] is ventana
    assert recuperaciones == [1]


def prueba_ubicacion_buscando_y_despues_el_lugar(ventana, tmp_path):
    from logica import metadatos
    from logica.lugares import Lugar

    class BuscadorFalso:
        def __init__(self):
            self.pendientes = set()

        def anadir(self, rutas):
            self.pendientes.update(rutas)

    ruta = tmp_path / "con_gps.jpg"
    Image.new("RGB", (8, 8)).save(ruta, "jpeg")
    metadatos.guardar_cambios(str(ruta), metadatos.Cambios(gps=(40.8, -2.1)))
    ventana.buscador = BuscadorFalso()
    ventana.anadir_imagenes([str(ruta)])
    assert ventana.list_ctrl.GetItemText(0, 4) == "buscando"

    ventana.buscador.pendientes.clear()
    ventana.al_encontrar_lugar(str(ruta), Lugar(localidad="Peralejos de las Truchas",
                                                provincia="Guadalajara", codigo_pais="es"))
    assert ventana.list_ctrl.GetItemText(0, 4) == "Peralejos de las Truchas, Guadalajara"
    ventana.al_encontrar_lugar(str(ruta), None)
    assert ventana.list_ctrl.GetItemText(0, 4) == "40,8000; -2,1000"
