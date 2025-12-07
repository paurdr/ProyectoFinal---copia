# app.py
# Dashboard Interactivo de Finanzas Personales (estructura base con tabs)

from dash import Dash, dcc, html, Input, Output, State
import dash  # para usar dash.no_update
import pandas as pd
import io
import base64
import plotly.graph_objects as go
import plotly.express as px
from sklearn.ensemble import IsolationForest
import plotly.io as pio

# 1. Crear la aplicación Dash
app = Dash(__name__, suppress_callback_exceptions=True)

# Necesario para despliegue (Render, etc.)
server = app.server

forest_dark_theme = {
    "layout": {
        "paper_bgcolor": "#0f2a24",     # fondo fuera del gráfico
        "plot_bgcolor": "#0f2a24",      # fondo dentro del gráfico
        "font": {"color": "#f4f1e9"},   # color texto general (crema)

        # Colores de la cuadrícula
        "xaxis": {
            "gridcolor": "#26433f",
            "zerolinecolor": "#26433f",
            "linecolor": "#f4f1e9",
            "tickfont": {"color": "#f4f1e9"}
        },
        "yaxis": {
            "gridcolor": "#26433f",
            "zerolinecolor": "#26433f",
            "linecolor": "#f4f1e9",
            "tickfont": {"color": "#f4f1e9"}
        },

        # Colores por defecto de las series
        "colorway": ["#ffb48a", "#78c6a3", "#ffd49e", "#a0e8af", "#ff9a76"],

        # Leyenda
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": "#f4f1e9"}
        },

        # Títulos
        "title": {"font": {"color": "#ffb48a", "size": 22}},
    }
}

# Activar el tema globalmente
pio.templates["forest_dark"] = forest_dark_theme
pio.templates.default = "forest_dark"


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

                        # ----------------------------
                        # (1) PREDICCIÓN ARIMA
                        # ----------------------------
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


                        # ----------------------------
                        # (2) CLUSTERING
                        # ----------------------------
                        html.H3("Segmentación de meses por patrones de gasto", style={"marginTop": "40px"}),
                        html.Div(id="cluster-output", style={"marginTop": "20px"}),


                        # ----------------------------
                        # (3) ANOMALÍAS
                        # ----------------------------
                        html.Hr(),
                        html.H3("Detección de anomalías en gastos mensuales", style={"marginTop": "30px"}),

                        html.Label(
                            "Sensibilidad del detector (más alto = más meses marcados como anómalos):",
                            style={"fontWeight": "bold"}
                        ),

                        html.Div(
                            dcc.Slider(
                                id="anom-contamination",
                                min=0.02,
                                max=0.30,
                                step=0.02,
                                value=0.10,
                                marks={
                                    0.02: "2%",
                                    0.10: "10%",
                                    0.20: "20%",
                                    0.30: "30%",
                                },
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                            style={"marginTop": "20px", "marginBottom": "20px"}
                        ),

                        html.Div(id="anom-output", style={"marginTop": "20px"}),


                        # ----------------------------
                        # (4) RECOMENDACIONES ML
                        # ----------------------------
                        html.Hr(),
                        html.H3("Recomendaciones de ahorro personalizadas", style={"marginTop": "40px"}),

                        html.Button(
                            "Calcular recomendaciones",
                            id="recom-calc",
                            n_clicks=0,
                            style={"marginTop": "10px"}
                        ),

                        html.Div(id="recom-output", style={"marginTop": "20px"}),

                    ], style={"padding": "20px"})
                ]),
            ],
        ),
    ]
)

# IMPORTAMOS LOS CALLBACKS (esto registra las funciones)
from callbacks import upload
from callbacks import resumen
from callbacks import categorias
from callbacks import mensual
from callbacks import instituciones
from callbacks import buscador
from callbacks import mapa
from callbacks import prediccion

# 3. Ejecutar la app en modo desarrollo
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)
