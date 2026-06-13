import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ── Detecção adaptativa ──────────────────────────────────────────────────────

def detectar_capacidades(df: pd.DataFrame) -> dict:
    """
    Analisa o DataFrame e retorna quais gráficos fazem sentido.
    Substitui a lógica hardcoded de sempre pegar coluna[0].
    """
    numericas = df.select_dtypes(include="number").columns.tolist()
    categoricas = df.select_dtypes(include="object").columns.tolist()

    # Filtra categóricas com cardinalidade razoável para gráficos
    # (colunas com 100+ categorias únicas viram bagunça em pizza/barras)
    categoricas_uteis = [
        col for col in categoricas
        if df[col].nunique() <= 30
    ]

    return {
        "numericas": numericas,
        "categoricas": categoricas,
        "categoricas_uteis": categoricas_uteis,
        "tem_histograma":    len(numericas) >= 1,
        "tem_scatter":       len(numericas) >= 2,
        "tem_heatmap":       len(numericas) >= 2,
        "tem_barras":        len(numericas) >= 1 and len(categoricas_uteis) >= 1,
        "tem_boxplot":       len(numericas) >= 1 and len(categoricas_uteis) >= 1,
        "tem_pizza":         len(categoricas_uteis) >= 1,
    }


# ── Funções de gráfico individuais ──────────────────────────────────────────
# Cada função recebe as colunas escolhidas pelo usuário — sem hardcode.

def gerar_histograma(df: pd.DataFrame, col: str, bins: int = 20):
    return px.histogram(
        df, x=col,
        nbins=bins,
        title=f"Distribuição — {col}",
        labels={col: col, "count": "Frequência"},
        color_discrete_sequence=["#4C72B0"],
        template="plotly_white",
    )


def gerar_scatter(df: pd.DataFrame, x: str, y: str, cor: str | None = None):
    return px.scatter(
        df, x=x, y=y,
        color=cor,
        title=f"Dispersão — {x} vs {y}",
        opacity=0.7,
        template="plotly_white",
    )


def gerar_heatmap_correlacao(df: pd.DataFrame, colunas: list[str] | None = None):
    subset = df[colunas] if colunas else df.select_dtypes(include="number")
    corr = subset.corr().round(2)
    return px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1,
        title="Correlação entre variáveis numéricas",
        template="plotly_white",
    )


def gerar_barras(df: pd.DataFrame, col_cat: str, col_num: str):
    media = (
        df.groupby(col_cat)[col_num]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    return px.bar(
        media, x=col_cat, y=col_num,
        title=f"Média de {col_num} por {col_cat}",
        color_discrete_sequence=["#DD8452"],
        labels={col_num: f"Média de {col_num}", col_cat: col_cat},
        template="plotly_white",
    )


def gerar_boxplot(df: pd.DataFrame, col_cat: str, col_num: str):
    return px.box(
        df, x=col_cat, y=col_num,
        color=col_cat,
        title=f"Distribuição de {col_num} por {col_cat}",
        template="plotly_white",
    )


def gerar_pizza(df: pd.DataFrame, col: str, top_n: int = 8):
    contagem = df[col].value_counts().head(top_n)
    return px.pie(
        values=contagem.values,
        names=contagem.index,
        title=f"Distribuição — {col} (top {top_n})",
        template="plotly_white",
    )