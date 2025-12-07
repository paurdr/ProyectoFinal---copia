# callbacks/upload.py
from dash import Input, Output, State, html
import dash
import pandas as pd

from dash import callback
from utils.data_utils import parse_contents

@callback(
    Output("upload-status", "children"),
    Output("Data", "data"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def update_output(contents, filename):
    """
    Cuando el usuario sube un archivo, este callback:
    - lo convierte en DataFrame
    - lo guarda en Data como JSON
    - muestra un mensaje de estado
    """

    if contents is None:
        return "No hay ningún archivo cargado.", dash.no_update

    df = parse_contents(contents, filename)
    if df is None:
        return "Error al leer el archivo. Asegúrate de que es CSV o Excel.", dash.no_update

    filas = len(df)
    columnas = list(df.columns)

    rango_fechas = ""
    for col in df.columns:
        if "date" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col])
                rango_fechas = f" | Rango de fechas: {df[col].min().date()} – {df[col].max().date()}"
            except Exception:
                pass
            break

    mensaje = f"Archivo '{filename}' cargado correctamente. Filas: {filas}. Columnas: {', '.join(columnas)}{rango_fechas}"

    data_json = df.to_json(date_format="iso", orient="split")

    return mensaje, data_json
