# app.py
# Dashboard Interactivo de Finanzas Personales (estructura base con tabs)

from dash import Dash, dcc, html, Input, Output, State
import dash  # para usar dash.no_update
import pandas as pd
import io
import base64
import plotly.graph_objects as go
import plotly.express as px
from pmdarima import auto_arima

# 1. Crear la aplicación Dash
app = Dash(__name__, suppress_callback_exceptions=True)

# Necesario para despliegue (Render, etc.)
server = app.server

# 2. Definir el layout (estructura visual)
app.layout = html.Div(
    children=[
        # Título principal
        html.H1("Dashboard de Finanzas Personales", style={"textAlign": "center"}),

        # === ZONA DE SUBIDA DE ARCHIVO ===
        dcc.Upload(
            id="upload-data",
            children=html.Div([
                "Arrastra y suelta tu archivo aquí o ",
                html.A("haz clic para seleccionarlo (CSV o Excel)")
            ]),
            style={
                "width": "80%",
                "margin": "20px auto",
                "padding": "20px",
                "borderWidth": "2px",
                "borderStyle": "dashed",
                "borderRadius": "10px",
                "textAlign": "center",
            },
            multiple=False  # solo un archivo
        ),

        # Aquí mostraremos un mensaje sobre el archivo cargado
        html.Div(
            id="upload-status",
            style={"textAlign": "center", "marginBottom": "20px"}
        ),

        # Almacen interno para guardar el DataFrame como JSON
        dcc.Store(id="Data"),

        # === TABS PRINCIPALES ===
        dcc.Tabs(
            id="tabs-principales",
            value="tab-resumen",  # pestaña seleccionada por defecto
            children=[
                dcc.Tab(label="Resumen", value="tab-resumen", children=[
                    html.Div(
                        id="kpi-container",
                        style={
                            "display": "flex",
                            "justifyContent": "space-around",
                            "marginTop": "20px",
                            "flexWrap": "wrap"
                        }
                    ),

                    html.Div(
                        id="grafico-resumen",
                        style={"marginTop": "40px"}
                    )
                ]),

                dcc.Tab(label="Categorías", value="tab-categorias", children=[
                    html.Div([
                        html.H3("Gastos por Categoría"),

                        # Aquí pondremos el gráfico
                        html.Div(id="grafico-categorias"),

                        # Aquí pondremos la tabla resumen
                        html.Div(id="tabla-categorias", style={"marginTop": "40px"})
                    ], style={"padding": "20px"})
                ]),

                dcc.Tab(label="Mensual", value="tab-mensual", children=[
                    html.Div([
                        html.H3("Análisis mensual"),

                        html.Div([
                            html.Label("Filtrar por institución:"),
                            dcc.Dropdown(
                                id="filtro-institucion",
                                placeholder="Selecciona una o varias instituciones",
                                multi=True
                            ),
                        ], style={"marginBottom": "20px"}),

                        html.Div([
                            html.Label("Filtrar por categoría:"),
                            dcc.Dropdown(
                                id="filtro-categoria",
                                placeholder="Selecciona una o varias categorías",
                                multi=True
                            ),
                        ], style={"marginBottom": "20px"}),

                        html.Div(id="grafico-mensual-linea", style={"marginTop": "40px"}),
                        html.Div(id="grafico-mensual-barras", style={"marginTop": "40px"}),
                    ], style={"padding": "20px"})
                ]),

                dcc.Tab(label="Instituciones", value="tab-instituciones", children=[
                    html.Div([
                        html.H3("Análisis por Institución", style={"marginTop": "20px"}),

                        # Filtro de institución
                        html.Label("Selecciona institución:", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="filtro-institucion-unico",
                            placeholder="Selecciona una institución",
                            style={"width": "50%", "marginBottom": "20px"}
                        ),

                        # gráfico
                        html.Div(id="grafico-institucion", style={"marginTop": "30px"}),

                        # tabla
                        html.Div(id="tabla-instituciones", style={"marginTop": "40px"})
                    ], style={"padding": "20px"})
                ]),

                dcc.Tab(label="Buscador", value="tab-buscador", children=[
                    html.Div([
                        html.H3("Buscador de transacciones", style={"marginTop": "20px"}),

                        # === FILA 1: BUSCADOR + CATEGORÍA ===
                        html.Div([
                            html.Div([
                                html.Label("Buscar texto en la descripción:", style={"fontWeight": "bold"}),
                                dcc.Input(
                                    id="buscador-descripcion",
                                    type="text",
                                    placeholder="Escribe parte de la descripción...",
                                    style={"width": "100%"}
                                )
                            ], style={"width": "48%"}),

                            html.Div([
                                html.Label("Categoría:", style={"fontWeight": "bold"}),
                                dcc.Dropdown(
                                    id="buscador-categoria",
                                    placeholder="Selecciona categoría",
                                    style={"width": "100%"}
                                )
                            ], style={"width": "48%"})
                        ], style={"display": "flex", "justifyContent": "space-between", "marginTop": "20px"}),

                        # === FILA 2: INSTITUCIÓN + FECHAS ===
                        html.Div([
                            html.Div([
                                html.Label("Institución:", style={"fontWeight": "bold"}),
                                dcc.Dropdown(
                                    id="buscador-institucion",
                                    placeholder="Selecciona institución",
                                    style={"width": "100%"}
                                )
                            ], style={"width": "48%"}),

                            html.Div([
                                html.Label("Rango de fechas:", style={"fontWeight": "bold"}),
                                dcc.DatePickerRange(
                                    id="buscador-fechas",
                                    display_format="YYYY-MM-DD",
                                    style={"width": "100%"}
                                )
                            ], style={"width": "48%"})
                        ], style={"display": "flex", "justifyContent": "space-between", "marginTop": "20px"}),

                        # === FILA 3: MONTOS ===
                        html.Div([
                            html.Div([
                                html.Label("Monto mínimo (€):", style={"fontWeight": "bold"}),
                                dcc.Input(
                                    id="monto-min",
                                    type="number",
                                    placeholder="Mínimo",
                                    style={"width": "100%"}
                                )
                            ], style={"width": "48%"}),

                            html.Div([
                                html.Label("Monto máximo (€):", style={"fontWeight": "bold"}),
                                dcc.Input(
                                    id="monto-max",
                                    type="number",
                                    placeholder="Máximo",
                                    style={"width": "100%"}
                                )
                            ], style={"width": "48%"})
                        ], style={"display": "flex", "justifyContent": "space-between", "marginTop": "20px"}),

                        # === RESULTADOS ===
                        html.Div(id="resultados-buscador", style={"marginTop": "40px"})
                    ], style={"padding": "20px"})
                ]),

                dcc.Tab(label="Mapa", value="tab-mapa", children=[
                    html.Div([
                        html.H3("Mapa de gastos e ingresos por país", style={"marginTop": "20px"}),

                        # === FILA 1: Selección de métrica ===
                        html.Div([
                            html.Div([
                                html.Label("Selecciona métrica:", style={"fontWeight": "bold"}),
                                dcc.Dropdown(
                                    id="mapa-metrica",
                                    options=[
                                        {"label": "Gastos", "value": "gastos"},
                                        {"label": "Ingresos", "value": "ingresos"},
                                        {"label": "Balance", "value": "balance"},
                                    ],
                                    value="balance",
                                    style={"width": "100%"}
                                )
                            ], style={"width": "48%"}),
                        ], style={
                            "display": "flex",
                            "justifyContent": "space-between",
                            "marginTop": "20px"
                        }),

                        # === MAPA ===
                        html.Div(id="mapa-output", style={"marginTop": "40px"}),

                    ], style={"padding": "20px"})
                ]),


                dcc.Tab(label="Predicción", value="tab-prediccion", children=[
                    html.Div([
                        html.H3("Predicción de gastos futuros", style={"marginTop": "20px"}),

                        html.Label("Meses a predecir:", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="pred-meses",
                            options=[
                                {"label": "3 meses", "value": 3},
                                {"label": "6 meses", "value": 6},
                                {"label": "12 meses", "value": 12},
                            ],
                            value=6,
                            style={"width": "200px", "marginBottom": "20px"}
                        ),

                        html.Div(id="prediccion-output", style={"marginTop": "30px"}),

                    ], style={"padding": "20px"})
                ]),
            ],
        ),
    ]
)

def parse_contents(contents, filename):
    """
    Recibe el contenido codificado y el nombre del archivo,
    devuelve un DataFrame de pandas.
    """
    content_type, content_string = contents.split(",")

    # Decodificar el contenido base64
    decoded = base64.b64decode(content_string)

    try:
        # Según la extensión del archivo, usamos read_csv o read_excel
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif filename.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None
    except Exception as e:
        print("Error al leer el archivo:", e)
        return None

    return df

def df_from_store(data_json):
    """Convierte el JSON guardado en Data a un DataFrame pandas."""
    if data_json is None:
        return None
    return pd.read_json(data_json, orient="split")

@app.callback(
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
        # No se ha subido archivo todavía
        return "No hay ningún archivo cargado.", dash.no_update

    # Procesar el archivo
    df = parse_contents(contents, filename)
    if df is None:
        return "Error al leer el archivo. Asegúrate de que es CSV o Excel.", dash.no_update

    # Intentamos hacer un pequeño resumen para enseñar al usuario
    filas = len(df)
    columnas = list(df.columns)

    # Si existe columna de fecha, Date, calculamos rango
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

    # Guardar el DataFrame en formato JSON para usarlo en otros callbacks
    data_json = df.to_json(date_format="iso", orient="split")

    return mensaje, data_json

@app.callback(
    Output("kpi-container", "children"),
    Input("Data", "data")
)
def actualizar_kpis(data_json):
    """
    Calcula y muestra los KPIs principales del resumen general.
    """
    df = df_from_store(data_json)

    if df is None:
        return [html.P("Sube un archivo para ver el resumen.")]

    # --- Asegurar que la columna de fecha es datetime ---
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    # --- Cálculos de KPIs ---
    total_gastado = df[df["Amount"] < 0]["Amount"].sum()
    total_ingresos = df[df["Amount"] > 0]["Amount"].sum()
    balance = df["Amount"].sum()

    # media mensual
    df_mensual = df.resample("ME", on="Date")["Amount"].sum()
    media_mensual = df_mensual.mean()

    num_transacciones = len(df)

    # --- Formateo de números ---
    def formato(eur):
        return f"{eur:,.2f} €".replace(",", ".").replace(".", ",", 1)

    # --- Construimos las tarjetas KPI ---
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
        html.Div([
            html.H4("Total Gastado"),
            html.H2(formato(total_gastado))
        ], style=estilo_kpi),

        html.Div([
            html.H4("Total Ingresos"),
            html.H2(formato(total_ingresos))
        ], style=estilo_kpi),

        html.Div([
            html.H4("Balance Total"),
            html.H2(formato(balance))
        ], style=estilo_kpi),

        html.Div([
            html.H4("Media Mensual"),
            html.H2(formato(media_mensual))
        ], style=estilo_kpi),

        html.Div([
            html.H4("Nº Transacciones"),
            html.H2(f"{num_transacciones}")
        ], style=estilo_kpi)
    ]

    return tarjetas

@app.callback(
    Output("grafico-resumen", "children"),
    Input("Data", "data")
)
def actualizar_graficos_resumen(data_json):
    df = df_from_store(data_json)

    if df is None:
        return html.P("Sube un archivo para ver los gráficos.")

    # Convertir Date a datetime
    df["Date"] = pd.to_datetime(df["Date"])

    # Agrupación mensual
    df_mensual = df.resample("ME", on="Date")["Amount"].sum().to_frame("Balance")

    # Gastos (Amount < 0)
    df_gastos = df[df["Amount"] < 0].resample("ME", on="Date")["Amount"].sum()

    # Ingresos (Amount > 0)
    df_ingresos = df[df["Amount"] > 0].resample("ME", on="Date")["Amount"].sum()

    # -------------------------------
    #  Gráfico con Plotly
    # -------------------------------
    fig = go.Figure()

    # Barras gastos
    fig.add_trace(go.Bar(
        x=df_gastos.index,
        y=df_gastos.values,
        name="Gastos",
        marker_color="red"
    ))

    # Barras ingresos
    fig.add_trace(go.Bar(
        x=df_ingresos.index,
        y=df_ingresos.values,
        name="Ingresos",
        marker_color="green"
    ))

    # Línea balance mensual
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
        template="simple_white"
    )

    return dcc.Graph(figure=fig)

@app.callback(
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

@app.callback(
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

@app.callback(
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
        template="simple_white"
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

@app.callback(
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

@app.callback(
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
        template="simple_white"
    )

    return dcc.Graph(figure=fig)

@app.callback(
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

@app.callback(
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


@app.callback(
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

@app.callback(
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

@app.callback(
    Output("prediccion-output", "children"),
    Input("Data", "data"),
    Input("pred-meses", "value")
)
def actualizar_prediccion(data_json, meses_pred):
    df = df_from_store(data_json)
    if df is None:
        return html.P("Sube un archivo para ver la predicción.")

    # Asegurar fecha
    df["Date"] = pd.to_datetime(df["Date"])

    # Solo gastos (positivizados)
    df_mensual = (
        df[df["Amount"] < 0]
        .resample("M", on="Date")["Amount"]
        .sum()
        .abs()
    )

    if len(df_mensual) < 6:
        return html.P("Se necesitan al menos 6 meses de historial.")

    # Último mes del historial
    last_date = df_mensual.index[-1]

    # Modelo ARIMA automático
    modelo = auto_arima(df_mensual, seasonal=False, error_action="ignore")

    # Predicción
    forecast, conf_int = modelo.predict(n_periods=meses_pred, return_conf_int=True)

    # Crear fechas futuras correctamente:
    # Desde el primer día del mes siguiente
    futuras_fechas = pd.date_range(
        start=last_date + pd.offsets.MonthBegin(1),
        periods=meses_pred,
        freq="M"
    )

    # ==== GRÁFICO ====
    fig = go.Figure()

    # Historial
    fig.add_trace(go.Scatter(
        x=df_mensual.index,
        y=df_mensual.values,
        mode="lines+markers",
        name="Historial de gastos",
        line=dict(color="blue")
    ))

    # Predicción
    fig.add_trace(go.Scatter(
        x=futuras_fechas,
        y=forecast,
        mode="lines+markers",
        name="Predicción",
        line=dict(color="orange")
    ))

    # Banda de confianza
    fig.add_trace(go.Scatter(
        x=list(futuras_fechas) + list(futuras_fechas[::-1]),
        y=list(conf_int[:, 0]) + list(conf_int[:, 1][::-1]),
        fill="toself",
        fillcolor="rgba(200,200,200,0.4)",
        line=dict(color="rgba(255,255,255,0)"),
        name="Intervalo de confianza"
    ))

    fig.update_layout(
        title=f"Predicción de gastos para los próximos {meses_pred} meses",
        xaxis_title="Fecha",
        yaxis_title="Gasto (€)",
        template="simple_white",
        height=600
    )

    return dcc.Graph(figure=fig)


# 3. Ejecutar la app en modo desarrollo
if __name__ == "__main__":
    app.run_server(debug=True)
