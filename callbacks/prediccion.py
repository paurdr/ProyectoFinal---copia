from dash import Input, Output, html, dcc, State  # y DatePickerRange, etc. si los usas
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px  # solo si lo necesitas

from dash import callback
from utils.data_utils import df_from_store

from pmdarima import auto_arima
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LinearRegression

@callback(
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
        .resample("ME", on="Date")["Amount"]
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
        freq="MS"
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
        template="forest_dark",
        height=600
    )

    return dcc.Graph(figure=fig)

# === CALLBACK DE SEGMENTACIÓN AVANZADA ===
@callback(
    Output("cluster-output", "children"),
    Input("Data", "data")
)
def segmentar_meses(data_json):

    df = df_from_store(data_json)
    if df is None:
        return html.P("Sube un archivo para ver la segmentación de meses.")

    df["Date"] = pd.to_datetime(df["Date"])

    # ============================
    #  1. AGREGACIÓN MENSUAL
    # ============================
    mensual = pd.DataFrame()
    mensual["gastos_abs"] = df[df["Amount"] < 0].resample("M", on="Date")["Amount"].sum().abs()
    mensual["ingresos"]   = df[df["Amount"] > 0].resample("M", on="Date")["Amount"].sum().abs()
    mensual["balance"]    = df.resample("M", on="Date")["Amount"].sum()
    mensual["n_trans"]    = df.resample("M", on="Date")["Amount"].count()
    mensual = mensual.dropna().reset_index()
    mensual["Mes"] = mensual["Date"]

    # ==========================================
    #  2. CLUSTERING POR GASTO (A > B > C)
    # ==========================================
    q1 = mensual["gastos_abs"].quantile(0.33)
    q2 = mensual["gastos_abs"].quantile(0.66)

    def clasificar(x):
        if x <= q1:
            return "Mes tipo C"     # menor gasto
        elif x <= q2:
            return "Mes tipo B"     # gasto medio
        else:
            return "Mes tipo A"     # mayor gasto

    mensual["tipo_mes"] = mensual["gastos_abs"].apply(clasificar)

    # Orden leyenda
    orden = ["Mes tipo A", "Mes tipo B", "Mes tipo C"]
    mensual["tipo_mes"] = pd.Categorical(mensual["tipo_mes"], categories=orden, ordered=True)

    # ===============================
    #  3. SCATTER PLOT
    # ===============================
    import plotly.express as px

    fig = px.scatter(
        mensual,
        x="ingresos",
        y="gastos_abs",
        color="tipo_mes",
        hover_name="Mes",
        labels={
            "ingresos": "Ingresos mensuales (€)",
            "gastos_abs": "Gastos mensuales (€, absolutos)",
            "tipo_mes": "Tipo de mes"
        },
        category_orders={"tipo_mes": orden},
        title="Clusters de meses según ingresos y gastos",
    )

    fig.update_traces(marker=dict(size=20))     # puntos más grandes
    fig.update_layout(height=550)               # gráfico más pequeño

    grafico = dcc.Graph(figure=fig)

    # ===============================
    #  4. TABLA RESUMEN CLUSTERS
    # ===============================
    tabla_clusters = mensual.groupby("tipo_mes").agg(
        n_meses=("Mes", "count"),
        gasto_medio=("gastos_abs", "mean"),
        ingreso_medio=("ingresos", "mean"),
        balance_medio=("balance", "mean")
    ).reset_index()

    tabla_html = html.Table([
        html.Thead(html.Tr([
            html.Th("Tipo de mes"), html.Th("Nº meses"),
            html.Th("Gasto medio (€)"), html.Th("Ingreso medio (€)"),
            html.Th("Balance medio (€)")
        ])),
        html.Tbody([
            html.Tr([
                html.Td(row["tipo_mes"]),
                html.Td(f"{row['n_meses']}"),
                html.Td(f"{row['gasto_medio']:.2f}"),
                html.Td(f"{row['ingreso_medio']:.2f}"),
                html.Td(f"{row['balance_medio']:.2f}")
            ]) for _, row in tabla_clusters.iterrows()
        ])
    ], style={"marginTop": "20px", "width": "80%", "margin": "auto"})

    # ===============================
    #  5. INSIGHTS AUTOMÁTICOS
    # ===============================
    mes_mayor_gasto   = mensual.loc[mensual["gastos_abs"].idxmax(), "Mes"].strftime("%B %Y")
    mes_menor_gasto   = mensual.loc[mensual["gastos_abs"].idxmin(), "Mes"].strftime("%B %Y")
    mejor_balance     = mensual.loc[mensual["balance"].idxmax(), "Mes"].strftime("%B %Y")
    peor_balance      = mensual.loc[mensual["balance"].idxmin(), "Mes"].strftime("%B %Y")

    insights = html.Div([
        html.H3("Insights automáticos"),
        html.Ul([
            html.Li(f"Mes con MAYOR gasto: {mes_mayor_gasto}"),
            html.Li(f"Mes con MENOR gasto: {mes_menor_gasto}"),
            html.Li(f"Mes con mejor balance: {mejor_balance}"),
            html.Li(f"Mes con peor balance: {peor_balance}"),
        ])
    ], style={"marginTop": "30px"})

    # ===============================
    #  6. DETALLES EXPLICATIVOS
    # ===============================
    explicacion = html.Div([
        html.H3("Explicación de los clusters"),
        html.Ul([
            html.Li("Mes tipo A → Meses con **gasto alto**, típicamente asociados a compras grandes, vacaciones o pagos excepcionales."),
            html.Li("Mes tipo B → Meses con **gasto intermedio**, comportamiento financiero normal."),
            html.Li("Mes tipo C → Meses con **gasto bajo**, normalmente acompañados de poco movimiento o alta disciplina de ahorro."),
        ])
    ])

    # ===============================
    #  7. REGLAS DE HÁBITOS DE GASTO
    # ===============================
    reglas = html.Div([
        html.H3("Reglas sugeridas según tus hábitos"),
        html.Ul([
            html.Li("Si encadenas 2 o más meses tipo A → revisa gastos extraordinarios."),
            html.Li("Si tus meses tipo C coinciden con ingresos altos → puedes ahorrar más esos meses."),
            html.Li("Si hay mucha variabilidad entre meses A y C → definir un presupuesto mensual puede minimizar picos."),
        ])
    ])

    # ===============================
    #  8. RECOMENDACIONES AUTOMÁTICAS
    # ===============================
    recomendaciones = html.Div([
        html.H3("Recomendaciones basadas en tus patrones"),
        html.Ul([
            html.Li("Planifica compras grandes en meses con mejores ingresos."),
            html.Li("Revisa los meses tipo A para identificar patrones repetidos (viajes, compras, recibos)."),
            html.Li("Aprovecha los meses tipo C para aumentar ahorro o amortizar deudas."),
        ])
    ])

    return html.Div([
        html.H2("Segmentación de meses por patrones de gasto"),
        grafico,
        tabla_html,
        insights,
        explicacion,
        reglas,
        recomendaciones
    ])

@callback(
    Output("anom-output", "children"),
    Input("Data", "data"),
    Input("anom-contamination", "value")
)
def detectar_anomalias(data_json, contamination):
    """
    Detecta meses con gasto 'anómalo' usando Isolation Forest.
    Trabaja con el gasto mensual total (solo Amount < 0, en valor absoluto).
    """
    df = df_from_store(data_json)

    if df is None:
        return html.P("Sube un archivo para ver la detección de anomalías.")

    # Aseguramos formato fecha
    if "Date" not in df.columns or "Amount" not in df.columns:
        return html.P("No se encuentran las columnas 'Date' y 'Amount' necesarias.")

    df["Date"] = pd.to_datetime(df["Date"])

    # Serie mensual de gastos (en valor absoluto, para que sea positiva)
    gastos_mensuales = (
        df[df["Amount"] < 0]
        .resample("ME", on="Date")["Amount"]
        .sum()
        .abs()
        .to_frame(name="Gasto")
    )

    if len(gastos_mensuales) < 6:
        return html.P("Se necesitan al menos 6 meses de historial de gastos para detectar anomalías.")

    # ----- Modelo IsolationForest -----
    modelo = IsolationForest(
        contamination=float(contamination),
        random_state=123
    )

    modelo.fit(gastos_mensuales[["Gasto"]])
    pred = modelo.predict(gastos_mensuales[["Gasto"]])  # 1 = normal, -1 = anómalo
    score = modelo.decision_function(gastos_mensuales[["Gasto"]])

    gastos_mensuales["Es_anomalo"] = (pred == -1)
    gastos_mensuales["Score"] = score

    # Separamos normales y anómalos para el gráfico
    normales = gastos_mensuales[~gastos_mensuales["Es_anomalo"]]
    anomalias = gastos_mensuales[gastos_mensuales["Es_anomalo"]]

    # ----- Gráfico -----
    fig = go.Figure()

    # Línea de todos los gastos
    fig.add_trace(go.Scatter(
        x=gastos_mensuales.index,
        y=gastos_mensuales["Gasto"],
        mode="lines+markers",
        name="Gasto mensual",
        line=dict(color="steelblue"),
        marker=dict(size=8)
    ))

    # Puntos de anomalías en rojo más grandes
    if not anomalias.empty:
        fig.add_trace(go.Scatter(
            x=anomalias.index,
            y=anomalias["Gasto"],
            mode="markers",
            name="Mes anómalo",
            marker=dict(color="red", size=14, symbol="circle-open"),
        ))

    fig.update_layout(
        title="Gasto mensual con anomalías detectadas",
        xaxis_title="Fecha",
        yaxis_title="Gasto (€)",
        template="forest_dark",
        height=450  # un poco más pequeño
    )

    # ----- Tabla resumen de meses anómalos -----
    if anomalias.empty:
        tabla_html = html.P("No se han detectado meses anómalos con la sensibilidad actual.")
    else:
        tabla_html = html.Table(
            [html.Tr([html.Th("Mes"), html.Th("Gasto (€)"), html.Th("Score (más bajo = más raro)")])] +
            [
                html.Tr([
                    html.Td(idx.strftime("%Y-%m")),
                    html.Td(f"{row['Gasto']:,.2f} €"),
                    html.Td(f"{row['Score']:.3f}")
                ])
                for idx, row in anomalias.iterrows()
            ],
            style={"width": "70%", "margin": "20px auto", "borderCollapse": "collapse"}
        )

    return html.Div([
        dcc.Graph(figure=fig),
        html.H4("Meses detectados como anómalos", style={"textAlign": "center", "marginTop": "20px"}),
        tabla_html
    ])


@callback(
    Output("recom-output", "children"),
    Input("recom-calc", "n_clicks"),
    State("Data", "data"),
)
def recomendaciones_ahorro(n_clicks, data_json):

    if n_clicks == 0:
        return ""

    df = df_from_store(data_json)
    if df is None:
        return html.P("Sube un archivo primero.")

    # --- Preparar datos ---
    df["Date"] = pd.to_datetime(df["Date"])

    # ingresos y gastos por mes
    mensual = df.resample("ME", on="Date")["Amount"].sum().to_frame("Balance")
    gastos = df[df["Amount"] < 0].resample("ME", on="Date")["Amount"].sum().abs()
    ingresos = df[df["Amount"] > 0].resample("ME", on="Date")["Amount"].sum()

    df_ml = pd.DataFrame({
        "Ingresos": ingresos,
        "Gastos": gastos,
        "Balance": ingresos - gastos
    }).dropna()

    # ============================================================
    # 1) MODELO DE REGRESIÓN: Gasto esperado según ingresos
    # ============================================================
    X = df_ml[["Ingresos"]]
    y = df_ml["Gastos"]

    modelo = LinearRegression()
    modelo.fit(X, y)

    gasto_previsto = modelo.predict(X)

    df_ml["Gasto previsto (€)"] = gasto_previsto.round(2)
    df_ml["Desviación (€)"] = (df_ml["Gastos"] - df_ml["Gasto previsto (€)"]).round(2)

    # ============================================================
    # 2) REGLAS INTELIGENTES DE AHORRO
    # ============================================================
    recomendaciones = []

    for mes, row in df_ml.iterrows():

        ingreso = row["Ingresos"]
        gasto_real = row["Gastos"]
        gasto_esperado = row["Gasto previsto (€)"]
        desviacion = row["Desviación (€)"]

        # regla 1 — 20% ahorro recomendado (método 50/30/20)
        ahorro_meta = ingreso * 0.20

        # regla 2 — si gastas más de lo esperado
        if desviacion > 0:
            texto = f"⚠️ En {mes.strftime('%b %Y')} gastaste {desviacion:.2f} € más de lo esperado."
        else:
            texto = f"✔️ En {mes.strftime('%b %Y')} gastaste {abs(desviacion):.2f} € menos de lo esperado."

        # regla 3 — recomendaciones personalizadas
        if gasto_real > ingreso:
            extra = "Gastas más de lo que ingresas. Urge recortar gastos fijos."
        elif gasto_real > ingreso * 0.8:
            extra = "Tu gasto está muy cerca de tus ingresos. Considera reducir ocio/compras."
        elif gasto_real < ingreso * 0.6:
            extra = "Excelente control del gasto. Podrías aumentar tu ahorro mensual."
        else:
            extra = "Todo dentro de niveles razonables."

        recomendaciones.append(
            html.Div([
                html.H4(mes.strftime("%B %Y")),
                html.P(texto),
                html.P(f"💰 Ahorro recomendado: {ahorro_meta:.2f} €"),
                html.P(extra),
                html.Hr()
            ], style={"padding": "10px"})
        )

    return recomendaciones