import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def gerar_graficos(df: pd.DataFrame, output_dir: str = "output") -> None:

    # Cria a pasta output se não existir
    Path(output_dir).mkdir(exist_ok=True)

    colunas_numericas = df.select_dtypes(include="number").columns.tolist()
    colunas_categoricas = df.select_dtypes(include="object").columns.tolist()

    # Cria uma figura com 4 subplots (2 linhas x 2 colunas)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Dashboard de Análise de Dados", fontsize=16, fontweight="bold")


    # --- Gráfico 1: Histograma
    if colunas_numericas:
        col = colunas_numericas[0]
        axes[0, 0].hist(df[col].dropna(), bins=10, color="#4C72B0", edgecolor="white")
        axes[0, 0].set_title(f"Distribuição: {col}")
        axes[0, 0].set_xlabel(col)
        axes[0, 0].set_ylabel("Frequência")


    # --- Gráfico 2: Barras
    if colunas_numericas and colunas_categoricas:
        col_num = colunas_numericas[0]
        col_cat = colunas_categoricas[0]
        media = df.groupby(col_cat)[col_num].mean().sort_values()
        media.plot(kind="bar", ax=axes[0, 1], color="#DD8452", edgecolor="white")
        axes[0, 1].set_title(f"Média de {col_num} por {col_cat}")
        axes[0, 1].set_xlabel(col_cat)
        axes[0, 1].set_ylabel(f"Média de {col_num}")
        axes[0, 1].tick_params(axis="x", rotation=45)


    # --- Gráfico 3: Scatter
    if len(colunas_numericas) >= 2:
        x = colunas_numericas[0]
        y = colunas_numericas[1]
        axes[1, 0].scatter(df[x], df[y], color="#55A868", alpha=0.7, edgecolors="white")
        axes[1, 0].set_title(f"Correlação: {x} vs {y}")
        axes[1, 0].set_xlabel(x)
        axes[1, 0].set_ylabel(y)


    # --- Gráfico 4: Pizza
    if colunas_categoricas:
        col = colunas_categoricas[0]
        contagem = df[col].value_counts()
        axes[1, 1].pie(
            contagem,
            labels=contagem.index,
            autopct="%1.1f%%",
            startangle=90,
            colors=["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B2"],
        )
        axes[1, 1].set_title(f"Distribuição: {col}")


    plt.tight_layout()
    caminho = f"{output_dir}/dashboard.png"
    plt.savefig(caminho, dpi=150)
    plt.close()
    print(f"\n✅ Dashboard salvo em: {caminho}")
    