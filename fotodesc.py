"""Punto de entrada de FotoDesc."""
import wx

from interfaz.dialogos import CONFIG_APP, DialogoAyuda
from interfaz.ventana_principal import VentanaPrincipal


def main():
    app = wx.App(False)
    # Los nombres de las claves de configuración se mantienen para no perder
    # la clave ni las preferencias de quien ya usaba la versión 1.0.
    config = wx.Config(CONFIG_APP)
    ventana = VentanaPrincipal(None)
    ventana.clave = config.Read("OpenAI_API_Key", "")
    ventana.Show()
    if config.ReadBool("ShowHelpOnStartup", True):
        dlg = DialogoAyuda(ventana)
        dlg.ShowModal()
        dlg.Destroy()
    app.MainLoop()


if __name__ == "__main__":
    main()
