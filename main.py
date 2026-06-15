import base64
import io

import pandas as pd
from dash import Dash, dcc, html, Input, Output, State, dash_table
import dash

from src.clean import clean_data
from src.detector import detectar_dominio
from src.domain_analysis import analisar_dominio
from src.charts import (
  detectar_capacidades,
  gerar_histograma, gerar_scatter,
  gerar_heatmap_correlacao, gerar_barras,
  gerar_boxplot, gerar_pizza, _grafico_vazio,
)


# ── Estilos ──────────────────────────────────────────────────────────────────
CARD = {
  "backgroundColor": "white", "borderRadius": "8px",
  "padding": "20px", "boxShadow": "0 1px 4px rgba(0,0,0,0.07)",
  "marginBottom": "16px",
}
LABEL  = {"fontSize": "12px", "color": "#6c757d", "marginBottom": "4px"}
SELECT = {"width": "100%", "marginBottom": "12px"}
TAMANHO_MAXIMO_MB = 50


# ── App ──────────────────────────────────────────────────────────────────────
app = Dash(__name__, title="Dashboard de Análise")


app.layout = html.Div(
  style={"fontFamily": "Segoe UI, sans-serif", "padding": "24px", "backgroundColor": "#f0f2f5", "minHeight": "100vh"},

  children=[
    # Cabeçalho
    html.Div(style={**CARD, "padding": "16px 20px", "borderLeft": "4px solid #0d6efd"}, children=[
      html.H2("Dashboard de Análise de Dados",
        style={"margin": 0, "color": "#212529", "fontWeight": 600}),
      html.P("Carregue um CSV ou Excel — o sistema detecta o domínio automaticamente",
        style={"margin": "4px 0 0", "color": "#6c757d", "fontSize": "14px"}),
    ]),

    # Upload
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
        multiple=False, max_size=TAMANHO_MAXIMO_MB * 1024 * 1024,
      ),
    ]),

    dcc.Store(id="store-df"),

    # Três seções independentes, preenchidas pelo callback 1
    html.Div(id="output-overview"),
    html.Div(id="output-dominio"),   # ← NOVO: badge + KPIs + gráficos automáticos
    html.Div(id="output-controles"),

    # Gráficos genéricos, preenchidos pelo callback 2
    html.Div(id="output-graficos"),
  ]
)


# ── Callback 1: Upload ───────────────────────────────────────────────────────
def _parse_upload(contents: str, filename: str) -> pd.DataFrame:
  _, content_string = contents.split(",", 1)
  decoded = base64.b64decode(content_string)
  ext = filename.rsplit(".", 1)[-1].lower()
  if ext == "csv":
    try:
      return pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    except UnicodeDecodeError:
      return pd.read_csv(io.StringIO(decoded.decode("latin-1")))
  elif ext in ("xlsx", "xls"):
    return pd.read_excel(io.BytesIO(decoded))
  raise ValueError(f"Formato '.{ext}' não suportado. Use CSV ou Excel.")


def _alerta(msg: str, tipo: str = "danger") -> html.Div:
  paleta = {
    "danger":  ("#fff3cd", "#856404", "#ffc107"),
    "warning": ("#fff3cd", "#856404", "#ffc107"),
    "info":    ("#cff4fc", "#055160", "#0dcaf0"),
  }
  bg, text, border = paleta.get(tipo, paleta["danger"])
  return html.Div(msg, style={
    "backgroundColor": bg, "color": text,
    "border": f"1px solid {border}", "borderRadius": "6px",
    "padding": "12px 16px", "marginBottom": "16px", "fontSize": "14px",
  })


@app.callback(
  Output("store-df",        "data"),
  Output("output-overview", "children"),
  Output("output-dominio",  "children"),   # ← NOVO output
  Output("output-controles","children"),
  Input("upload-data",  "contents"),
  State("upload-data",  "filename"),
  prevent_initial_call=True,
)
def processar_upload(contents, filename):
  if contents is None:
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

  try:
    df_raw = _parse_upload(contents, filename)
  except ValueError as e:
    return None, _alerta(f"Arquivo inválido: {e}"), None, None
  except Exception as e:
    return None, _alerta(f"Erro ao ler '{filename}': {e}"), None, None

  if df_raw.empty:
    return None, _alerta("O arquivo está vazio."), None, None
  if df_raw.shape[0] < 5:
    return None, _alerta("Menos de 5 linhas — estatísticas requerem mais dados.", "warning"), None, None

  df, mensagens = clean_data(df_raw)
  store_data = df.to_json(date_format="iso", orient="split")
  caps = detectar_capacidades(df)


  # ── Overview ──
  itens_log = [
    html.Li(m, style={
      "fontSize": "13px", "margin": "4px 0",
      "color": "#856404" if "⚠️" in m else "#0f5132",
    })
    for m in mensagens
  ]
  overview = html.Div([
    html.Div(style=CARD, children=[
      html.H5("Visão Geral", style={"marginTop": 0, "color": "#343a40"}),
      html.Div(style={"display": "flex", "gap": "16px", "flexWrap": "wrap", "marginBottom": "16px"}, children=[
        _metrica("Linhas originais",    f"{df_raw.shape[0]:,}"),
        _metrica("Linhas pós-limpeza",  f"{df.shape[0]:,}"),
        _metrica("Colunas",             f"{df.shape[1]}"),
        _metrica("Numéricas",           f"{len(caps['numericas'])}"),
        _metrica("Categóricas",         f"{len(caps['categoricas'])}"),
      ]),
      html.Details([
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

  # ── Detecção de domínio ──
  deteccao  = detectar_dominio(df)
  analise   = analisar_dominio(df, deteccao)
  dominio_ui = _renderizar_dominio(deteccao, analise)

  # ── Controles genéricos ──
  controles = _montar_controles(caps)

  return store_data, overview, dominio_ui, controles


# ── Renderização da seção de domínio ─────────────────────────────────────────
def _renderizar_dominio(deteccao: dict, analise: dict) -> html.Div:
  if deteccao["dominio"] == "generico":
    return html.Div()   # Sem domínio detectado → seção oculta

  cor         = deteccao["cor"]
  emoji       = deteccao["emoji"]
  label       = deteccao["label"]
  confianca   = deteccao["confianca"]
  descricao   = deteccao["descricao"]
  kpis        = analise.get("kpis", [])
  graficos    = analise.get("graficos", [])
  insights    = analise.get("insights", [])

  # Texto e cor do badge de confiança
  confianca_cfg = {
    "alta":  ("Alta confiança",  "#d1e7dd", "#0f5132"),
    "media": ("Média confiança", "#fff3cd", "#856404"),
    "baixa": ("Baixa confiança", "#f8d7da", "#842029"),
  }
  conf_label, conf_bg, conf_text = confianca_cfg.get(confianca, ("", "#eee", "#333"))

  # ── Banner do domínio ──
  banner = html.Div(style={
    **CARD,
    "borderLeft": f"4px solid {cor}",
    "display": "flex", "alignItems": "center",
    "justifyContent": "space-between", "flexWrap": "wrap", "gap": "12px",
  }, children=[
    html.Div([
      html.Span(f"{emoji}  Domínio detectado: ", style={"color": "#6c757d", "fontSize": "13px"}),
      html.Span(label, style={"fontWeight": 700, "fontSize": "16px", "color": cor}),
      html.Br(),
      html.Span(descricao, style={"fontSize": "12px", "color": "#6c757d"}),
    ]),
    html.Span(conf_label, style={
      "fontSize": "11px", "fontWeight": 600,
      "backgroundColor": conf_bg, "color": conf_text,
      "padding": "4px 12px", "borderRadius": "999px",
    }),
  ])

  # ── KPI cards ──
  kpi_cards = html.Div(
    style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "16px"},
    children=[
      html.Div(style={
        "backgroundColor": cor if k.get("destaque") else "#f8f9fa",
        "borderRadius": "8px", "padding": "14px 20px",
        "minWidth": "140px", "textAlign": "center",
        "flex": "1",
      }, children=[
          html.Div(k["valor"], style={
            "fontSize": "20px", "fontWeight": "700",
            "color": "white" if k.get("destaque") else "#212529",
          }),
          html.Div(k["label"], style={
            "fontSize": "11px", "marginTop": "2px",
            "color": "rgba(255,255,255,0.85)" if k.get("destaque") else "#6c757d",
          }),
        ])
        for k in kpis
    ],
  ) if kpis else html.Div()

  # ── Insights ──
  insight_els = html.Div([
    _alerta(i, "warning") for i in insights
  ]) if insights else html.Div()

  # ── Gráficos do domínio ──
  graf_els = html.Div(
    style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
    children=[
      html.Div(style={**CARD, "marginBottom": 0},
        children=[dcc.Graph(figure=fig)])
      for fig in graficos
    ],
  ) if graficos else html.Div()

  return html.Div([
    banner,
    html.Div(style=CARD, children=[
      html.H6(f"Métricas — {label}", style={"color": "#343a40", "marginTop": 0}),
      kpi_cards,
      insight_els,
    ]) if (kpis or insights) else html.Div(),
    html.Div(style={**CARD, "paddingBottom": "4px"}, children=[
      html.H6(f"Gráficos Automáticos — {label}",
        style={"color": "#343a40", "marginTop": 0, "marginBottom": "16px"}),
      graf_els,
    ]) if graficos else html.Div(),
  ])


# ── Callback 2: Controles → gráficos genéricos ───────────────────────────────
def _gerar_seguro(fn, *args, **kwargs):
  try:
    return fn(*args, **kwargs)
  except Exception as e:
    return _grafico_vazio(f"Erro ao gerar gráfico: {e}")


@app.callback(
  Output("output-graficos", "children"),
  Input("store-df",                              "data"),
  Input({"type": "ctrl", "id": "hist-col"},     "value"),
  Input({"type": "ctrl", "id": "scatter-x"},    "value"),
  Input({"type": "ctrl", "id": "scatter-y"},    "value"),
  Input({"type": "ctrl", "id": "barras-cat"},   "value"),
  Input({"type": "ctrl", "id": "barras-num"},   "value"),
  Input({"type": "ctrl", "id": "boxplot-cat"},  "value"),
  Input({"type": "ctrl", "id": "boxplot-num"},  "value"),
  Input({"type": "ctrl", "id": "pizza-col"},    "value"),
  prevent_initial_call=True,
)
def atualizar_graficos(store_data, hist_col, sc_x, sc_y, bar_cat, bar_num, box_cat, box_num, pizza_col):
  if store_data is None:
    return dash.no_update

  try:
    df = pd.read_json(io.StringIO(store_data), orient="split")
  except Exception as e:
    return _alerta(f"Erro ao carregar dados: {e}")

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
    return html.Div("Selecione colunas nos controles acima para gerar gráficos.",
      style={**CARD, "color": "#6c757d", "textAlign": "center"})

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
  return dcc.Dropdown(
    id={"type": "ctrl", "id": id_val},
    options=[{"label": o, "value": o} for o in options],
    value=value or (options[0] if options else None),
    placeholder=placeholder, clearable=False, style=SELECT,
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
    return html.Div("Nenhum gráfico disponível para este conjunto de dados.",
      style={**CARD, "color": "#6c757d"})

  return html.Div(style=CARD, children=[
    html.H5("Explorar Dados", style={"marginTop": 0, "color": "#343a40"}),
    html.P("Gráficos customizáveis — escolha as colunas abaixo.",
      style={"fontSize": "13px", "color": "#6c757d", "marginBottom": "16px"}),
    html.Div(
      style={"display": "grid", "gridTemplateColumns": "repeat(auto-fill, minmax(200px, 1fr))", "gap": "0 24px"},
      children=secoes,
    ),
  ])


def _secao(titulo, children):
  return html.Div([
    html.P(titulo, style={"fontSize": "13px", "fontWeight": "600", "color": "#495057", "marginBottom": "6px"}),
    *children,
  ])


if __name__ == "__main__":
  app.run(debug=True)

