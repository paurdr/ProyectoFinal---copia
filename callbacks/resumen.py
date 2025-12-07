# callbacks/resumen.py
from dash import Input, Output, html, dcc
import pandas as pd
import plotly.graph_objects as go

from dash import callback
from utils.data_utils import df_from_store

@callback(
    Output("kpi-container", "children"),
    Input("Data", "data")
)
def actualizar_kpis(data_json):
    df = df_from_store(data_json)

    if df is None:
        return [html.P("Sube un archivo para ver el resumen.")]

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    total_gastado = df[df["Amount"] < 0]["Amount"].sum()
    total_ingresos = df[df["Amount"] > 0]["Amount"].sum()
    balance = df["Amount"].sum()

    df_mensual = df.resample("ME", on="Date")["Amount"].sum()
    media_mensual = df_mensual.mean()

    num_transacciones = len(df)

    def formato(eur):
        return f"{eur:,.2f} €".replace(",", ".").replace(".", ",", 1)

    estilo_kpi = {
        "border": "1px solid #ccc",
        "borderRadius": "10px",
        "padding": "20px",
        "width": "200px",
        "textAlign": "center",
        "margin": "10px",
        "boxShadow": "0 2px 5px rgba(0,0,0,0.1)"
    }

    tarjetas = [
        html.Div([html.H4("Total Gastado"), html.H2(formato(total_gastado))], style=estilo_kpi),
        html.Div([html.H4("Total Ingresos"), html.H2(formato(total_ingresos))], style=estilo_kpi),
        html.Div([html.H4("Balance Total"), html.H2(formato(balance))], style=estilo_kpi),
        html.Div([html.H4("Media Mensual"), html.H2(formato(media_mensual))], style=estilo_kpi),
        html.Div([html.H4("Nº Transacciones"), html.H2(f"{num_transacciones}")], style=estilo_kpi),
    ]

    return tarjetas


@callback(
    Output("grafico-resumen", "children"),
    Input("Data", "data")
)
def actualizar_graficos_resumen(data_json):
    df = df_from_store(data_json)

    if df is None:
        return html.P("Sube un archivo para ver los gráficos.")

    df["Date"] = pd.to_datetime(df["Date"])

    df_mensual = df.resample("ME", on="Date")["Amount"].sum().to_frame("Balance")

    df_gastos = df[df["Amount"] < 0].resample("ME", on="Date")["Amount"].sum()
    df_ingresos = df[df["Amount"] > 0].resample("ME", on="Date")["Amount"].sum()

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_gastos.index,
        y=df_gastos.values,
        name="Gastos",
        marker_color="red"
    ))

    fig.add_trace(go.Bar(
        x=df_ingresos.index,
        y=df_ingresos.values,
        name="Ingresos",
        marker_color="green"
    ))

    fig.add_trace(go.Scatter(
        x=df_mensual.index,
        y=df_mensual["Balance"],
        mode="lines+markers",
        name="Balance mensual",
        line=dict(color="blue")
    ))

    fig.update_layout(
        title="Resumen financiero mensual",
        xaxis_title="Fecha",
        yaxis_title="Cantidad (€)",
        barmode="group",
        template="forest_dark"
    )

    return dcc.Graph(figure=fig)