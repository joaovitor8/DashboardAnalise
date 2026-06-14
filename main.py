import base64
import io

import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table
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
    _grafico_vazio,
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

TAMANHO_MAXIMO_MB = 50

# ── App ──────────────────────────────────────────────────────────────────────
app = Dash(__name__, title="Dashboard de Análise")

app.layout = html.Div(
    style={"fontFamily": "Segoe UI, sans-serif", "padding": "24px",
           "backgroundColor": "#f0f2f5", "minHeight": "100vh"},
    children=[
        html.Div(style={**CARD, "padding": "16px 20px", "borderLeft": "4px solid #0d6efd"}, children=[
            html.H2("Dashboard de Análise de Dados",
                    style={"margin": 0, "color": "#212529", "fontWeight": 600}),
            html.P("Carregue um CSV ou Excel para começar",
                   style={"margin": "4px 0 0", "color": "#6c757d", "fontSize": "14px"}),
        ]),

        html.Div(style=CARD, children=[
            dcc.Upload(
                id="upload-data",
                children=html.Div([
                    "Arraste e solte ou ",
                    html.A("selecione um arquivo", style={"color": "#0d6efd"}),
                    html.Br(),
                    html.Span(f"CSV ou Excel · Máximo {TAMANHO_MAXIMO_MB}MB",
                              style={"fontSize": "12px", "color": "#adb5bd"}),
                ]),
                style={
                    "width": "100%", "height": "90px", "lineHeight": "1.6",
                    "borderWidth": "2px", "borderStyle": "dashed",
                    "borderRadius": "8px", "textAlign": "center",
                    "padding": "18px 0", "cursor": "pointer",
                    "borderColor": "#0d6efd", "color": "#495057",
                },
                multiple=False,
                max_size=TAMANHO_MAXIMO_MB * 1024 * 1024,
            ),
        ]),

        dcc.Store(id="store-df"),
        html.Div(id="output-overview"),
        html.Div(id="output-controles"),
        html.Div(id="output-graficos"),
    ]
)


# ── Callback 1: Upload → visão geral + controles ─────────────────────────────

def _parse_upload(contents: str, filename: str) -> pd.DataFrame:
    """
    Decodifica o arquivo vindo do browser.
    Lança ValueError com mensagem clara se o formato não for suportado.
    """
    _, content_string = contents.split(",", 1)
    decoded = base64.b64decode(content_string)

    ext = filename.rsplit(".", 1)[-1].lower()

    if ext == "csv":
        # Tenta UTF-8, depois latin-1 (comum em exports brasileiros)
        try:
            return pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        except UnicodeDecodeError:
            return pd.read_csv(io.StringIO(decoded.decode("latin-1")))

    elif ext in ("xlsx", "xls"):
        return pd.read_excel(io.BytesIO(decoded))

    else:
        raise ValueError(f"Formato '.{ext}' não suportado. Use CSV ou Excel.")


def _alerta(mensagem: str, tipo: str = "danger") -> html.Div:
    cores = {
        "danger":  ("#fff3cd", "#856404", "#ffc107"),
        "warning": ("#fff3cd", "#856404", "#ffc107"),
        "info":    ("#cff4fc", "#055160", "#0dcaf0"),
    }
    bg, text, border = cores.get(tipo, cores["danger"])
    return html.Div(mensagem, style={
        "backgroundColor": bg, "color": text,
        "border": f"1px solid {border}", "borderRadius": "6px",
        "padding": "12px 16px", "marginBottom": "16px", "fontSize": "14px",
    })


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

    # Parsing com mensagem de erro clara
    try:
        df_raw = _parse_upload(contents, filename)
    except ValueError as e:
        return None, _alerta(f"Arquivo inválido: {e}"), None
    except Exception as e:
        return None, _alerta(f"Erro inesperado ao ler '{filename}': {e}"), None

    # Validações básicas do DataFrame antes de qualquer processamento
    if df_raw.empty:
        return None, _alerta("O arquivo está vazio — nenhum dado encontrado."), None
    if df_raw.shape[1] == 0:
        return None, _alerta("O arquivo não tem colunas reconhecíveis."), None
    if df_raw.shape[0] < 2:
        return None, _alerta(
            "O arquivo tem menos de 2 linhas — análise estatística requer mais dados.",
            tipo="warning",
        ), None

    # Limpeza (já robusta no clean.py)
    df, mensagens = clean_data(df_raw)

    # Salva no Store
    store_data = df.to_json(date_format="iso", orient="split")

    caps = detectar_capacidades(df)

    # Aviso se nenhum gráfico for possível
    avisos = []
    if not caps["tem_histograma"] and not caps["tem_pizza"]:
        avisos.append(_alerta(
            "Este arquivo não tem colunas numéricas nem categóricas reconhecíveis. "
            "Verifique se o CSV está formatado corretamente.",
            tipo="warning",
        ))

    # Ícones de status no log de limpeza
    itens_log = []
    for m in mensagens:
        icone = "⚠️" if m.startswith("⚠️") else "✅"
        cor = "#856404" if "⚠️" in m else "#0f5132"
        itens_log.append(html.Li(m, style={"fontSize": "13px", "margin": "4px 0", "color": cor}))

    overview = html.Div([
        *avisos,
        html.Div(style=CARD, children=[
            html.H5("Visão Geral", style={"marginTop": 0, "color": "#343a40"}),
            html.Div(
                style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "16px"},
                children=[
                    _metrica("Linhas originais",    f"{df_raw.shape[0]:,}"),
                    _metrica("Linhas após limpeza", f"{df.shape[0]:,}"),
                    _metrica("Colunas",             f"{df.shape[1]}"),
                    _metrica("Numéricas",           f"{len(caps['numericas'])}"),
                    _metrica("Categóricas",         f"{len(caps['categoricas'])}"),
                ],
            ),
            html.Details(children=[
                html.Summary("🧹 Log de limpeza",
                             style={"cursor": "pointer", "color": "#6c757d", "fontSize": "13px"}),
                html.Ul(itens_log, style={"marginTop": "8px", "paddingLeft": "16px"}),
            ]),
        ]),
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

    controles = _montar_controles(caps)
    return store_data, overview, controles


# ── Callback 2: Seleção de colunas → gráficos adaptativos ───────────────────

def _gerar_seguro(fn, *args, **kwargs):
    """
    Chama a função de gráfico dentro de try/except.
    Se falhar, retorna _grafico_vazio com a mensagem de erro
    em vez de travar o callback inteiro.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        return _grafico_vazio(f"Erro ao gerar gráfico: {e}")


@app.callback(
    Output("output-graficos", "children"),
    Input("store-df", "data"),
    Input({"type": "ctrl", "id": "hist-col"},    "value"),
    Input({"type": "ctrl", "id": "scatter-x"},   "value"),
    Input({"type": "ctrl", "id": "scatter-y"},   "value"),
    Input({"type": "ctrl", "id": "barras-cat"},  "value"),
    Input({"type": "ctrl", "id": "barras-num"},  "value"),
    Input({"type": "ctrl", "id": "boxplot-cat"}, "value"),
    Input({"type": "ctrl", "id": "boxplot-num"}, "value"),
    Input({"type": "ctrl", "id": "pizza-col"},   "value"),
    prevent_initial_call=True,
)
def atualizar_graficos(store_data, hist_col, sc_x, sc_y,
                       bar_cat, bar_num, box_cat, box_num, pizza_col):
    if store_data is None:
        return dash.no_update

    try:
        df = pd.read_json(io.StringIO(store_data), orient="split")
    except Exception as e:
        return _alerta(f"Erro ao carregar dados do Store: {e}")

    caps = detectar_capacidades(df)
    graficos = []

    if caps["tem_histograma"] and hist_col:
        graficos.append(_card_grafico(_gerar_seguro(gerar_histograma, df, hist_col)))

    if caps["tem_scatter"] and sc_x and sc_y and sc_x != sc_y:
        graficos.append(_card_grafico(_gerar_seguro(gerar_scatter, df, sc_x, sc_y)))

    if caps["tem_heatmap"]:
        graficos.append(_card_grafico(_gerar_seguro(gerar_heatmap_correlacao, df)))

    if caps["tem_barras"] and bar_cat and bar_num:
        graficos.append(_card_grafico(_gerar_seguro(gerar_barras, df, bar_cat, bar_num)))

    if caps["tem_boxplot"] and box_cat and box_num:
        graficos.append(_card_grafico(_gerar_seguro(gerar_boxplot, df, box_cat, box_num)))

    if caps["tem_pizza"] and pizza_col:
        graficos.append(_card_grafico(_gerar_seguro(gerar_pizza, df, pizza_col)))

    if not graficos:
        return html.Div(
            "Selecione colunas nos controles acima para gerar gráficos.",
            style={**CARD, "color": "#6c757d", "textAlign": "center"},
        )

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
    return html.Div(style={**CARD, "marginBottom": 0},
                    children=[dcc.Graph(figure=fig)])


def _dropdown(id_val, options, placeholder, value=None):
    return dcc.Dropdown(
        id={"type": "ctrl", "id": id_val},
        options=[{"label": o, "value": o} for o in options],
        value=value or (options[0] if options else None),
        placeholder=placeholder,
        clearable=False,
        style=SELECT,
    )


def _montar_controles(caps: dict) -> html.Div:
    secoes = []

    if caps["tem_histograma"]:
        secoes.append(_secao("📊 Histograma", [
            html.P("Coluna", style=LABEL),
            _dropdown("hist-col", caps["numericas"], "Selecione coluna"),
        ]))

    if caps["tem_scatter"]:
        secoes.append(_secao("🔵 Dispersão", [
            html.P("Eixo X", style=LABEL),
            _dropdown("scatter-x", caps["numericas"], "Eixo X"),
            html.P("Eixo Y", style=LABEL),
            _dropdown("scatter-y", caps["numericas"], "Eixo Y",
                      value=caps["numericas"][1] if len(caps["numericas"]) > 1 else None),
        ]))

    if caps["tem_barras"]:
        secoes.append(_secao("📈 Barras", [
            html.P("Categoria", style=LABEL),
            _dropdown("barras-cat", caps["categoricas_uteis"], "Categoria"),
            html.P("Numérica", style=LABEL),
            _dropdown("barras-num", caps["numericas"], "Numérica"),
        ]))

    if caps["tem_boxplot"]:
        secoes.append(_secao("📦 Box plot", [
            html.P("Categoria", style=LABEL),
            _dropdown("boxplot-cat", caps["categoricas_uteis"], "Categoria"),
            html.P("Numérica", style=LABEL),
            _dropdown("boxplot-num", caps["numericas"], "Numérica"),
        ]))

    if caps["tem_pizza"]:
        secoes.append(_secao("🥧 Pizza", [
            html.P("Coluna categórica", style=LABEL),
            _dropdown("pizza-col", caps["categoricas_uteis"], "Coluna"),
        ]))

    if not secoes:
        return html.Div(
            "Nenhum gráfico disponível para este conjunto de dados.",
            style={**CARD, "color": "#6c757d"},
        )

    return html.Div(style=CARD, children=[
        html.H5("Controles de Gráficos", style={"marginTop": 0, "color": "#343a40"}),
        html.P("Os gráficos atualizam automaticamente ao mudar as seleções.",
               style={"fontSize": "13px", "color": "#6c757d", "marginBottom": "16px"}),
        html.Div(
            style={"display": "grid",
                   "gridTemplateColumns": "repeat(auto-fill, minmax(200px, 1fr))",
                   "gap": "0 24px"},
            children=secoes,
        ),
    ])


def _secao(titulo, children):
    return html.Div([
        html.P(titulo, style={"fontSize": "13px", "fontWeight": "600",
                               "color": "#495057", "marginBottom": "6px"}),
        *children,
    ])


if __name__ == "__main__":
    app.run(debug=True)