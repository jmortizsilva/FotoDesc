"""Punto de entrada de FotoDesc."""
import wx

from ia import claves
from interfaz.configuracion import config
from interfaz.dialogos import DialogoAyuda
from interfaz.ventana_principal import VentanaPrincipal


def main():
    app = wx.App(False)
    # "ShowHelpOnStartup" y "OpenAI_API_Key" son los nombres de la versión 1.0: se
    # mantienen para no perder las preferencias de quien ya la usaba.
    preferencias = config()
    claves.migrar_clave_antigua(preferencias.Read("OpenAI_API_Key", ""),
                                lambda: preferencias.DeleteEntry("OpenAI_API_Key"))
    ventana = VentanaPrincipal(None)
    ventana.Show()
    if preferencias.ReadBool("ShowHelpOnStartup", True):
        dlg = DialogoAyuda(ventana)
        dlg.ShowModal()
        dlg.Destroy()
    app.MainLoop()


if __name__ == "__main__":
    main()
