import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ── Placeholder: retornado quando um gráfico não pode ser gerado ─────────────

def _grafico_vazio(motivo: str) -> go.Figure:
    """
    Retorna um gráfico em branco com mensagem explicativa.
    Usado em vez de lançar exceção — o callback continua rodando.
    """
    fig = go.Figure()
    fig.add_annotation(
        text=motivo,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(size=13, color="#6c757d"),
        align="center",
    )
    fig.update_layout(
        template="plotly_white",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(t=40, b=20, l=20, r=20),
        height=300,
    )
    return fig


# ── Detecção adaptativa ──────────────────────────────────────────────────────

def detectar_capacidades(df: pd.DataFrame) -> dict:
    numericas = df.select_dtypes(include="number").columns.tolist()
    categoricas = df.select_dtypes(include="object").columns.tolist()

    # Categóricas com cardinalidade razoável (pizza/barras com 200+ categorias = ilegível)
    categoricas_uteis = [col for col in categoricas if df[col].nunique() <= 30]

    return {
        "numericas": numericas,
        "categoricas": categoricas,
        "categoricas_uteis": categoricas_uteis,
        "tem_histograma": len(numericas) >= 1,
        "tem_scatter":    len(numericas) >= 2,
        "tem_heatmap":    len(numericas) >= 2,
        "tem_barras":     len(numericas) >= 1 and len(categoricas_uteis) >= 1,
        "tem_boxplot":    len(numericas) >= 1 and len(categoricas_uteis) >= 1,
        "tem_pizza":      len(categoricas_uteis) >= 1,
    }


# ── Funções de gráfico — cada uma com try/except próprio ────────────────────

def gerar_histograma(df: pd.DataFrame, col: str, bins: int = 20) -> go.Figure:
    try:
        dados = df[col].dropna()
        if dados.empty:
            return _grafico_vazio(f"'{col}' não tem valores válidos para histograma")
        if dados.nunique() == 1:
            return _grafico_vazio(f"'{col}' tem apenas um valor único — histograma sem sentido")
        return px.histogram(
            df, x=col, nbins=bins,
            title=f"Distribuição — {col}",
            labels={col: col, "count": "Frequência"},
            color_discrete_sequence=["#4C72B0"],
            template="plotly_white",
        )
    except Exception as e:
        return _grafico_vazio(f"Não foi possível gerar histograma de '{col}': {e}")


def gerar_scatter(df: pd.DataFrame, x: str, y: str, cor: str | None = None) -> go.Figure:
    try:
        subset = df[[x, y]].dropna()
        if subset.empty:
            return _grafico_vazio(f"Sem dados válidos para '{x}' vs '{y}'")
        if len(subset) < 2:
            return _grafico_vazio(f"Poucos pontos para dispersão ({len(subset)} linha(s))")
        return px.scatter(
            df, x=x, y=y, color=cor,
            title=f"Dispersão — {x} vs {y}",
            opacity=0.7,
            template="plotly_white",
        )
    except Exception as e:
        return _grafico_vazio(f"Não foi possível gerar dispersão: {e}")


def gerar_heatmap_correlacao(df: pd.DataFrame, colunas: list[str] | None = None) -> go.Figure:
    try:
        subset = df[colunas] if colunas else df.select_dtypes(include="number")
        if subset.shape[1] < 2:
            return _grafico_vazio("Necessário ao menos 2 colunas numéricas para correlação")

        corr = subset.corr().round(2)

        # Remove colunas com variância zero (correlação seria NaN)
        colunas_validas = corr.columns[~corr.isnull().all()].tolist()
        if len(colunas_validas) < 2:
            return _grafico_vazio(
                "Correlação não pôde ser calculada — "
                "verifique se as colunas têm variação suficiente"
            )

        corr_limpo = corr.loc[colunas_validas, colunas_validas]
        return px.imshow(
            corr_limpo,
            text_auto=True,
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            title="Correlação entre variáveis numéricas",
            template="plotly_white",
        )
    except Exception as e:
        return _grafico_vazio(f"Não foi possível gerar heatmap de correlação: {e}")


def gerar_barras(df: pd.DataFrame, col_cat: str, col_num: str) -> go.Figure:
    try:
        subset = df[[col_cat, col_num]].dropna()
        if subset.empty:
            return _grafico_vazio(f"Sem dados válidos para '{col_cat}' e '{col_num}'")

        media = subset.groupby(col_cat)[col_num].mean().sort_values(ascending=False).reset_index()
        if media.empty:
            return _grafico_vazio(f"Nenhum grupo encontrado em '{col_cat}'")

        return px.bar(
            media, x=col_cat, y=col_num,
            title=f"Média de {col_num} por {col_cat}",
            color_discrete_sequence=["#DD8452"],
            labels={col_num: f"Média de {col_num}", col_cat: col_cat},
            template="plotly_white",
        )
    except Exception as e:
        return _grafico_vazio(f"Não foi possível gerar barras: {e}")


def gerar_boxplot(df: pd.DataFrame, col_cat: str, col_num: str) -> go.Figure:
    try:
        subset = df[[col_cat, col_num]].dropna()
        if subset.empty:
            return _grafico_vazio(f"Sem dados válidos para '{col_cat}' e '{col_num}'")
        return px.box(
            df, x=col_cat, y=col_num,
            color=col_cat,
            title=f"Distribuição de {col_num} por {col_cat}",
            template="plotly_white",
        )
    except Exception as e:
        return _grafico_vazio(f"Não foi possível gerar box plot: {e}")


def gerar_pizza(df: pd.DataFrame, col: str, top_n: int = 8) -> go.Figure:
    try:
        dados = df[col].dropna()
        if dados.empty:
            return _grafico_vazio(f"'{col}' não tem valores válidos para gráfico de pizza")

        contagem = dados.value_counts().head(top_n)
        if contagem.empty:
            return _grafico_vazio(f"Nenhuma categoria encontrada em '{col}'")

        return px.pie(
            values=contagem.values,
            names=contagem.index,
            title=f"Distribuição — {col} (top {top_n})",
            template="plotly_white",
        )
    except Exception as e:
        return _grafico_vazio(f"Não foi possível gerar pizza: {e}")