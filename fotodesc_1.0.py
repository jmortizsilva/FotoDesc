import wx
import os
import piexif
import requests
from PIL import Image
import urllib.request
import urllib.error
import json
import base64
import mimetypes

# Registrar el opener para HEIF/HEIC si pillow-heif está instalado
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

# ---------------- Clase para panel no accesible para tabulación ----------------
class NonFocusablePanel(wx.Panel):
    def AcceptsFocus(self):
        return False

# ---------------- Diálogo "Acerca de" ----------------
class AboutDialog(wx.Dialog):
    def __init__(self, parent):
        super(AboutDialog, self).__init__(parent, title="Acerca de", size=(500,400))
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        about_text = (
            "Versión: 1.0\n\n"
            "Soy una persona, que a pesar de a penas tener resto visual, le gusta la fotografía y guardar recuerdos de los viajes.\n\n"
            "De esto surgió una conversación con mi amigo Ramón Corominas que gracias a sus muchos conocimientos, entre otras cosas en Python, me preparó una mini app para que desde el menú de aplicaciones, al estar situado encima de un archivo JPG, pudiera añadirle una descripción que se guarda directamente en la imagen.\n\n"
            "Si esta imagen se comparte mediante correo electrónico o de cualquier otra forma que no sea Whatsapp (Telegram no lo se porque no es accesible para ciegos al menos en iOS y no lo he probado), esta descripción se mantiene, con lo que es posible tener tus fotos en tu dispositivo móvil descritas.\n\n"
            "Se que en iOS existe una manera para añadirle descripción a las imágenes, pero es bastante engorrosa y está muy escondida.\n\n"
            "Basándome en esta idea de mi amigo Ramón y con la ayuda de Chat GPT y alguna otra persona por ahí, he conseguido realizar esta aplicación que permite ya no solo la edición de la descripción, si no la edición de la geolocalización mediante los datos de latitud y longitud, además de obtener una descripción automática utilizando la API de Open AI.\n\n"
            "Gracias, Ramón y al resto de personas que han contribuido en que esto sea funcional y sirva."
        )
        self.about_ctrl = wx.TextCtrl(panel, value=about_text, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.about_ctrl, 1, wx.EXPAND | wx.ALL, 10)
        btn = wx.Button(panel, label="Aceptar")
        vbox.Add(btn, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        panel.SetSizer(vbox)
        btn.Bind(wx.EVT_BUTTON, self.on_ok)
        self.Centre()
    
    def on_ok(self, event):
        self.EndModal(wx.ID_OK)

# ---------------- Diálogo para introducir la API Key ----------------
class APIKeyDialog(wx.Dialog):
    """
    Diálogo para introducir la API Key de OpenAI.
    """
    def __init__(self, parent, current_api_key):
        super(APIKeyDialog, self).__init__(parent, title="Configurar API Key", size=(400,200))
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        label = wx.StaticText(panel, label="Ingrese su API Key de OpenAI:")
        vbox.Add(label, 0, wx.ALL | wx.CENTER, 10)
        
        self.txt_api_key = wx.TextCtrl(panel, value=current_api_key)
        vbox.Add(self.txt_api_key, 0, wx.EXPAND | wx.ALL, 10)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        btn_guardar = wx.Button(panel, label="Guardar")
        btn_cancelar = wx.Button(panel, label="Cancelar")
        hbox.Add(btn_guardar, 0, wx.ALL, 5)
        hbox.Add(btn_cancelar, 0, wx.ALL, 5)
        vbox.Add(hbox, 0, wx.ALIGN_CENTER)
        
        panel.SetSizer(vbox)
        
        btn_guardar.Bind(wx.EVT_BUTTON, self.on_guardar)
        btn_cancelar.Bind(wx.EVT_BUTTON, self.on_cancelar)
        
    def on_guardar(self, event):
        wx.MessageBox("API Key guardada correctamente", "Confirmación", wx.OK | wx.ICON_INFORMATION)
        self.EndModal(wx.ID_OK)
        
    def on_cancelar(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def GetAPIKey(self):
        return self.txt_api_key.GetValue()

# ---------------- Funciones Comunes ----------------
def decimal_to_dms_rational(dec):
    dec = abs(dec)
    degrees = int(dec)
    minutes = int((dec - degrees) * 60)
    seconds = (dec - degrees - minutes / 60) * 3600
    return ((degrees, 1), (minutes, 1), (int(seconds * 100), 100))

def dms_to_decimal(dms, ref):
    try:
        degrees = dms[0][0] / dms[0][1]
        minutes = dms[1][0] / dms[1][1]
        seconds = dms[2][0] / dms[2][1]
        dec = degrees + minutes / 60 + seconds / 3600
        if ref in ['S', 'W']:
            dec = -dec
        return dec
    except Exception:
        return None

def imagen_a_data_url(ruta_imagen):
    """Convierte una imagen en un Data URL en Base64."""
    with open(ruta_imagen, "rb") as f:
        contenido = f.read()
    mime_type = mimetypes.guess_type(ruta_imagen)[0] or "application/octet-stream"
    encoded = base64.b64encode(contenido).decode("utf-8")
    data_url = f"data:{mime_type};base64,{encoded}"
    return data_url

def describir_imagen(api_key, ruta_imagen, prompt, detail="high", max_tokens=300):
    """Envía una imagen y un prompt a la API de OpenAI para obtener una descripción."""
    data_url = imagen_a_data_url(ruta_imagen)
    
    payload = {
        "model": "gpt-4o-mini",  # Verifica en la documentación oficial el nombre correcto del modelo
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url, "detail": detail}}
                ]
            }
        ],
        "max_tokens": max_tokens
    }
    
    data = json.dumps(payload).encode("utf-8")
    url_api = "https://api.openai.com/v1/chat/completions"
    req = urllib.request.Request(url_api, data=data)
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + api_key)
    
    try:
        with urllib.request.urlopen(req) as response:
            respuesta = response.read().decode("utf-8")
            datos = json.loads(respuesta)
            contenido = datos.get("choices", [{}])[0].get("message", {}).get("content",
                        "No se encontró contenido en la respuesta.")
            return contenido
    except urllib.error.HTTPError as e:
        error_info = e.read().decode("utf-8")
        raise Exception("Error en la petición: {} - {}".format(e.code, error_info))
    except Exception as ex:
        raise Exception("Se produjo un error: " + str(ex))

def update_image_description(file_path, description):
    """Actualiza la descripción en el EXIF de la imagen."""
    try:
        img = Image.open(file_path)
        if "exif" in img.info:
            exif_dict = piexif.load(img.info["exif"])
        else:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = description.encode("utf-8")
        exif_bytes = piexif.dump(exif_dict)
        img.save(file_path, "jpeg", exif=exif_bytes)
    except Exception as e:
        raise Exception("Error al actualizar la descripción: " + str(e))

def get_metadata(file_path):
    """
    Extrae metadatos de la imagen: descripción, geolocalización, fecha y hora.
    Retorna una tupla: (descripción, (lat, lon) o None, fecha, hora).
    Se extrae la fecha desde DateTimeOriginal (formato "YYYY:MM:DD HH:MM:SS") y se convierte a "DD/MM/AAAA".
    """
    try:
        img = Image.open(file_path)
        if "exif" in img.info:
            exif_dict = piexif.load(img.info["exif"])
        else:
            exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
        desc = exif_dict["0th"].get(piexif.ImageIFD.ImageDescription, b"").decode("utf-8", errors="ignore")
        if not desc:
            desc = ""
        gps = None
        if piexif.GPSIFD.GPSLatitude in exif_dict.get("GPS", {}):
            lat_tuple = exif_dict["GPS"].get(piexif.GPSIFD.GPSLatitude)
            lat_ref = exif_dict["GPS"].get(piexif.GPSIFD.GPSLatitudeRef, b'N').decode("utf-8")
            lon_tuple = exif_dict["GPS"].get(piexif.GPSIFD.GPSLongitude)
            lon_ref = exif_dict["GPS"].get(piexif.GPSIFD.GPSLongitudeRef, b'E').decode("utf-8")
            if lat_tuple and lon_tuple:
                lat = dms_to_decimal(lat_tuple, lat_ref)
                lon = dms_to_decimal(lon_tuple, lon_ref)
                gps = (lat, lon)
        fecha = ""
        hora = ""
        if "Exif" in exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
            dt_str = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode("utf-8")
            parts = dt_str.split(" ")
            if len(parts) == 2:
                y, m, d = parts[0].split(":")
                fecha = f"{d}/{m}/{y}"
                hora = parts[1]
        return desc, gps, fecha, hora
    except Exception:
        return "", None, "", ""

# ---------------- Ventana de Ayuda (con casilla de verificación) ----------------
class HelpDialog(wx.Dialog):
    def __init__(self, parent):
        super(HelpDialog, self).__init__(parent, title="Ayuda", size=(500,450))
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        help_text = (
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
        self.help_ctrl = wx.TextCtrl(panel, value=help_text, style=wx.TE_MULTILINE | wx.TE_READONLY)
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
        config = wx.Config("FotodescApp")
        config.WriteBool("ShowHelpOnStartup", self.chk_show.GetValue())
        self.EndModal(wx.ID_OK)

# ---------------- Ventana de Edición ----------------
class EditDialog(wx.Dialog):
    def __init__(self, parent, file_path):
        super(EditDialog, self).__init__(parent, title="Editar Imagen", size=(500,600))
        self.parent = parent
        self.file_path = file_path
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Vista previa (no enfocada para el lector)
        self.preview_bitmap = wx.StaticBitmap(panel, wx.ID_ANY, wx.NullBitmap)
        sizer.Add(self.preview_bitmap, 0, wx.ALL | wx.CENTER, 10)
        self.update_preview()
        
        # Obtener metadatos
        desc, gps, fecha, hora = get_metadata(file_path)
        direccion = parent.addresses.get(file_path, "")
        nombre = os.path.basename(file_path)
        latitud = str(gps[0]) if gps else ""
        longitud = str(gps[1]) if gps else ""
        
        self.txt_nombre = self.create_field(panel, sizer, "Nombre:", nombre)
        self.txt_fecha = self.create_field(panel, sizer, "Fecha (DD/MM/AAAA):", fecha)
        self.txt_hora = self.create_field(panel, sizer, "Hora (HH:MM:SS):", hora)
        self.txt_desc = self.create_field(panel, sizer, "Descripción:", desc, style=wx.TE_MULTILINE)
        self.txt_lat = self.create_field(panel, sizer, "Latitud:", latitud)
        self.txt_lon = self.create_field(panel, sizer, "Longitud:", longitud)
        self.txt_dir = self.create_field(panel, sizer, "Dirección:", direccion)
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_guardar = wx.Button(panel, label="Guardar")
        btn_cancelar = wx.Button(panel, label="Cancelar")
        btn_sizer.Add(btn_guardar, 0, wx.ALL, 5)
        btn_sizer.Add(btn_cancelar, 0, wx.ALL, 5)
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)
        
        panel.SetSizer(sizer)
        btn_guardar.Bind(wx.EVT_BUTTON, self.on_guardar)
        btn_cancelar.Bind(wx.EVT_BUTTON, self.on_cancelar)
        
    def create_field(self, panel, sizer, label_text, default_value, style=wx.TE_LEFT):
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(panel, label=label_text)
        hsizer.Add(label, 0, wx.ALL | wx.CENTER, 5)
        txt = wx.TextCtrl(panel, value=default_value, style=style)
        hsizer.Add(txt, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(hsizer, 0, wx.EXPAND)
        return txt
        
    def update_preview(self):
        try:
            img = wx.Image(self.file_path, wx.BITMAP_TYPE_ANY)
            img = img.Scale(200, 200, wx.IMAGE_QUALITY_HIGH)
            bmp = img.ConvertToBitmap()
            self.preview_bitmap.SetBitmap(bmp)
        except Exception as e:
            wx.MessageBox("Error al cargar la vista previa: " + str(e), "Error", wx.OK | wx.ICON_ERROR)
        
    def on_guardar(self, event):
        new_nombre = self.txt_nombre.GetValue().strip()
        new_fecha = self.txt_fecha.GetValue().strip()
        new_hora = self.txt_hora.GetValue().strip()
        new_desc = self.txt_desc.GetValue().strip()
        new_lat = self.txt_lat.GetValue().strip()
        new_lon = self.txt_lon.GetValue().strip()
        new_dir = self.txt_dir.GetValue().strip()
        
        try:
            directorio = os.path.dirname(self.file_path)
            nombre_actual = os.path.basename(self.file_path)
            new_path = self.file_path
            if new_nombre and new_nombre != nombre_actual:
                new_path = os.path.join(directorio, new_nombre)
                os.rename(self.file_path, new_path)
                self.file_path = new_path
                for idx, f in enumerate(self.parent.images):
                    if os.path.basename(f) == nombre_actual:
                        self.parent.images[idx] = new_path
                        break
            img = Image.open(self.file_path)
            if "exif" in img.info:
                exif_dict = piexif.load(img.info["exif"])
            else:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
            exif_dict["0th"][piexif.ImageIFD.ImageDescription] = new_desc.encode("utf-8")
            if new_fecha and new_hora:
                parts = new_fecha.split("/")
                if len(parts) == 3:
                    dt_str = f"{parts[2]}:{parts[1]}:{parts[0]} {new_hora}"
                    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = dt_str.encode("utf-8")
            if new_lat and new_lon:
                try:
                    lat = float(new_lat.replace(',', '.'))
                    lon = float(new_lon.replace(',', '.'))
                    lat_ref = 'N' if lat >= 0 else 'S'
                    lon_ref = 'E' if lon >= 0 else 'W'
                    exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = lat_ref.encode("utf-8")
                    exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = decimal_to_dms_rational(lat)
                    exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = lon_ref.encode("utf-8")
                    exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = decimal_to_dms_rational(lon)
                except:
                    pass
            exif_bytes = piexif.dump(exif_dict)
            img.save(self.file_path, "jpeg", exif=exif_bytes)
            self.parent.addresses[self.file_path] = new_dir
            wx.MessageBox("Datos de la foto editados correctamente", "Confirmación", wx.OK | wx.ICON_INFORMATION)
            self.EndModal(wx.ID_OK)
        except Exception as e:
            wx.MessageBox("Error al guardar los cambios: " + str(e), "Error", wx.OK | wx.ICON_ERROR)
        
    def on_cancelar(self, event):
        self.EndModal(wx.ID_CANCEL)

# ---------------- Ventana Principal ----------------
class MainFrame(wx.Frame):
    def __init__(self, parent):
        # Asignamos IDs para los aceleradores
        self.id_add_image = wx.NewIdRef()
        self.id_add_folder = wx.NewIdRef()
        self.id_config = wx.NewIdRef()
        self.id_about = wx.NewIdRef()  # Acerca de en el menú
        self.id_edit = wx.NewIdRef()
        self.id_address = wx.NewIdRef()
        self.id_auto_desc = wx.NewIdRef()
        self.id_back = wx.NewIdRef()  # Atrás
        super(MainFrame, self).__init__(parent, title="FotoDesc", size=(1000,700))
        self.images = []       # Lista de rutas de imágenes
        self.addresses = {}    # Diccionario para almacenar la dirección de cada imagen
        self.api_key = ""      # Se carga desde wx.Config o se pide al usuario
        self.InitUI()
        # Establecemos atajos usando exclusivamente Alt:
        self.SetAcceleratorTable(wx.AcceleratorTable([
            (wx.ACCEL_ALT, ord('I'), self.id_add_image),  # Alt+I: Añadir imagen
            (wx.ACCEL_ALT, ord('C'), self.id_add_folder),   # Alt+C: Añadir carpeta
            (wx.ACCEL_ALT, ord('F'), self.id_config),       # Alt+F: Configuración
            (wx.ACCEL_ALT, ord('U'), self.id_about),         # Alt+U: Acerca de
            (wx.ACCEL_ALT, ord('A'), self.id_back),          # Alt+A: Atrás
            (wx.ACCEL_ALT, ord('E'), self.id_edit),          # Alt+E: Editar
            (wx.ACCEL_ALT, ord('D'), self.id_address),       # Alt+D: Obtener dirección
            (wx.ACCEL_ALT, ord('O'), self.id_auto_desc),     # Alt+O: Obtener descripción
        ]))
        # Bind global para los aceleradores
        self.Bind(wx.EVT_MENU, self.on_add_image, id=self.id_add_image)
        self.Bind(wx.EVT_MENU, self.on_add_folder, id=self.id_add_folder)
        self.Bind(wx.EVT_MENU, self.on_config, id=self.id_config)
        self.Bind(wx.EVT_MENU, self.on_about, id=self.id_about)
        self.Bind(wx.EVT_MENU, self.on_back, id=self.id_back)
        self.Bind(wx.EVT_MENU, self.on_edit, id=self.id_edit)
        self.Bind(wx.EVT_MENU, self.on_address, id=self.id_address)
        self.Bind(wx.EVT_MENU, self.on_auto_desc, id=self.id_auto_desc)
        
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
        
        # Botón Atrás
        btn_back = wx.Button(self.list_panel, label="Atrás")
        btn_back.SetToolTip("Atajo: Alt+A")
        btn_back.Bind(wx.EVT_BUTTON, self.on_back)
        list_panel_sizer.Add(btn_back, 0, wx.ALL | wx.CENTER, 5)
        
        # Etiqueta para el listado
        label_listado = wx.StaticText(self.list_panel, label="Listado de Imágenes:")
        list_panel_sizer.Add(label_listado, 0, wx.ALL, 5)
        
        # Contenedor para el splitter
        splitter_holder = wx.Panel(self.list_panel)
        splitter_holder_sizer = wx.BoxSizer(wx.VERTICAL)
        self.splitter_list = wx.SplitterWindow(splitter_holder, style=wx.SP_LIVE_UPDATE)
        
        # Panel izquierdo: listado
        panel_list = wx.Panel(self.splitter_list)
        list_sizer = wx.BoxSizer(wx.VERTICAL)
        self.list_ctrl = wx.ListCtrl(panel_list, style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.SetToolTip("Listado de imágenes")
        self.list_ctrl.InsertColumn(0, "Archivo", width=200)
        self.list_ctrl.InsertColumn(1, "Descripción", width=200)
        self.list_ctrl.InsertColumn(2, "Localización", width=150)
        self.list_ctrl.InsertColumn(3, "Dirección", width=200)
        self.list_ctrl.InsertColumn(4, "Fecha", width=100)
        self.list_ctrl.InsertColumn(5, "Hora", width=100)
        list_sizer.Add(self.list_ctrl, 1, wx.EXPAND | wx.ALL, 5)
        
        btn_panel = wx.Panel(panel_list)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_edit = wx.Button(btn_panel, label="Editar")
        self.btn_edit.SetToolTip("Atajo: Alt+E")
        self.btn_auto_desc = wx.Button(btn_panel, label="Obtener descripción")
        self.btn_auto_desc.SetToolTip("Atajo: Alt+O")
        self.btn_address = wx.Button(btn_panel, label="Obtener dirección")
        self.btn_address.SetToolTip("Atajo: Alt+D")
        self.btn_config = wx.Button(btn_panel, label="Configuración")
        self.btn_config.SetToolTip("Atajo: Alt+F")
        btn_sizer.Add(self.btn_edit, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_auto_desc, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_address, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_config, 0, wx.ALL, 5)
        btn_panel.SetSizer(btn_sizer)
        list_sizer.Add(btn_panel, 0, wx.ALIGN_CENTER)
        panel_list.SetSizer(list_sizer)
        
        # Panel derecho: vista previa
        self.panel_preview = NonFocusablePanel(self.splitter_list)
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
        self.list_panel.Hide()  # Se muestra inicialmente la pantalla de inicio
        
        self.main_panel.SetSizer(self.sizer)
        self.SetMinSize((800,600))
        self.Centre()
        
        # Bindear eventos
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_list_item_selected)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_list_item_activated)
        self.list_ctrl.Bind(wx.EVT_KEY_DOWN, self.on_list_key_down)
        self.btn_edit.Bind(wx.EVT_BUTTON, self.on_edit)
        self.btn_auto_desc.Bind(wx.EVT_BUTTON, self.on_auto_desc)
        self.btn_address.Bind(wx.EVT_BUTTON, self.on_address)
        self.btn_config.Bind(wx.EVT_BUTTON, self.on_config)
        
    def on_add_image(self, event):
        dlg = wx.FileDialog(self, "Selecciona una imagen",
                            wildcard="Archivos de imagen (*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.heif;*.heic)|*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.heif;*.heic",
                            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            file_path = dlg.GetPath()
            self.add_image(file_path)
            self.show_list_panel()
        dlg.Destroy()
        
    def on_add_folder(self, event):
        dlg = wx.DirDialog(self, "Selecciona una carpeta", defaultPath=os.path.expanduser("~"), style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK:
            folder = dlg.GetPath()
            if self.images:
                msg = ("Ya hay imágenes cargadas.\n\n"
                       "¿Desea añadir las nuevas imágenes a la lista actual o reemplazarla?")
                confirm_dlg = wx.MessageDialog(self, msg, "Agregar o Reemplazar", wx.YES_NO | wx.ICON_QUESTION)
                try:
                    confirm_dlg.SetYesNoLabels("Añadir", "Reemplazar")
                except AttributeError:
                    pass
                result = confirm_dlg.ShowModal()
                confirm_dlg.Destroy()
                if result == wx.ID_NO:
                    self.images = []
            for f in os.listdir(folder):
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.heif', '.heic')):
                    file_path = os.path.join(folder, f)
                    self.add_image(file_path)
            self.show_list_panel()
        dlg.Destroy()
        
    def on_config(self, event):
        menu = wx.Menu()
        id_help = wx.NewIdRef()
        id_api = wx.NewIdRef()
        id_about = wx.NewIdRef()
        menu.Append(id_help, "Ayuda\tF1")
        menu.Append(id_api, "Configurar API Key\tCtrl+K")
        menu.Append(id_about, "Acerca de\tAlt+U")
        self.Bind(wx.EVT_MENU, self.show_help, id=id_help)
        self.Bind(wx.EVT_MENU, self.show_api_key_dialog, id=id_api)
        self.Bind(wx.EVT_MENU, self.on_about, id=id_about)
        btn = event.GetEventObject()
        pos = btn.ClientToScreen((0, btn.GetSize().y))
        pos = self.ScreenToClient(pos)
        self.PopupMenu(menu, pos)
        menu.Destroy()
        
    def on_about(self, event):
        dlg = AboutDialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        
    def show_help(self, event):
        dlg = HelpDialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        
    def show_api_key_dialog(self, event):
        dlg = APIKeyDialog(self, self.api_key)
        if dlg.ShowModal() == wx.ID_OK:
            self.api_key = dlg.GetAPIKey()
            config = wx.Config("FotodescApp")
            config.Write("OpenAI_API_Key", self.api_key)
        dlg.Destroy()
        
    def add_image(self, file_path):
        if file_path not in self.images:
            self.images.append(file_path)
        self.refresh_list()
        
    def refresh_list(self):
        sel_index = self.list_ctrl.GetFirstSelected()
        self.list_ctrl.DeleteAllItems()
        for idx, file_path in enumerate(self.images):
            desc, gps, fecha, hora = get_metadata(file_path)
            localizacion = f"{gps[0]:.6f}, {gps[1]:.6f}" if gps else ""
            direccion = self.addresses.get(file_path, "")
            index = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), os.path.basename(file_path))
            self.list_ctrl.SetItem(index, 1, desc)
            self.list_ctrl.SetItem(index, 2, localizacion)
            self.list_ctrl.SetItem(index, 3, direccion)
            self.list_ctrl.SetItem(index, 4, fecha)
            self.list_ctrl.SetItem(index, 5, hora)
        if self.list_ctrl.GetItemCount() > 0 and sel_index == -1:
            self.list_ctrl.SetItemState(0, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
                                          wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
            self.list_ctrl.EnsureVisible(0)
            self.list_ctrl.SetFocus()
        elif sel_index != -1:
            self.list_ctrl.SetItemState(sel_index, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
                                          wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
            self.list_ctrl.EnsureVisible(sel_index)
            self.list_ctrl.SetFocus()
        
    def show_list_panel(self):
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
        index = event.GetIndex()
        if index == -1:
            return
        file_name = self.list_ctrl.GetItemText(index, 0)
        for file_path in self.images:
            if os.path.basename(file_path) == file_name:
                self.update_preview(file_path)
                break
        
    def update_preview(self, file_path):
        try:
            wx_img = wx.Image(file_path, wx.BITMAP_TYPE_ANY)
            wx_img = wx_img.Scale(300, 300, wx.IMAGE_QUALITY_HIGH)
            bmp = wx_img.ConvertToBitmap()
            self.preview_bitmap.SetBitmap(bmp)
            self.panel_preview.Layout()
        except Exception as e:
            wx.MessageBox("Error al cargar la vista previa: " + str(e), "Error", wx.OK | wx.ICON_ERROR)
        
    def get_selected_image(self):
        index = self.list_ctrl.GetFirstSelected()
        if index == -1:
            return None
        file_name = self.list_ctrl.GetItemText(index, 0)
        for file_path in self.images:
            if os.path.basename(file_path) == file_name:
                return file_path, index
        return None
        
    def on_edit(self, event):
        selected = self.get_selected_image()
        if not selected:
            wx.MessageBox("Selecciona una imagen para editar.", "Error", wx.OK | wx.ICON_ERROR)
            return
        file_path, index = selected
        dlg = EditDialog(self, file_path)
        if dlg.ShowModal() == wx.ID_OK:
            self.refresh_list()
        dlg.Destroy()
        
    def on_auto_desc(self, event):
        selected = self.get_selected_image()
        if not selected:
            wx.MessageBox("Selecciona una imagen para obtener descripción.", "Error", wx.OK | wx.ICON_ERROR)
            return
        file_path, index = selected
        prompt = "Describe la imagen de manera detallada."
        try:
            description = describir_imagen(self.api_key, file_path, prompt)
            update_image_description(file_path, description)
            self.refresh_list()
            wx.MessageBox("Descripción automática obtenida correctamente", "Confirmación", wx.OK | wx.ICON_INFORMATION)
            self.set_focus_selected(index)
        except Exception as e:
            wx.MessageBox("Error al obtener la descripción automática: " + str(e),
                          "Error", wx.OK | wx.ICON_ERROR)
        
    def on_address(self, event):
        selected = self.get_selected_image()
        if not selected:
            wx.MessageBox("Selecciona una imagen para obtener la dirección.", "Error", wx.OK | wx.ICON_ERROR)
            return
        file_path, index = selected
        desc, gps, fecha, hora = get_metadata(file_path)
        if not gps:
            wx.MessageBox("No hay datos de latitud y longitud.", "Error", wx.OK | wx.ICON_ERROR)
            return
        lat, lon = gps
        params = {"format": "json", "lat": lat, "lon": lon, "zoom": 18, "addressdetails": 1}
        headers = {"User-Agent": "wxPythonApp Fotodesc (contacto@tudominio.com)"}
        try:
            response = requests.get("https://nominatim.openstreetmap.org/reverse", params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                address = data.get("display_name", "")
                if address:
                    self.addresses[file_path] = address
                    self.refresh_list()
                    wx.MessageBox("Dirección obtenida correctamente", "Confirmación", wx.OK | wx.ICON_INFORMATION)
                    self.set_focus_selected(index)
                else:
                    wx.MessageBox("No se encontró dirección.", "Información", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("Error al obtener la dirección. Código: " + str(response.status_code),
                              "Error", wx.OK | wx.ICON_ERROR)
        except Exception as e:
            wx.MessageBox("Error en la conexión: " + str(e), "Error", wx.OK | wx.ICON_ERROR)
            
    def set_focus_selected(self, index):
        self.list_ctrl.SetItemState(index, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
                                      wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)
        self.list_ctrl.EnsureVisible(index)
        self.list_ctrl.SetFocus()
        
    def on_list_item_activated(self, event):
        self.show_popup_menu()
        
    def on_list_key_down(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.show_popup_menu()
        else:
            event.Skip()
            
    def show_popup_menu(self):
        selected = self.get_selected_image()
        if not selected:
            return
        file_path, index = selected
        menu = wx.Menu()
        id_edit = wx.NewIdRef()
        id_address = wx.NewIdRef()
        id_desc = wx.NewIdRef()
        menu.Append(id_edit, "Editar\tAlt+E")
        menu.Append(id_address, "Obtener Dirección\tAlt+D")
        menu.Append(id_desc, "Obtener Descripción\tAlt+O")
        self.Bind(wx.EVT_MENU, self.on_edit, id=id_edit)
        self.Bind(wx.EVT_MENU, self.on_address, id=id_address)
        self.Bind(wx.EVT_MENU, self.on_auto_desc, id=id_desc)
        index_selected = self.list_ctrl.GetFirstSelected()
        if index_selected != -1:
            rect = self.list_ctrl.GetItemRect(index_selected, wx.LIST_RECT_BOUNDS)
            self.list_ctrl.PopupMenu(menu, (rect.x, rect.y))
        menu.Destroy()

# ---------------- Main ----------------
if __name__ == "__main__":
    app = wx.App(False)
    config = wx.Config("FotodescApp")
    api_key = config.Read("OpenAI_API_Key", "")
    frame = MainFrame(None)
    frame.api_key = api_key
    frame.Show()
    if config.ReadBool("ShowHelpOnStartup", True):
        dlg = HelpDialog(frame)
        dlg.ShowModal()
        dlg.Destroy()
    app.MainLoop()
