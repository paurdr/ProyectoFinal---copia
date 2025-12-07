from dash import Input, Output, html, dcc  # y DatePickerRange, etc. si los usas
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  # solo si lo necesitas

from dash import callback
from utils.data_utils import df_from_store


@callback(
    Output("mapa-output", "children"),
    Input("Data", "data"),
    Input("mapa-metrica", "value")
)
def actualizar_mapa(data_json, metrica):
    df = df_from_store(data_json)
    if df is None:
        return html.P("Sube un archivo para ver el mapa.")

    # Asegurar columna de fecha
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    # Normalizamos nombre país por seguridad
    df["Country"] = df["Country"].astype(str)

    # === Cálculo según métrica ===
    if metrica == "gastos":
        df_filtrado = df[df["Amount"] < 0]
        resumen = df_filtrado.groupby("Country")["Amount"].sum().abs()
        titulo = "Gastos totales por país (€)"
    elif metrica == "ingresos":
        df_filtrado = df[df["Amount"] > 0]
        resumen = df_filtrado.groupby("Country")["Amount"].sum()
        titulo = "Ingresos totales por país (€)"
    else:
        resumen = df.groupby("Country")["Amount"].sum()
        titulo = "Balance total por país (€)"

    # Convertir a DataFrame para px.choropleth
    mapa_df = resumen.reset_index()
    mapa_df.columns = ["Country", "Value"]

    # === Crear el mapa ===
    fig = px.choropleth(
        mapa_df,
        locations="Country",
        locationmode="country names",
        color="Value",
        color_continuous_scale="RdYlGn",
        title=titulo,
    )

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 50, "b": 0},
        height=600
    )

    return dcc.Graph(figure=fig)