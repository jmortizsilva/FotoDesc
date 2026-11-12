import keyring.errors
import wx

from ia import claves, proveedores, servicio
from ia.errores import ErrorIA
from ia.servicio import Ajustes
from interfaz import configuracion
from interfaz.progreso import Cancelado, ejecutar_con_progreso

TITULO = "Inteligencia artificial"


class DialogoIA(wx.Dialog):
    """Servicio, modelo, clave y, para Ollama, dirección.

    Los cambios de cada servicio se recuerdan al cambiar de uno a otro en la lista y
    solo se guardan al pulsar Aceptar.
    """

    def __init__(self, parent):
        super().__init__(parent, title=TITULO)
        self.pendientes = {}  # id -> (modelo, dirección, clave)
        self.id_actual = None
        panel = wx.Panel(self)
        rejilla = wx.FlexGridSizer(cols=2, vgap=8, hgap=8)
        rejilla.AddGrowableCol(1)

        # Cada etiqueta se crea justo antes de su control: así la leen los lectores.
        rejilla.Add(wx.StaticText(panel, label="Servicio:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.servicio = wx.Choice(panel, choices=[p.nombre for p in proveedores.PROVEEDORES])
        rejilla.Add(self.servicio, 1, wx.EXPAND)

        rejilla.Add(wx.StaticText(panel, label="Modelo:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.modelo = wx.ComboBox(panel, style=wx.CB_DROPDOWN)
        rejilla.Add(self.modelo, 1, wx.EXPAND)

        self.etiqueta_clave = wx.StaticText(panel, label="Clave:")
        rejilla.Add(self.etiqueta_clave, 0, wx.ALIGN_CENTER_VERTICAL)
        # wx no deja cambiar el estilo de contraseña de un campo ya creado, así que hay
        # dos campos y "Mostrar clave" alterna cuál se ve.
        caja_clave = wx.BoxSizer(wx.HORIZONTAL)
        self.clave_oculta = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        self.clave_visible = wx.TextCtrl(panel)
        self.clave_visible.Hide()
        caja_clave.Add(self.clave_oculta, 1, wx.EXPAND)
        caja_clave.Add(self.clave_visible, 1, wx.EXPAND)
        rejilla.Add(caja_clave, 1, wx.EXPAND)

        rejilla.AddSpacer(0)
        self.mostrar = wx.CheckBox(panel, label="Mostrar clave")
        rejilla.Add(self.mostrar)

        self.etiqueta_direccion = wx.StaticText(panel, label="Dirección:")
        rejilla.Add(self.etiqueta_direccion, 0, wx.ALIGN_CENTER_VERTICAL)
        self.direccion = wx.TextCtrl(panel)
        rejilla.Add(self.direccion, 1, wx.EXPAND)

        botones = wx.BoxSizer(wx.HORIZONTAL)
        self.probar = wx.Button(panel, label="Probar")
        aceptar = wx.Button(panel, wx.ID_OK, label="Aceptar")
        cancelar = wx.Button(panel, wx.ID_CANCEL, label="Cancelar")
        aceptar.SetDefault()
        for boton in (self.probar, aceptar, cancelar):
            botones.Add(boton, 0, wx.ALL, 5)

        caja = wx.BoxSizer(wx.VERTICAL)
        caja.Add(rejilla, 1, wx.EXPAND | wx.ALL, 12)
        caja.Add(botones, 0, wx.ALIGN_CENTER | wx.BOTTOM, 8)
        panel.SetSizer(caja)
        self.panel = panel
        exterior = wx.BoxSizer(wx.VERTICAL)
        exterior.Add(panel, 1, wx.EXPAND)
        self.SetSizer(exterior)

        self.servicio.Bind(wx.EVT_CHOICE, self.al_cambiar_servicio)
        self.mostrar.Bind(wx.EVT_CHECKBOX, self.al_mostrar_clave)
        self.probar.Bind(wx.EVT_BUTTON, self.al_probar)
        aceptar.Bind(wx.EVT_BUTTON, self.al_aceptar)

        activo = configuracion.leer_ajustes().proveedor
        self.servicio.SetSelection(proveedores.PROVEEDORES.index(activo))
        self.cargar(activo.id)
        self.Centre()
        self.servicio.SetFocus()

    # ---------- Estado de los campos ----------

    def proveedor_elegido(self):
        return proveedores.PROVEEDORES[self.servicio.GetSelection()]

    def clave_escrita(self):
        campo = self.clave_visible if self.mostrar.GetValue() else self.clave_oculta
        return campo.GetValue().strip()

    def recordar_actual(self):
        if self.id_actual:
            self.pendientes[self.id_actual] = (self.modelo.GetValue().strip(),
                                               self.direccion.GetValue().strip(),
                                               self.clave_escrita())

    def cargar(self, id_proveedor):
        proveedor = proveedores.buscar(id_proveedor)
        if id_proveedor in self.pendientes:
            modelo, direccion, clave = self.pendientes[id_proveedor]
        else:
            guardados = configuracion.leer_ajustes_de(id_proveedor)
            modelo, direccion = guardados.modelo, guardados.url
            clave = claves.leer(id_proveedor)
        self.id_actual = id_proveedor

        self.modelo.Set(proveedor.modelos)
        self.modelo.SetValue(modelo or proveedor.modelos[0])
        self.clave_oculta.SetValue(clave)
        self.clave_visible.SetValue(clave)
        self.direccion.SetValue(direccion or proveedor.url)

        self.etiqueta_clave.SetLabel("Clave:" if proveedor.necesita_clave else "Clave (no hace falta):")
        for campo in (self.clave_oculta, self.clave_visible, self.mostrar):
            campo.Enable(proveedor.necesita_clave)
        self.etiqueta_direccion.Show(proveedor.es_local)
        self.direccion.Show(proveedor.es_local)
        self.ajustar_tamano()

    def ajustar_tamano(self):
        # Al mostrar u ocultar la dirección cambia la altura; el ancho mínimo evita
        # que los campos queden demasiado estrechos.
        self.panel.Layout()
        self.GetSizer().Fit(self)
        ancho, alto = self.GetSize()
        self.SetSize(max(ancho, 520), alto)

    def ajustes_escritos(self):
        return Ajustes(self.proveedor_elegido().id, self.modelo.GetValue().strip(),
                       self.direccion.GetValue().strip())

    # ---------- Eventos ----------

    def al_cambiar_servicio(self, event):
        self.recordar_actual()
        self.cargar(self.proveedor_elegido().id)

    def al_mostrar_clave(self, event):
        mostrar = self.mostrar.GetValue()
        origen, destino = ((self.clave_oculta, self.clave_visible) if mostrar
                           else (self.clave_visible, self.clave_oculta))
        destino.SetValue(origen.GetValue())
        origen.Hide()
        destino.Show()
        self.panel.Layout()

    def al_probar(self, event):
        ajustes = self.ajustes_escritos()
        nombre = ajustes.proveedor.nombre_corto
        try:
            ejecutar_con_progreso(self, f"Probando {nombre}",
                                  lambda: servicio.probar(ajustes, self.clave_escrita()))
        except Cancelado:
            return
        except ErrorIA as e:
            wx.MessageBox(servicio.texto_error(e, ajustes), "Error", wx.OK | wx.ICON_ERROR, self)
            return
        wx.MessageBox(f"Conexión correcta, {nombre}", TITULO, wx.OK | wx.ICON_INFORMATION, self)

    def al_aceptar(self, event):
        self.recordar_actual()
        try:
            for id_proveedor, (modelo, direccion, clave) in self.pendientes.items():
                configuracion.guardar_ajustes(Ajustes(id_proveedor, modelo, direccion), activar=False)
                if clave != claves.leer(id_proveedor):
                    claves.guardar(id_proveedor, clave)
        except keyring.errors.KeyringError as e:
            wx.MessageBox(f"No se pudo guardar la clave: {e}", "Error", wx.OK | wx.ICON_ERROR, self)
            return
        configuracion.guardar_ajustes(self.ajustes_escritos(), activar=True)
        self.EndModal(wx.ID_OK)
