from dash import Input, Output, html, dcc  # y DatePickerRange, etc. si los usas
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  # solo si lo necesitas

from dash import callback
from utils.data_utils import df_from_store


@callback(
    Output("grafico-mensual-linea", "children"),
    Output("grafico-mensual-barras", "children"),
    Input("Data", "data"),
    Input("filtro-institucion", "value"),
    Input("filtro-categoria", "value")
)
def actualizar_mensual(data_json, instituciones, categorias):
    df = df_from_store(data_json)

    if df is None:
        return html.P("Sube un archivo para ver el análisis mensual."), None

    # Asegurar formato fecha
    if "Date" not in df.columns:
        return html.P("No se encontró la columna 'Date'."), None

    df["Date"] = pd.to_datetime(df["Date"])

    # === APLICAR FILTROS DINÁMICOS ===
    if instituciones and "Institution" in df.columns:
        df = df[df["Institution"].isin(instituciones)]

    if categorias and "Category" in df.columns:
        df = df[df["Category"].isin(categorias)]

    if df.empty:
        return html.P("No hay datos para los filtros seleccionados."), None

    # === RESAMPLE MENSUAL ===
    # Balance mensual total (ingresos - gastos)
    df_mes = df.resample("ME", on="Date")["Amount"].sum().to_frame("Balance")

    # Gastos (negativos)
    df_gastos = df[df["Amount"] < 0].resample("ME", on="Date")["Amount"].sum()

    # Ingresos (positivos)
    df_ingresos = df[df["Amount"] > 0].resample("ME", on="Date")["Amount"].sum()

    # ==========================
    #  GRÁFICO DE LÍNEA (BALANCE)
    # ==========================
    fig_linea = go.Figure()
    fig_linea.add_trace(go.Scatter(
        x=df_mes.index,
        y=df_mes["Balance"],
        mode="lines+markers",
        name="Balance mensual",
        line=dict(color="blue", width=3)
    ))

    fig_linea.update_layout(
        title="Balance mensual",
        xaxis_title="Mes",
        yaxis_title="Balance (€)",
        template="forest_dark"
    )

    # ==========================
    #  GRÁFICO DE BARRAS (STACKED)
    # ==========================
    fig_barras = go.Figure()

    fig_barras.add_trace(go.Bar(
        x=df_ingresos.index,
        y=df_ingresos.values,
        name="Ingresos",
        marker_color="green"
    ))

    fig_barras.add_trace(go.Bar(
        x=df_gastos.index,
        y=df_gastos.values,
        name="Gastos",
        marker_color="red"
    ))

    fig_barras.update_layout(
        title="Ingresos y gastos mensuales",
        xaxis_title="Mes",
        yaxis_title="Cantidad (€)",
        barmode="relative",   # usar 'relative' para que gastos (negativos) vayan hacia abajo
        template="simple_white"
    )

    return dcc.Graph(figure=fig_linea), dcc.Graph(figure=fig_barras)