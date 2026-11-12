import io

from PIL import Image

from ia.imagen import preparar_jpeg


def abrir(datos):
    return Image.open(io.BytesIO(datos))


def prueba_reduce_y_mantiene_proporcion():
    resultado = abrir(preparar_jpeg(Image.new("RGB", (4000, 3000)), lado_maximo=1000))
    assert resultado.format == "JPEG"
    assert resultado.size == (1000, 750)


def prueba_no_amplia_las_pequenas():
    assert abrir(preparar_jpeg(Image.new("RGB", (300, 200)))).size == (300, 200)


def prueba_png_transparente_sale_jpeg_con_fondo_blanco():
    imagen = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
    resultado = abrir(preparar_jpeg(imagen))
    assert resultado.mode == "RGB"
    assert resultado.getpixel((5, 5)) == (255, 255, 255)


def prueba_gira_segun_orientacion_exif():
    imagen = Image.new("RGB", (40, 20))
    exif = imagen.getexif()
    exif[0x0112] = 6  # Girada 90 grados: la foto real es vertical
    datos = io.BytesIO()
    imagen.save(datos, "jpeg", exif=exif.tobytes())
    assert abrir(preparar_jpeg(abrir(datos.getvalue()))).size == (20, 40)
