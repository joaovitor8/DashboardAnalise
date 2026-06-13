import pandas as pd
import plotly.express as px

def gerar_graficos_interativos(df: pd.DataFrame) -> dict:
    colunas_numericas = df.select_dtypes(include="number").columns.tolist()
    colunas_categoricas = df.select_dtypes(include="object").columns.tolist()
    
    graficos = {}

    # --- Gráfico 1: Histograma
    if colunas_numericas:
        col = colunas_numericas[0]
        graficos["histograma"] = px.histogram(
            df, x=col, title=f"Distribuição: {col}", 
            template="plotly_white", color_discrete_sequence=["#4C72B0"]
        )

    # --- Gráfico 2: Barras Interativas
    if colunas_numericas and colunas_categoricas:
        col_num = colunas_numericas[0]
        col_cat = colunas_categoricas[0]
        media = df.groupby(col_cat)[col_num].mean().sort_values().reset_index()
        graficos["barras"] = px.bar(
            media, x=col_cat, y=col_num, title=f"Média de {col_num} por {col_cat}",
            template="plotly_white", color_discrete_sequence=["#DD8452"]
        )

    # --- Gráfico 3: Scatter Plot
    if len(colunas_numericas) >= 2:
        x = colunas_numericas[0]
        y = colunas_numericas[1]
        graficos["dispersion"] = px.scatter(
            df, x=x, y=y, title=f"Correlação: {x} vs {y}",
            template="plotly_white", color_discrete_sequence=["#55A868"]
        )

    return graficos

