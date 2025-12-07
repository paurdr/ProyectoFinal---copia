from dash import Input, Output, html, dcc  # y DatePickerRange, etc. si los usas
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  # solo si lo necesitas

from dash import callback
from utils.data_utils import df_from_store


@callback(
    Output("buscador-categoria", "options"),
    Output("buscador-institucion", "options"),
    Input("Data", "data")
)
def cargar_filtros_buscador(data_json):
    df = df_from_store(data_json)

    if df is None:
        return [], []

    # CATEGORÍAS
    if "Category" in df.columns:
        categorias = sorted(df["Category"].dropna().astype(str).unique())
        opciones_categorias = [{"label": c, "value": c} for c in categorias]
    else:
        opciones_categorias = []

    # INSTITUCIONES
    if "Institution" in df.columns:
        instituciones = sorted(df["Institution"].dropna().astype(str).unique())
        opciones_instituciones = [{"label": i, "value": i} for i in instituciones]
    else:
        opciones_instituciones = []

    return opciones_categorias, opciones_instituciones


@callback(
    Output("resultados-buscador", "children"),
    Input("Data", "data"),
    Input("buscador-descripcion", "value"),
    Input("buscador-categoria", "value"),
    Input("buscador-institucion", "value"),
    Input("buscador-fechas", "start_date"),
    Input("buscador-fechas", "end_date"),
    Input("monto-min", "value"),
    Input("monto-max", "value")
)
def aplicar_buscador(data_json, texto, categoria, institucion, fecha_ini, fecha_fin, monto_min, monto_max):
    df = df_from_store(data_json)

    if df is None:
        return html.P("Sube un archivo para usar el buscador.")

    # FECHA
    df["Date"] = pd.to_datetime(df["Date"])

    # FILTRO 1: TEXTO EN DESCRIPCIÓN
    if texto:
        df = df[df["Description"].str.contains(texto, case=False, na=False)]

    # FILTRO 2: CATEGORÍA
    if categoria:
        df = df[df["Category"].astype(str) == str(categoria)]

    # FILTRO 3: INSTITUCIÓN
    if institucion:
        df = df[df["Institution"].astype(str) == str(institucion)]

    # FILTRO 4: RANGO DE FECHAS
    if fecha_ini:
        df = df[df["Date"] >= fecha_ini]
    if fecha_fin:
        df = df[df["Date"] <= fecha_fin]

    # FILTRO 5: MONTO
    if monto_min is not None:
        df = df[df["Amount"] >= monto_min]

    if monto_max is not None:
        df = df[df["Amount"] <= monto_max]

    if df.empty:
        return html.P("No se encontraron resultados con esos filtros.")

    # ---- TABLA RESULTADOS ----
    tabla = html.Table(
        [html.Tr([html.Th(col) for col in df.columns])] +
        [
            html.Tr([html.Td(str(df.iloc[i][col])) for col in df.columns])
            for i in range(len(df))
        ],
        style={"width": "90%", "margin": "auto", "borderCollapse": "collapse"}
    )

    return tabla