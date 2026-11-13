"""Prototipo: cuatro formas de mostrar la lista de fotos, para probarlas con lectores.

Uso, desde la carpeta del proyecto:
    python -m prototipos.tablas                  (fotos de ejemplo)
    python -m prototipos.tablas C:\\ruta\\carpeta  (fotos de esa carpeta)

Ctrl+Tab cambia de pestaña. No modifica ninguna foto.
"""
import os
import sys

import wx
import wx.dataview as dv
import wx.grid

from logica import metadatos

COLUMNAS = ["Nombre", "Descripción", "Fecha", "Hora", "Ubicación", "Dirección"]

EJEMPLO = [
    ["IMG_0101.jpg", "Barranco del río Tajo con niebla entre los pinos.", "16/04/2022", "10:05:30",
     "40.812345, -2.103456", "Peralejos de las Truchas, Guadalajara"],
    ["IMG_0102.jpg", "Dos personas sentadas en una roca junto al río.", "16/04/2022", "10:42:11",
     "40.813001, -2.101002", "Peralejos de las Truchas, Guadalajara"],
    ["IMG_0150.jpg", "Plato de migas con uvas en una mesa de madera.", "17/04/2022", "14:20:00", "", ""],
    ["captura.png", "", "", "", "", ""],
]


def filas_de_carpeta(carpeta):
    filas = []
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.lower().endswith((".jpg", ".jpeg", ".png", ".heic", ".heif")):
            continue
        datos = metadatos.leer_metadatos(os.path.join(carpeta, nombre))
        ubicacion = f"{datos.gps[0]:.6f}, {datos.gps[1]:.6f}" if datos.gps else ""
        filas.append([nombre, datos.descripcion, datos.fecha, datos.hora, ubicacion, ""])
    return filas


def pagina(cuaderno, titulo):
    panel = wx.Panel(cuaderno)
    caja = wx.BoxSizer(wx.VERTICAL)
    panel.SetSizer(caja)
    cuaderno.AddPage(panel, titulo)
    # La etiqueta va justo antes del control para que los lectores la asocien.
    caja.Add(wx.StaticText(panel, label="Fotos:"), 0, wx.ALL, 5)
    return panel, caja


def lista_actual(cuaderno, filas):
    panel, caja = pagina(cuaderno, "1 Lista actual")
    lista = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
    for i, columna in enumerate(COLUMNAS):
        lista.InsertColumn(i, columna, width=160)
    for fila in filas:
        indice = lista.InsertItem(lista.GetItemCount(), fila[0])
        for i, valor in enumerate(fila[1:], start=1):
            lista.SetItem(indice, i, valor)
    caja.Add(lista, 1, wx.EXPAND | wx.ALL, 5)
    return lista


def vista_de_datos(cuaderno, filas):
    panel, caja = pagina(cuaderno, "2 Vista de datos")
    vista = dv.DataViewListCtrl(panel, style=dv.DV_ROW_LINES | dv.DV_SINGLE)
    for columna in COLUMNAS:
        vista.AppendTextColumn(columna, width=160)
    for fila in filas:
        vista.AppendItem(fila)
    caja.Add(vista, 1, wx.EXPAND | wx.ALL, 5)
    return vista


def cuadricula(cuaderno, filas):
    panel, caja = pagina(cuaderno, "3 Cuadrícula")
    rejilla = wx.grid.Grid(panel)
    rejilla.CreateGrid(len(filas), len(COLUMNAS))
    rejilla.EnableEditing(False)
    # Con Tab se sale de la cuadrícula en vez de saltar de celda en celda.
    rejilla.SetTabBehaviour(wx.grid.Grid.Tab_Leave)
    for i, columna in enumerate(COLUMNAS):
        rejilla.SetColLabelValue(i, columna)
    for f, fila in enumerate(filas):
        for c, valor in enumerate(fila):
            rejilla.SetCellValue(f, c, valor)
    rejilla.AutoSizeColumns()
    caja.Add(rejilla, 1, wx.EXPAND | wx.ALL, 5)
    return rejilla


def lista_con_detalles(cuaderno, filas):
    panel, caja = pagina(cuaderno, "4 Lista con detalles")
    lista = wx.ListCtrl(panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
    lista.InsertColumn(0, "Nombre", width=200)
    lista.InsertColumn(1, "Descripción", width=400)
    for fila in filas:
        indice = lista.InsertItem(lista.GetItemCount(), fila[0])
        lista.SetItem(indice, 1, fila[1])
    caja.Add(lista, 1, wx.EXPAND | wx.ALL, 5)

    caja.Add(wx.StaticText(panel, label="Datos de la foto:"), 0, wx.ALL, 5)
    detalles = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 140))
    caja.Add(detalles, 0, wx.EXPAND | wx.ALL, 5)

    def mostrar(event):
        fila = filas[event.GetIndex()]
        detalles.SetValue("\n".join(f"{c}: {v or 'sin datos'}" for c, v in zip(COLUMNAS, fila)))

    lista.Bind(wx.EVT_LIST_ITEM_SELECTED, mostrar)
    if filas:
        lista.Select(0)
    return lista


def main():
    filas = filas_de_carpeta(sys.argv[1]) if len(sys.argv) > 1 else EJEMPLO
    app = wx.App(False)
    ventana = wx.Frame(None, title="Prototipo de tablas, FotoDesc", size=(1000, 600))
    cuaderno = wx.Notebook(ventana)
    primera = lista_actual(cuaderno, filas)
    vista_de_datos(cuaderno, filas)
    cuadricula(cuaderno, filas)
    lista_con_detalles(cuaderno, filas)
    ventana.Show()
    primera.SetFocus()
    app.MainLoop()


if __name__ == "__main__":
    main()
