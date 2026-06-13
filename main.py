import base64
import io
import dash
from dash import dcc, html, Input, Output, State, dash_table
import pandas as pd

# Importar as tuas funções existentes
from src.clean import clean_data
from src.analyzer import analyze
from src.charts import gerar_graficos_interativos

# Inicializar a aplicação Dash
app = dash.Dash(__name__, title="Dashboard de Análise")

# Layout da aplicação usando componentes HTML e Dash
app.layout = html.Div(style={"fontFamily": "Segoe UI, sans-serif", "padding": "20px", "backgroundColor": "#f8f9fa"}, children=[
    html.Header(style={"borderBottom": "2px solid #e9ecef", "marginBottom": "20px"}, children=[
        html.H1("Dashboard de Análise de Dados", style={"color": "#212529", "fontWeight": "600"}),
        html.P("Faça upload de um ficheiro CSV ou Excel para iniciar a análise reativa.", style={"color": "#6c757d"})
    ]),

    # Componente de Upload (Substitui o Tkinter)
    dcc.Upload(
        id="upload-data",
        children=html.Div(["Arraste e solte ou ", html.A("Selecione um Ficheiro")]),
        style={
            "width": "100%", "height": "80px", "lineHeight": "80px",
            "borderWidth": "2px", "borderStyle": "dashed", "borderRadius": "8px",
            "textAlign": "center", "backgroundColor": "#ffffff", "borderColor": "#0d6efd",
            "cursor": "pointer", "color": "#495057", "marginBottom": "20px"
        },
        multiple=False
    ),

    # Espaço para renderizar os resultados da análise e gráficos
    html.Div(id="output-dashboard")
])

# Função auxiliar para processar o ficheiro vindo do navegador (Substitui o loader.py)
def parse_contents(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif "xls" in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        return df
    except Exception as e:
        print(e)
        return None

# Callback reativo do Dash
@app.callback(
    Output("output-dashboard", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename")
)
def update_output(contents, filename):
    if contents is None:
        return html.Div(style={"textAlign": "center", "marginTop": "40px"}, children=[
            html.H3("Aguardando upload de dados...", style={"color": "#adb5bd"})
        ])

    # 1. Carregar Dados
    df = parse_contents(contents, filename)
    if df is None:
        return html.Div("Ocorreu um erro ao processar o ficheiro.", style={"color": "red"})

    # 2. Executar a tua limpeza existente automaticamente
    df_limpo = clean_data(df)

    # 3. Executar a tua análise existente
    resultado_analise = analyze(df_limpo)

    # 4. Gerar os novos gráficos interativos do Plotly
    graficos = gerar_graficos_interativos(df_limpo)

    # Construir a interface de visualização dinamicamente
    return html.Div([
        html.Div(className="row", style={"display": "flex", "gap": "20px", "marginBottom": "20px"}, children=[
            html.Div(style={"flex": "1", "backgroundColor": "white", "padding": "20px", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"}, children=[
                html.H4("📐 Visão Geral", style={"color": "#343a40", "borderBottom": "1px solid #dee2e6", "paddingBottom": "8px"}),
                html.P(f"Linhas Originais: {df.shape[0]} | Linhas Pós-Limpeza: {df_limpo.shape[0]}"),
                html.P(f"Colunas Detetadas: {df_limpo.shape[1]}"),
                html.P(f"Variáveis Numéricas: {', '.join(resultado_analise['colunas_numericas'])}"),
                html.P(f"Variáveis Categóricas: {', '.join(resultado_analise['colunas_categoricas'])}")
            ]),
        ]),

        # Grid de Gráficos Interativos
        html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"}, children=[
            html.Div(style={"backgroundColor": "white", "padding": "15px", "borderRadius": "8px"}, children=[
                dcc.Graph(figure=graficos["histograma"]) if "histograma" in graficos else "Sem dados numéricos"
            ]),
            html.Div(style={"backgroundColor": "white", "padding": "15px", "borderRadius": "8px"}, children=[
                dcc.Graph(figure=graficos["barras"]) if "barras" in graficos else "Sem dados categóricos/numéricos"
            ]),
        ])
    ])

if __name__ == "__main__":
    app.run_server(debug=True)

    