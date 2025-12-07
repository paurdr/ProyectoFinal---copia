from dash import Input, Output, html, dcc  # y DatePickerRange, etc. si los usas
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px  # solo si lo necesitas

from dash import callback
from utils.data_utils import df_from_store

@callback(
    Output("grafico-categorias", "children"),
    Output("tabla-categorias", "children"),
    Input("Data", "data")
)
def actualizar_categorias(data_json):
    df = df_from_store(data_json)

    if df is None:
        return html.P("Sube un archivo para ver las categorías."), None

    # Asegurar formato de fecha
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    # Mantener solo gastos (Amount < 0)
    df_gastos = df[df["Amount"] < 0]

    if "Category" not in df_gastos.columns:
        return html.P("No existe una columna llamada 'Category'."), None

    # Agrupación por categoría
    resumen = df_gastos.groupby("Category")["Amount"].sum().sort_values()

    # Convertimos los valores negativos a positivos para mostrar bien los gráficos
    resumen_abs = resumen.abs()

    # % de gasto
    porcentajes = (resumen_abs / resumen_abs.sum()) * 100

    # -------------------------------
    #  GRÁFICO PIE
    # -------------------------------
    fig = go.Figure(data=[
        go.Pie(
            labels=resumen_abs.index,
            values=resumen_abs.values,
            hole=0.4,
            hoverinfo="label+percent+value",
        )
    ])

    fig.update_layout(
        title="Distribución del gasto por categoría",
        showlegend=True
    )

    grafico = dcc.Graph(figure=fig)

    # -------------------------------
    #  TABLA RESUMEN
    # -------------------------------
    tabla = html.Table(
        [
            html.Tr([html.Th("Categoría"), html.Th("Gasto Total (€)"), html.Th("% del gasto")])
        ] + [
            html.Tr([
                html.Td(cat),
                html.Td(f"{float(resumen_abs[cat]):,.2f} €"),
                html.Td(f"{porcentajes[cat]:.2f}%")
            ])
            for cat in resumen_abs.index
        ],
        style={"width": "60%", "margin": "auto", "borderCollapse": "collapse"}
    )

    return grafico, tabla

@callback(
    Output("filtro-institucion", "options"),
    Output("filtro-categoria", "options"),
    Input("Data", "data")
)
def cargar_filtros(data_json):
    df = df_from_store(data_json)
    if df is None:
        return [], []

    opciones_institucion = []
    opciones_categoria = []

    # --- Opciones de institución ---
    if "Institution" in df.columns:
        instituciones = df["Institution"].dropna().unique()
        # Pasamos todo a string para evitar mezclas str/int
        instituciones = [str(x) for x in instituciones]
        instituciones.sort()
        opciones_institucion = [{"label": inst, "value": inst} for inst in instituciones]

    # --- Opciones de categoría ---
    if "Category" in df.columns:
        categorias = df["Category"].dropna().unique()
        categorias = [str(x) for x in categorias]
        categorias.sort()
        opciones_categoria = [{"label": cat, "value": cat} for cat in categorias]

    return opciones_institucion, opciones_categoria
