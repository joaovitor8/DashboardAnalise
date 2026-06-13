import base64
import io
import json

import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table, callback_context
import dash

from src.clean import clean_data
from src.analyzer import analyze
from src.charts import (
    detectar_capacidades,
    gerar_histograma,
    gerar_scatter,
    gerar_heatmap_correlacao,
    gerar_barras,
    gerar_boxplot,
    gerar_pizza,
)

# ── Helpers de estilo ────────────────────────────────────────────────────────
CARD = {
    "backgroundColor": "white",
    "borderRadius": "8px",
    "padding": "20px",
    "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
    "marginBottom": "16px",
}
LABEL = {"fontSize": "12px", "color": "#6c757d", "marginBottom": "4px"}
SELECT = {"width": "100%", "marginBottom": "12px"}

# ── App ──────────────────────────────────────────────────────────────────────
app = Dash(__name__, title="Dashboard de Análise")

app.layout = html.Div(
    style={"fontFamily": "Segoe UI, sans-serif", "padding": "24px", "backgroundColor": "#f0f2f5", "minHeight": "100vh"},
    children=[

        # Cabeçalho
        html.Div(style={**CARD, "padding": "16px 20px", "borderLeft": "4px solid #0d6efd"}, children=[
            html.H2("Dashboard de Análise de Dados", style={"margin": 0, "color": "#212529", "fontWeight": 600}),
            html.P("Carregue um CSV ou Excel para começar", style={"margin": "4px 0 0", "color": "#6c757d", "fontSize": "14px"}),
        ]),

        # Upload
        html.Div(style=CARD, children=[
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    html.I(className="", style={"fontSize": "24px", "marginBottom": "8px", "display": "block"}),
                    "Arraste e solte ou ",
                    html.A("selecione um arquivo", style={"color": "#0d6efd"}),
                    html.Br(),
                    html.Span("CSV ou Excel (.xlsx)", style={"fontSize": "12px", "color": "#adb5bd"}),
                ]),
                style={
                    "width": "100%", "height": "100px", "lineHeight": "1.5",
                    "borderWidth": "2px", "borderStyle": "dashed",
                    "borderRadius": "8px", "textAlign": "center",
                    "padding": "20px 0", "cursor": "pointer",
                    "borderColor": "#0d6efd", "color": "#495057",
                },
                multiple=False,
            ),
        ]),

        # Armazena o DataFrame como JSON entre callbacks (sem variável global)
        dcc.Store(id="store-df"),

        # Área preenchida pelo callback 1
        html.Div(id="output-overview"),

        # Controles de gráficos (preenchidos pelo callback 1)
        html.Div(id="output-controles"),

        # Gráficos (preenchidos pelo callback 2)
        html.Div(id="output-graficos"),
    ]
)


# ── Callback 1: Upload → visão geral + controles ─────────────────────────────
def parse_upload(contents, filename):
    """Decodifica o arquivo vindo do browser."""
    _, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    if filename.endswith(".csv"):
        return pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    return pd.read_excel(io.BytesIO(decoded))


@app.callback(
    Output("store-df", "data"),
    Output("output-overview", "children"),
    Output("output-controles", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def processar_upload(contents, filename):
    if contents is None:
        return dash.no_update, dash.no_update, dash.no_update

    try:
        df_raw = parse_upload(contents, filename)
    except Exception as e:
        erro = html.Div(f"Erro ao ler arquivo: {e}", style={"color": "red", **CARD})
        return None, erro, None

    # Limpeza — mensagens agora chegam aqui, não no terminal
    df, mensagens = clean_data(df_raw)

    # Salva no Store como JSON para o callback 2 usar
    store_data = df.to_json(date_format="iso", orient="split")

    # Análise
    resultado = analyze(df)
    caps = detectar_capacidades(df)

    # ── Visão geral ──
    overview = html.Div([
        html.Div(style=CARD, children=[
            html.H5("Visão Geral", style={"marginTop": 0, "color": "#343a40"}),

            # Métricas
            html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "16px"}, children=[
                _metrica("Linhas originais",   f"{df_raw.shape[0]:,}"),
                _metrica("Linhas após limpeza", f"{df.shape[0]:,}"),
                _metrica("Colunas",            f"{df.shape[1]}"),
                _metrica("Numéricas",          f"{len(caps['numericas'])}"),
                _metrica("Categóricas",        f"{len(caps['categoricas'])}"),
            ]),

            # Log de limpeza — exibido no BROWSER, não no terminal
            html.Details(children=[
                html.Summary("🧹 Log de limpeza", style={"cursor": "pointer", "color": "#6c757d", "fontSize": "13px"}),
                html.Ul([html.Li(m, style={"fontSize": "13px", "margin": "4px 0"}) for m in mensagens],
                        style={"marginTop": "8px", "paddingLeft": "16px"}),
            ]),
        ]),

        # Tabela de preview
        html.Div(style=CARD, children=[
            html.H6("Primeiras linhas", style={"color": "#343a40", "marginTop": 0}),
            dash_table.DataTable(
                data=df.head(10).to_dict("records"),
                columns=[{"name": c, "id": c} for c in df.columns],
                style_table={"overflowX": "auto"},
                style_cell={"fontSize": "13px", "padding": "6px 12px", "textAlign": "left"},
                style_header={"backgroundColor": "#f8f9fa", "fontWeight": "600"},
                page_size=10,
            ),
        ]),
    ])

    # ── Controles adaptativos — só aparece o que faz sentido ──
    controles = _montar_controles(caps)

    return store_data, overview, controles


# ── Callback 2: Seleção de colunas → gráficos adaptativos ───────────────────
@app.callback(
    Output("output-graficos", "children"),
    Input("store-df", "data"),
    # Inputs opcionais — só existem se o callback 1 já criou os controles
    Input({"type": "ctrl", "id": "hist-col"},       "value"),
    Input({"type": "ctrl", "id": "scatter-x"},      "value"),
    Input({"type": "ctrl", "id": "scatter-y"},      "value"),
    Input({"type": "ctrl", "id": "barras-cat"},     "value"),
    Input({"type": "ctrl", "id": "barras-num"},     "value"),
    Input({"type": "ctrl", "id": "boxplot-cat"},    "value"),
    Input({"type": "ctrl", "id": "boxplot-num"},    "value"),
    Input({"type": "ctrl", "id": "pizza-col"},      "value"),
    prevent_initial_call=True,
)
def atualizar_graficos(store_data, hist_col, sc_x, sc_y, bar_cat, bar_num, box_cat, box_num, pizza_col):
    if store_data is None:
        return dash.no_update

    df = pd.read_json(io.StringIO(store_data), orient="split")
    caps = detectar_capacidades(df)
    graficos = []

    # Grid adaptativo: só renderiza o gráfico se tiver coluna selecionada E fizer sentido
    if caps["tem_histograma"] and hist_col:
        graficos.append(_card_grafico(gerar_histograma(df, hist_col)))

    if caps["tem_scatter"] and sc_x and sc_y and sc_x != sc_y:
        graficos.append(_card_grafico(gerar_scatter(df, sc_x, sc_y)))

    if caps["tem_heatmap"] and len(caps["numericas"]) >= 2:
        graficos.append(_card_grafico(gerar_heatmap_correlacao(df)))

    if caps["tem_barras"] and bar_cat and bar_num:
        graficos.append(_card_grafico(gerar_barras(df, bar_cat, bar_num)))

    if caps["tem_boxplot"] and box_cat and box_num:
        graficos.append(_card_grafico(gerar_boxplot(df, box_cat, box_num)))

    if caps["tem_pizza"] and pizza_col:
        graficos.append(_card_grafico(gerar_pizza(df, pizza_col)))

    if not graficos:
        return html.Div("Selecione colunas nos controles acima para gerar gráficos.",
                        style={**CARD, "color": "#6c757d", "textAlign": "center"})

    # Grid 2 colunas
    return html.Div(
        style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
        children=graficos,
    )


# ── Helpers de layout ────────────────────────────────────────────────────────
def _metrica(label, valor):
    return html.Div(style={
        "backgroundColor": "#f8f9fa", "borderRadius": "6px",
        "padding": "10px 16px", "minWidth": "120px", "textAlign": "center",
    }, children=[
        html.Div(valor, style={"fontSize": "22px", "fontWeight": "600", "color": "#212529"}),
        html.Div(label, style={"fontSize": "11px", "color": "#6c757d", "marginTop": "2px"}),
    ])


def _card_grafico(fig):
    return html.Div(style={**CARD, "marginBottom": 0}, children=[dcc.Graph(figure=fig)])


def _dropdown(id_val, options, placeholder, value=None):
    """Dropdown com ID pattern-matching para o callback 2."""
    return dcc.Dropdown(
        id={"type": "ctrl", "id": id_val},
        options=[{"label": o, "value": o} for o in options],
        value=value or (options[0] if options else None),
        placeholder=placeholder,
        clearable=False,
        style=SELECT,
    )


def _montar_controles(caps: dict) -> html.Div:
    """
    Cria apenas os dropdowns que fazem sentido para os dados.
    Se o CSV só tiver texto, não aparece dropdown de histograma.
    Se só tiver números, não aparece pizza nem barras.
    """
    secoes = []

    if caps["tem_histograma"]:
        secoes.append(_secao_controle("📊 Histograma", [
            html.P("Coluna", style=LABEL),
            _dropdown("hist-col", caps["numericas"], "Selecione coluna"),
        ]))

    if caps["tem_scatter"]:
        secoes.append(_secao_controle("🔵 Dispersão", [
            html.P("Eixo X", style=LABEL),
            _dropdown("scatter-x", caps["numericas"], "Eixo X"),
            html.P("Eixo Y", style=LABEL),
            _dropdown("scatter-y", caps["numericas"], "Eixo Y",
                      value=caps["numericas"][1] if len(caps["numericas"]) > 1 else None),
        ]))

    if caps["tem_barras"]:
        secoes.append(_secao_controle("📈 Barras por categoria", [
            html.P("Categoria", style=LABEL),
            _dropdown("barras-cat", caps["categoricas_uteis"], "Categoria"),
            html.P("Numérica", style=LABEL),
            _dropdown("barras-num", caps["numericas"], "Numérica"),
        ]))

    if caps["tem_boxplot"]:
        secoes.append(_secao_controle("📦 Box plot", [
            html.P("Categoria", style=LABEL),
            _dropdown("boxplot-cat", caps["categoricas_uteis"], "Categoria"),
            html.P("Numérica", style=LABEL),
            _dropdown("boxplot-num", caps["numericas"], "Numérica"),
        ]))

    if caps["tem_pizza"]:
        secoes.append(_secao_controle("🥧 Pizza", [
            html.P("Coluna categórica", style=LABEL),
            _dropdown("pizza-col", caps["categoricas_uteis"], "Coluna"),
        ]))

    if not secoes:
        return html.Div("Nenhum gráfico disponível para este conjunto de dados.",
                        style={**CARD, "color": "#6c757d"})

    return html.Div(style={**CARD}, children=[
        html.H5("Controles de Gráficos", style={"marginTop": 0, "color": "#343a40"}),
        html.P("Os gráficos atualizam automaticamente ao mudar as seleções.",
               style={"fontSize": "13px", "color": "#6c757d", "marginBottom": "16px"}),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "repeat(auto-fill, minmax(200px, 1fr))", "gap": "0 24px"},
            children=secoes,
        ),
    ])


def _secao_controle(titulo, children):
    return html.Div([
        html.P(titulo, style={"fontSize": "13px", "fontWeight": "600",
                               "color": "#495057", "marginBottom": "6px"}),
        *children,
    ])


if __name__ == "__main__":
    app.run(debug=True)