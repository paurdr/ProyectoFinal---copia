from dash import Input, Output, html, dcc  # y DatePickerRange, etc. si los usas
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  # solo si lo necesitas

from dash import callback
from utils.data_utils import df_from_store


@callback(
    Output("filtro-institucion-unico", "options"),
    Input("Data", "data")
)
def cargar_lista_instituciones(data_json):
    df = df_from_store(data_json)

    if df is None or "Institution" not in df.columns:
        return []

    instituciones = df["Institution"].dropna().unique()

    # Convertimos todo a string para evitar errores de mezcla str/int
    instituciones = [str(x) for x in instituciones]
    instituciones.sort()

    return [{"label": inst, "value": inst} for inst in instituciones]

@callback(
    Output("grafico-institucion", "children"),
    Input("Data", "data"),
    Input("filtro-institucion-unico", "value")
)
def actualizar_grafico_institucion(data_json, institucion):
    df = df_from_store(data_json)

    if df is None:
        return html.P("Sube un archivo para ver el gráfico.")

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    if "Institution" not in df.columns:
        return html.P("No existe columna 'Institution' en el archivo.")

    # Si no hay institución seleccionada → mensaje
    if institucion is None:
        return html.P("Selecciona una institución para ver el gráfico.")

    # Filtrar solo esa institución
    df_inst = df[df["Institution"].astype(str) == str(institucion)]

    if df_inst.empty:
        return html.P("No hay datos para esa institución.")

    # Agrupar por mes
    df_m = df_inst.resample("ME", on="Date")["Amount"].sum().to_frame("Balance")
    df_gastos = df_inst[df_inst["Amount"] < 0].resample("ME", on="Date")["Amount"].sum()
    df_ingresos = df_inst[df_inst["Amount"] > 0].resample("ME", on="Date")["Amount"].sum()

    # FIGURA
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_gastos.index, y=df_gastos.values,
        name="Gastos", marker_color="red"
    ))

    fig.add_trace(go.Bar(
        x=df_ingresos.index, y=df_ingresos.values,
        name="Ingresos", marker_color="green"
    ))

    fig.add_trace(go.Scatter(
        x=df_m.index, y=df_m["Balance"],
        mode="lines+markers",
        name="Balance mensual", line=dict(color="blue")
    ))

    fig.update_layout(
        title=f"Evolución financiera de {institucion}",
        xaxis_title="Fecha",
        yaxis_title="Cantidad (€)",
        barmode="group",
        template="forest_dark"
    )

    return dcc.Graph(figure=fig)

@callback(
    Output("tabla-instituciones", "children"),
    Input("Data", "data")
)
def tabla_resumen_instituciones(data_json):
    df = df_from_store(data_json)

    if df is None or "Institution" not in df.columns:
        return html.P("No se encuentra la columna 'Institution'.")

    # Agrupar todas las instituciones
    resumen = df.groupby("Institution")["Amount"].sum().sort_values(ascending=False)

    tabla = html.Table(
        [html.Tr([html.Th("Institución"), html.Th("Balance Total (€)")])] +
        [
            html.Tr([
                html.Td(str(inst)),
                html.Td(f"{float(resumen[inst]):,.2f} €")
            ])
            for inst in resumen.index
        ],
        style={"width": "50%", "margin": "auto", "borderCollapse": "collapse"}
    )

    return tabla