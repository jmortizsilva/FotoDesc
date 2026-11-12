import os

import wx

from interfaz.configuracion import CONFIG_APP
from logica import metadatos


class DialogoAcercaDe(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Acerca de", size=(500, 400))
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        texto = (
            "Versión: 1.0\n\n"
            "Soy una persona, que a pesar de a penas tener resto visual, le gusta la fotografía y guardar recuerdos de los viajes.\n\n"
            "De esto surgió una conversación con mi amigo Ramón Corominas que gracias a sus muchos conocimientos, entre otras cosas en Python, me preparó una mini app para que desde el menú de aplicaciones, al estar situado encima de un archivo JPG, pudiera añadirle una descripción que se guarda directamente en la imagen.\n\n"
            "Si esta imagen se comparte mediante correo electrónico o de cualquier otra forma que no sea Whatsapp (Telegram no lo se porque no es accesible para ciegos al menos en iOS y no lo he probado), esta descripción se mantiene, con lo que es posible tener tus fotos en tu dispositivo móvil descritas.\n\n"
            "Se que en iOS existe una manera para añadirle descripción a las imágenes, pero es bastante engorrosa y está muy escondida.\n\n"
            "Basándome en esta idea de mi amigo Ramón y con la ayuda de Chat GPT y alguna otra persona por ahí, he conseguido realizar esta aplicación que permite ya no solo la edición de la descripción, si no la edición de la geolocalización mediante los datos de latitud y longitud, además de obtener una descripción automática utilizando la API de Open AI.\n\n"
            "Gracias, Ramón y al resto de personas que han contribuido en que esto sea funcional y sirva."
        )
        self.about_ctrl = wx.TextCtrl(panel, value=texto, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.about_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        btn = wx.Button(panel, label="Aceptar")
        vbox.Add(btn, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        btn.Bind(wx.EVT_BUTTON, self.on_ok)
        self.Centre()

    def on_ok(self, event):
        self.EndModal(wx.ID_OK)


class DialogoAyuda(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Ayuda", size=(500, 450))
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        texto = (
            "Bienvenido a FotoDesc.\n\n"
            "Esta aplicación permite administrar imágenes y editar sus metadatos.\n\n"
            "Pantalla de inicio:\n"
            "  • Añadir imagen (Alt+I): Selecciona una imagen individual.\n"
            "  • Añadir carpeta (Alt+C): Selecciona una carpeta con imágenes.\n"
            "  • Configuración (Alt+F): Accede al menú de configuración.\n\n"
            "Pantalla de listado:\n"
            "  • Atrás (Alt+A): Vuelve a la pantalla de inicio.\n"
            "  • Editar (Alt+E): Abre la ventana para editar la imagen seleccionada.\n"
            "  • Obtener dirección (Alt+D): Obtiene la dirección basada en la geolocalización.\n"
            "  • Obtener descripción (Alt+O): Obtiene la descripción automática mediante la API.\n"
            "  • Al pulsar Enter sobre una imagen se despliega un menú contextual con estas opciones.\n\n"
            "Cuando se añade una carpeta y ya hay imágenes cargadas, se le preguntará:\n"
            "  ¿Desea añadir las nuevas imágenes a la lista actual o reemplazarla?\n"
            "\nGracias por usar FotoDesc."
        )
        self.help_ctrl = wx.TextCtrl(panel, value=texto, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.help_ctrl, 1, wx.EXPAND | wx.ALL, 10)

        self.chk_show = wx.CheckBox(panel, label="Mostrar esta ayuda al iniciar")
        self.chk_show.SetValue(True)
        vbox.Add(self.chk_show, 0, wx.ALL, 10)

        btn = wx.Button(panel, label="Aceptar")
        vbox.Add(btn, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        btn.Bind(wx.EVT_BUTTON, self.on_ok)
        self.Centre()

    def on_ok(self, event):
        wx.Config(CONFIG_APP).WriteBool("ShowHelpOnStartup", self.chk_show.GetValue())
        self.EndModal(wx.ID_OK)


class DialogoEditar(wx.Dialog):
    def __init__(self, parent, ruta):
        super().__init__(parent, title="Editar Imagen", size=(500, 600))
        self.parent = parent
        self.ruta = ruta
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Vista previa (no enfocada para el lector)
        self.preview_bitmap = wx.StaticBitmap(panel, wx.ID_ANY, wx.NullBitmap)
        sizer.Add(self.preview_bitmap, 0, wx.ALL | wx.CENTER, 10)
        self.actualizar_vista_previa()

        datos = metadatos.leer_metadatos(ruta)
        direccion = parent.direcciones.get(ruta, "")
        latitud = str(datos.gps[0]) if datos.gps else ""
        longitud = str(datos.gps[1]) if datos.gps else ""

        self.txt_nombre = self.crear_campo(panel, sizer, "Nombre:", os.path.basename(ruta))
        self.txt_fecha = self.crear_campo(panel, sizer, "Fecha (DD/MM/AAAA):", datos.fecha)
        self.txt_hora = self.crear_campo(panel, sizer, "Hora (HH:MM:SS):", datos.hora)
        self.txt_desc = self.crear_campo(panel, sizer, "Descripción:", datos.descripcion, style=wx.TE_MULTILINE)
        self.txt_lat = self.crear_campo(panel, sizer, "Latitud:", latitud)
        self.txt_lon = self.crear_campo(panel, sizer, "Longitud:", longitud)
        self.txt_dir = self.crear_campo(panel, sizer, "Dirección:", direccion)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_guardar = wx.Button(panel, label="Guardar")
        btn_cancelar = wx.Button(panel, label="Cancelar")
        btn_sizer.Add(btn_guardar, 0, wx.ALL, 5)
        btn_sizer.Add(btn_cancelar, 0, wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)

        panel.SetSizer(sizer)
        btn_guardar.Bind(wx.EVT_BUTTON, self.on_guardar)
        btn_cancelar.Bind(wx.EVT_BUTTON, self.on_cancelar)

    def crear_campo(self, panel, sizer, etiqueta, valor, style=wx.TE_LEFT):
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.StaticText(panel, label=etiqueta), 0, wx.ALL | wx.CENTER, 5)
        txt = wx.TextCtrl(panel, value=valor, style=style)
        hsizer.Add(txt, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(hsizer, 0, wx.EXPAND)
        return txt

    def actualizar_vista_previa(self):
        try:
            img = wx.Image(self.ruta, wx.BITMAP_TYPE_ANY)
            img = img.Scale(200, 200, wx.IMAGE_QUALITY_HIGH)
            self.preview_bitmap.SetBitmap(img.ConvertToBitmap())
        except Exception as e:
            wx.MessageBox("Error al cargar la vista previa: " + str(e), "Error", wx.OK | wx.ICON_ERROR)

    def on_guardar(self, event):
        nuevo_nombre = self.txt_nombre.GetValue().strip()
        try:
            nombre_actual = os.path.basename(self.ruta)
            if nuevo_nombre and nuevo_nombre != nombre_actual:
                nueva_ruta = os.path.join(os.path.dirname(self.ruta), nuevo_nombre)
                os.rename(self.ruta, nueva_ruta)
                self.parent.cambiar_ruta(self.ruta, nueva_ruta)
                self.ruta = nueva_ruta

            exif = metadatos.leer_exif(self.ruta)
            metadatos.poner_descripcion(exif, self.txt_desc.GetValue().strip())
            metadatos.poner_fecha(exif, self.txt_fecha.GetValue().strip(), self.txt_hora.GetValue().strip())
            latitud = metadatos.leer_coordenada(self.txt_lat.GetValue())
            longitud = metadatos.leer_coordenada(self.txt_lon.GetValue())
            if latitud is not None and longitud is not None:
                metadatos.poner_gps(exif, latitud, longitud)
            metadatos.guardar_exif(self.ruta, exif)

            self.parent.direcciones[self.ruta] = self.txt_dir.GetValue().strip()
            wx.MessageBox("Datos de la foto editados correctamente", "Confirmación", wx.OK | wx.ICON_INFORMATION)
            self.EndModal(wx.ID_OK)
        except Exception as e:
            wx.MessageBox("Error al guardar los cambios: " + str(e), "Error", wx.OK | wx.ICON_ERROR)

    def on_cancelar(self, event):
        self.EndModal(wx.ID_CANCEL)
