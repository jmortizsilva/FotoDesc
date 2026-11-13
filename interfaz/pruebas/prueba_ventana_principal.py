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
