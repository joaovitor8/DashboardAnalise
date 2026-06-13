import pandas as pd


def analyze(df: pd.DataFrame) -> dict:
    """
    Lógica original preservada.
    Retorna dicionário — quem renderiza é o main.py via Dash.
    """
    colunas_numericas = df.select_dtypes(include="number").columns.tolist()
    colunas_categoricas = df.select_dtypes(include="object").columns.tolist()

    return {
        "shape": df.shape,
        "colunas_numericas": colunas_numericas,
        "colunas_categoricas": colunas_categoricas,
        "resumo_estatistico": df[colunas_numericas].describe() if colunas_numericas else None,
        "top_valores": {
            col: df[col].value_counts().head(5)
            for col in colunas_categoricas
        },
        "correlacao": (
            df[colunas_numericas].corr()
            if len(colunas_numericas) > 1 else None
        ),
        "media_por_grupo": {
            cat: df.groupby(cat)[colunas_numericas].mean().round(2)
            for cat in colunas_categoricas
            if colunas_numericas
        },
    }
