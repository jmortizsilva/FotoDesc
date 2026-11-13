import os

import wx

from ia import claves, servicio
from ia.errores import ErrorIA
from interfaz import configuracion
from interfaz.dialogo_ia import DialogoIA
from interfaz.dialogos import DialogoAcercaDe, DialogoAyuda, DialogoEditar
from interfaz.progreso import Cancelado, ejecutar_con_progreso
from interfaz import voz
from interfaz.buscador_lugares import BuscadorLugares
from logica import columnas, lugares, metadatos
from ubicacion.cache import CacheLugares
from ubicacion.nominatim import Nominatim

EXTENSIONES = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".heif", ".heic")


class PanelSinFoco(wx.Panel):
    """Panel de la vista previa: el tabulador lo salta."""

    def AcceptsFocus(self):
        return False


class VentanaPrincipal(wx.Frame):
    def __init__(self, parent):
        self.id_add_image = wx.NewIdRef()
        self.id_add_folder = wx.NewIdRef()
        self.id_config = wx.NewIdRef()
        self.id_about = wx.NewIdRef()
        self.id_edit = wx.NewIdRef()
        self.id_auto_desc = wx.NewIdRef()
        self.id_back = wx.NewIdRef()
        self.id_help = wx.NewIdRef()
        self.id_ia = wx.NewIdRef()
        super().__init__(parent, title="FotoDesc", size=(1000, 700))
        self.imagenes = []     # Rutas, en el mismo orden que las filas de la lista
        self.columna = 0       # Columna en la que está quien recorre la lista con izquierda/derecha
        self.buscador = None   # Busca el lugar de las fotos con GPS; se crea al cargar fotos
        self.InitUI()
        self.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_ALT, ord("I"), self.id_add_image),
            (wx.ACCEL_ALT, ord("C"), self.id_add_folder),
            (wx.ACCEL_ALT, ord("F"), self.id_config),
            (wx.ACCEL_ALT, ord("U"), self.id_about),
            (wx.ACCEL_ALT, ord("A"), self.id_back),
            (wx.ACCEL_ALT, ord("E"), self.id_edit),
            (wx.ACCEL_ALT, ord("O"), self.id_auto_desc),
            # En la 1.0, F1 y Ctrl+K solo aparecían en el menú de Configuración y no
            # funcionaban desde la ventana.
            (wx.ACCEL_NORMAL, wx.WXK_F1, self.id_help),
            (wx.ACCEL_CTRL, ord("K"), self.id_ia),
        ]))
        self.Bind(wx.EVT_MENU, self.on_add_image, id=self.id_add_image)
        self.Bind(wx.EVT_MENU, self.on_add_folder, id=self.id_add_folder)
        self.Bind(wx.EVT_MENU, self.on_config, id=self.id_config)
        self.Bind(wx.EVT_MENU, self.on_about, id=self.id_about)
        self.Bind(wx.EVT_MENU, self.on_back, id=self.id_back)
        self.Bind(wx.EVT_MENU, self.on_edit, id=self.id_edit)
        self.Bind(wx.EVT_MENU, self.on_auto_desc, id=self.id_auto_desc)
        self.Bind(wx.EVT_MENU, self.mostrar_ayuda, id=self.id_help)
        self.Bind(wx.EVT_MENU, self.mostrar_dialogo_ia, id=self.id_ia)

    def InitUI(self):
        self.main_panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Pantalla de inicio
        self.start_panel = wx.Panel(self.main_panel)
        start_sizer = wx.BoxSizer(wx.VERTICAL)
        btn_add_image = wx.Button(self.start_panel, label="Añadir imagen")
        btn_add_image.SetToolTip("Atajo: Alt+I")
        btn_add_folder = wx.Button(self.start_panel, label="Añadir carpeta")
        btn_add_folder.SetToolTip("Atajo: Alt+C")
        btn_config = wx.Button(self.start_panel, label="Configuración")
        btn_config.SetToolTip("Atajo: Alt+F")
        start_sizer.Add(btn_add_image, 0, wx.ALL | wx.CENTER, 10)
        start_sizer.Add(btn_add_folder, 0, wx.ALL | wx.CENTER, 10)
        start_sizer.Add(btn_config, 0, wx.ALL | wx.CENTER, 10)
        self.start_panel.SetSizer(start_sizer)

        btn_add_image.Bind(wx.EVT_BUTTON, self.on_add_image)
        btn_add_folder.Bind(wx.EVT_BUTTON, self.on_add_folder)
        btn_config.Bind(wx.EVT_BUTTON, self.on_config)

        # Pantalla de listado de imágenes
        self.list_panel = wx.Panel(self.main_panel)
        list_panel_sizer = wx.BoxSizer(wx.VERTICAL)

        btn_back = wx.Button(self.list_panel, label="Atrás")
        btn_back.SetToolTip("Atajo: Alt+A")
        btn_back.Bind(wx.EVT_BUTTON, self.on_back)
        list_panel_sizer.Add(btn_back, 0, wx.ALL | wx.CENTER, 5)

        label_listado = wx.StaticText(self.list_panel, label="Listado de Imágenes:")
        list_panel_sizer.Add(label_listado, 0, wx.ALL, 5)

        splitter_holder = wx.Panel(self.list_panel)
        splitter_holder_sizer = wx.BoxSizer(wx.VERTICAL)
        self.splitter_list = wx.SplitterWindow(splitter_holder, style=wx.SP_LIVE_UPDATE)

        # Panel izquierdo: listado
        panel_list = wx.Panel(self.splitter_list)
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_ctrl = wx.ListCtrl(panel_list, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.SetToolTip("Listado de imágenes")
        anchos = [180, 360, 150, 80, 280]
        for indice, (titulo, ancho) in enumerate(zip(columnas.COLUMNAS, anchos)):
            self.list_ctrl.InsertColumn(indice, titulo, width=ancho)
        list_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        btn_panel = wx.Panel(panel_list)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_edit = wx.Button(btn_panel, label="Editar")
        self.btn_edit.SetToolTip("Atajo: Alt+E")
        self.btn_auto_desc = wx.Button(btn_panel, label="Obtener descripción")
        self.btn_auto_desc.SetToolTip("Atajo: Alt+O")
        self.btn_config = wx.Button(btn_panel, label="Configuración")
        self.btn_config.SetToolTip("Atajo: Alt+F")
        btn_sizer.Add(self.btn_edit, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_auto_desc, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_config, 0, wx.ALL, 5)
        btn_panel.SetSizer(btn_sizer)
        list_sizer.Add(btn_panel, 0, wx.ALIGN_CENTER)
        panel_list.SetSizer(list_sizer)

        # Panel derecho: vista previa
        self.panel_preview = PanelSinFoco(self.splitter_list)
        preview_sizer = wx.BoxSizer(wx.VERTICAL)
        self.preview_bitmap = wx.StaticBitmap(self.panel_preview, wx.ID_ANY, wx.NullBitmap)
        preview_sizer.Add(self.preview_bitmap, 1, wx.EXPAND | wx.ALL, 10)
        self.panel_preview.SetSizer(preview_sizer)

        self.splitter_list.SplitVertically(panel_list, self.panel_preview, sashPosition=600)
        splitter_holder_sizer.Add(self.splitter_list, 1, wx.EXPAND)
        splitter_holder.SetSizer(splitter_holder_sizer)

        list_panel_sizer.Add(splitter_holder, 1, wx.EXPAND)
        self.list_panel.SetSizer(list_panel_sizer)

        self.sizer.Add(self.start_panel, 1, wx.EXPAND | wx.ALL, 10)
        self.sizer.Add(self.list_panel, 1, wx.EXPAND | wx.ALL, 10)
        self.list_panel.Hide()

        self.main_panel.SetSizer(self.sizer)
        self.SetMinSize((800, 600))
        self.Centre()

        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_item_selected)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_list_item_activated)
        self.list_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_list_key_down)
        self.btn_edit.Bind(wx.EVT_BUTTON, self.on_edit)
        self.btn_auto_desc.Bind(wx.EVT_BUTTON, self.on_auto_desc)
        self.btn_config.Bind(wx.EVT_BUTTON, self.on_config)

    def on_add_image(self, event):
        comodin = ";".join("*" + e for e in EXTENSIONES)
        dlg = wx.FileDialog(self, "Selecciona una imagen",
                            wildcard=f"Archivos de imagen ({comodin})|{comodin}",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.anadir_imagenes([dlg.GetPath()])
            self.mostrar_listado()
        dlg.Destroy()

    def on_add_folder(self, event):
        dlg = wx.DirDialog(self, "Selecciona una carpeta", defaultPath=os.path.expanduser("~"),
                           style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            carpeta = dlg.GetPath()
            if self.imagenes:
                msg = ("Ya hay imágenes cargadas.\n\n"
                       "¿Desea añadir las nuevas imágenes a la lista actual o reemplazarla?")
                confirmar = wx.MessageDialog(self, msg, "Agregar o Reemplazar", wx.YES_NO | wx.ICON_QUESTION)
                try:
                    confirmar.SetYesNoLabels("Añadir", "Reemplazar")
                except AttributeError:
                    pass
                resultado = confirmar.ShowModal()
                confirmar.Destroy()
                if resultado == wx.ID_NO:
                    self.imagenes = []
                    if self.buscador:
                        self.buscador.vaciar()
            self.anadir_imagenes(os.path.join(carpeta, nombre) for nombre in sorted(os.listdir(carpeta))
                                 if nombre.lower().endswith(EXTENSIONES))
            self.mostrar_listado()
        dlg.Destroy()

    def on_config(self, event):
        menu = wx.Menu()
        id_help = wx.NewIdRef()
        id_api = wx.NewIdRef()
        id_about = wx.NewIdRef()
        menu.Append(id_help, "Ayuda\tF1")
        menu.Append(id_api, "Inteligencia artificial…\tCtrl+K")
        menu.Append(id_about, "Acerca de\tAlt+U")
        self.Bind(wx.EVT_MENU, self.mostrar_ayuda, id=id_help)
        self.Bind(wx.EVT_MENU, self.mostrar_dialogo_ia, id=id_api)
        self.Bind(wx.EVT_MENU, self.on_about, id=id_about)
        btn = event.GetEventObject()
        pos = self.ScreenToClient(btn.ClientToScreen((0, btn.GetSize().y)))
        self.PopupMenu(menu, pos)
        menu.Destroy()

    def abrir_modal(self, dlg):
        """Abre el diálogo y, al cerrarlo, devuelve la ventana y el foco a donde estaban.

        En Windows, tras un diálogo abierto desde un menú emergente, la ventana principal
        no recuperaba el foco y había que salir y volver con Alt+Tab.
        """
        foco = wx.Window.FindFocus()
        try:
            return dlg.ShowModal()
        finally:
            dlg.Destroy()
            self.recuperar_foco(foco)

    def avisar(self, mensaje, titulo, estilo):
        """Muestra un aviso y devuelve el foco adonde estaba.

        Sin la ventana como padre, al cerrar el aviso Windows no devolvía el foco a la
        lista y había que salir y volver con Alt+Tab.
        """
        foco = wx.Window.FindFocus()
        wx.MessageBox(mensaje, titulo, estilo, self)
        self.recuperar_foco(foco)

    def recuperar_foco(self, foco=None):
        self.Raise()
        if foco and foco.GetTopLevelParent() is self and foco.IsShownOnScreen():
            foco.SetFocus()
        elif self.list_panel.IsShown() and self.list_ctrl.GetItemCount() > 0:
            self.list_ctrl.SetFocus()
        elif self.start_panel.IsShown():
            self.start_panel.SetFocus()

    def on_about(self, event):
        self.abrir_modal(DialogoAcercaDe(self))

    def mostrar_ayuda(self, event):
        self.abrir_modal(DialogoAyuda(self))

    def mostrar_dialogo_ia(self, event):
        self.abrir_modal(DialogoIA(self))

    def anadir_imagenes(self, rutas):
        # La lista se monta una sola vez al final: montarla por cada foto leía los
        # metadatos de todas las anteriores otra vez (cuadrático con carpetas grandes).
        nuevas = []
        for ruta in rutas:
            if ruta not in self.imagenes:
                self.imagenes.append(ruta)
                nuevas.append(ruta)
        sin_lugar = []
        for ruta in nuevas:
            datos = metadatos.leer_metadatos(ruta)
            if datos.gps and not datos.lugar:
                sin_lugar.append(ruta)
        if sin_lugar:
            if self.buscador is None:
                self.buscador = self.crear_buscador()
            self.buscador.anadir(sin_lugar)
        self.refrescar_lista()

    def crear_buscador(self):
        ruta_cache = os.path.join(wx.StandardPaths.Get().GetUserDataDir(), "lugares.json")
        return BuscadorLugares(CacheLugares(ruta_cache), Nominatim(), self.al_encontrar_lugar,
                               wx.CallAfter)

    def al_encontrar_lugar(self, ruta, lugar):
        """Actualiza solo la celda de Ubicación, sin rehacer la lista ni mover el foco."""
        if ruta not in self.imagenes:
            return
        fila = self.imagenes.index(ruta)
        if lugar:
            texto = lugares.texto(lugar)
        else:
            texto = columnas.ubicacion_legible(metadatos.leer_metadatos(ruta).gps)
        self.list_ctrl.SetItem(fila, columnas.COLUMNAS.index("Ubicación"), texto)

    def cambiar_ruta(self, ruta_vieja, ruta_nueva):
        """Tras renombrar un archivo, actualiza su ruta en la lista."""
        if ruta_vieja in self.imagenes:
            self.imagenes[self.imagenes.index(ruta_vieja)] = ruta_nueva

    def refrescar_lista(self):
        seleccionada = self.list_ctrl.GetFirstSelected()
        self.list_ctrl.DeleteAllItems()
        for ruta in self.imagenes:
            buscando = bool(self.buscador) and ruta in self.buscador.pendientes
            valores = columnas.valores_fila(os.path.basename(ruta), metadatos.leer_metadatos(ruta),
                                            buscando)
            fila = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), valores[0])
            for indice, valor in enumerate(valores[1:], start=1):
                self.list_ctrl.SetItem(fila, indice, valor)
        if self.list_ctrl.GetItemCount() == 0:
            return
        if seleccionada == -1 or seleccionada >= self.list_ctrl.GetItemCount():
            seleccionada = 0
        self.enfocar_fila(seleccionada)

    def mostrar_listado(self):
        self.start_panel.Hide()
        self.list_panel.Show()
        self.Layout()
        if self.list_ctrl.GetItemCount() > 0:
            self.list_ctrl.SetFocus()

    def on_back(self, event):
        self.list_panel.Hide()
        self.start_panel.Show()
        self.Layout()
        self.start_panel.SetFocus()

    def on_list_item_selected(self, event):
        fila = event.GetIndex()
        if 0 <= fila < len(self.imagenes):
            self.actualizar_vista_previa(self.imagenes[fila])

    def actualizar_vista_previa(self, ruta):
        try:
            img = wx.Image(ruta, wx.BITMAP_TYPE_ANY)
            img = img.Scale(300, 300, wx.IMAGE_QUALITY_HIGH)
            self.preview_bitmap.SetBitmap(img.ConvertToBitmap())
            self.panel_preview.Layout()
        except Exception as e:
            self.avisar("Error al cargar la vista previa: " + str(e), "Error", wx.OK | wx.ICON_ERROR)

    def imagen_seleccionada(self):
        """(ruta, fila) de la foto seleccionada, o None.

        Las filas de la lista van en el mismo orden que self.imagenes, así que se usa
        la posición: buscar por nombre confundía fotos con el mismo nombre en
        carpetas distintas.
        """
        fila = self.list_ctrl.GetFirstSelected()
        if 0 <= fila < len(self.imagenes):
            return self.imagenes[fila], fila
        return None

    def on_edit(self, event):
        seleccion = self.imagen_seleccionada()
        if not seleccion:
            self.avisar("Selecciona una imagen para editar.", "Error", wx.OK | wx.ICON_ERROR)
            return
        if self.abrir_modal(DialogoEditar(self, seleccion[0])) == wx.ID_OK:
            self.refrescar_lista()

    def on_auto_desc(self, event):
        seleccion = self.imagen_seleccionada()
        if not seleccion:
            self.avisar("Selecciona una imagen para obtener descripción.", "Error", wx.OK | wx.ICON_ERROR)
            return
        ruta, fila = seleccion
        nombre = os.path.basename(ruta)
        # Se comprueba antes de llamar a la IA para no gastar una petición en vano.
        with open(ruta, "rb") as f:
            if not metadatos.es_jpeg(f.read(2)):
                self.avisar(str(metadatos.FormatoNoSoportado()), "Error", wx.OK | wx.ICON_ERROR)
                return
        ajustes = configuracion.leer_ajustes()
        clave = claves.leer(ajustes.id_proveedor)
        lugar = metadatos.leer_metadatos(ruta).lugar
        texto_lugar = lugares.texto(lugar) if lugar else ""
        try:
            descripcion = ejecutar_con_progreso(
                self, f"Describiendo {nombre}",
                lambda: servicio.describir_foto(ajustes, clave, ruta, texto_lugar))
        except Cancelado:
            self.enfocar_fila(fila)
            return
        except ErrorIA as e:
            self.avisar(servicio.texto_error(e, ajustes), "Error", wx.OK | wx.ICON_ERROR)
            self.enfocar_fila(fila)
            return
        try:
            metadatos.guardar_cambios(ruta, metadatos.Cambios(descripcion=descripcion))
        except Exception as e:
            self.avisar("No se pudo guardar la descripción: " + str(e), "Error", wx.OK | wx.ICON_ERROR)
            return
        self.refrescar_lista()
        self.avisar(f"Descripción guardada, {nombre}", "Confirmación", wx.OK | wx.ICON_INFORMATION)
        self.enfocar_fila(fila)

    def enfocar_fila(self, fila):
        estado = wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED
        self.list_ctrl.SetItemState(fila, estado, estado)
        self.list_ctrl.EnsureVisible(fila)
        # Con la pantalla de inicio delante la lista está oculta: pedirle el foco
        # falla en Windows ("'SetFocus' failed ... El parámetro no es correcto").
        if self.list_ctrl.IsShownOnScreen():
            self.list_ctrl.SetFocus()

    def on_list_item_activated(self, event):
        self.mostrar_menu_contextual()

    def on_list_key_down(self, event):
        tecla = event.GetKeyCode()
        modificadores = event.GetModifiers()
        if tecla == wx.WXK_RETURN:
            self.mostrar_menu_contextual()
        elif tecla in (wx.WXK_LEFT, wx.WXK_RIGHT) and modificadores == wx.MOD_NONE:
            self.mover_columna(-1 if tecla == wx.WXK_LEFT else 1)
        elif (modificadores == wx.MOD_CONTROL
              and ord("1") <= tecla < ord("1") + len(columnas.COLUMNAS)):
            self.leer_columna(tecla - ord("1"))
        else:
            event.Skip()

    def mover_columna(self, paso):
        self.columna, en_extremo = columnas.mover(self.columna, paso)
        if en_extremo:
            wx.Bell()
            return
        self.leer_columna(self.columna)

    def leer_columna(self, columna):
        fila = self.list_ctrl.GetFirstSelected()
        if fila == -1:
            return
        self.columna = columna
        voz.anunciar(columnas.anuncio(columna, self.list_ctrl.GetItemText(fila, columna)))

    def mostrar_menu_contextual(self):
        seleccion = self.imagen_seleccionada()
        if not seleccion:
            return
        menu = wx.Menu()
        id_edit = wx.NewIdRef()
        id_desc = wx.NewIdRef()
        menu.Append(id_edit, "Editar\tAlt+E")
        menu.Append(id_desc, "Obtener Descripción\tAlt+O")
        self.Bind(wx.EVT_MENU, self.on_edit, id=id_edit)
        self.Bind(wx.EVT_MENU, self.on_auto_desc, id=id_desc)
        rect = self.list_ctrl.GetItemRect(seleccion[1], wx.LIST_RECT_BOUNDS)
        self.list_ctrl.PopupMenu(menu, (rect.x, rect.y))
        menu.Destroy()
