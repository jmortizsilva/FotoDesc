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
