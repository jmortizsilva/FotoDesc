import threading

import wx


class Cancelado(Exception):
    pass


def ejecutar_con_progreso(padre, titulo, funcion):
    """Ejecuta `funcion` en un hilo con una ventana de progreso que se puede cancelar.

    Devuelve lo que devuelva `funcion`, relanza su excepción o lanza Cancelado. Si se
    cancela, el hilo no se puede parar: termina por su cuenta y su resultado se descarta.
    """
    resultado = {}

    def trabajo():
        try:
            resultado["valor"] = funcion()
        except BaseException as e:
            resultado["error"] = e

    foco = wx.Window.FindFocus()
    hilo = threading.Thread(target=trabajo, daemon=True)
    hilo.start()
    dialogo = wx.ProgressDialog(titulo, titulo, parent=padre,
                                style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_AUTO_HIDE)
    try:
        while hilo.is_alive():
            seguir, _ = dialogo.Pulse()
            if not seguir:
                raise Cancelado()
            wx.MilliSleep(100)
    finally:
        dialogo.Destroy()
        # Al cerrarse la ventana de progreso, Windows no devuelve el foco a la que
        # la abrió: el lector se queda sin ventana activa.
        padre.GetTopLevelParent().Raise()
        if foco:
            foco.SetFocus()
    if "error" in resultado:
        raise resultado["error"]
    return resultado.get("valor")
