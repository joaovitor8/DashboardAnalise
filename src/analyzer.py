import pandas as pd


def analyze(df: pd.DataFrame) -> dict:

    colunas_numericas = df.select_dtypes(include="number").columns.tolist()
    colunas_categoricas = df.select_dtypes(include="object").columns.tolist()

    resultado = {

        # 1. Visão geral
        "shape": df.shape,
        "colunas_numericas": colunas_numericas,
        "colunas_categoricas": colunas_categoricas,

        # 2. Distribuição numérica
        "resumo_estatistico": df[colunas_numericas].describe(),

        # 3. Distribuição categórica
        "top_valores": {
            col: df[col].value_counts().head(5)
            for col in colunas_categoricas
        },

        # 4. Relações
        "correlacao": df[colunas_numericas].corr() if len(colunas_numericas) > 1 else None,

        # 5. Agrupamentos: média de cada numérica por cada categórica
        "media_por_grupo": {
            cat: df.groupby(cat)[colunas_numericas].mean()
            for cat in colunas_categoricas
        },
    }

    return resultado


def print_analise(resultado: dict) -> None:

    print("\n📐 VISÃO GERAL")
    print("-" * 40)
    print(f"  Linhas:   {resultado['shape'][0]}")
    print(f"  Colunas:  {resultado['shape'][1]}")
    print(f"  Numéricas:    {resultado['colunas_numericas']}")
    print(f"  Categóricas:  {resultado['colunas_categoricas']}")

    print("\n📊 RESUMO ESTATÍSTICO")
    print("-" * 40)
    print(resultado["resumo_estatistico"].round(2).to_string())

    print("\n🔤 TOP VALORES POR COLUNA CATEGÓRICA")
    print("-" * 40)
    for col, valores in resultado["top_valores"].items():
        print(f"\n  [{col}]")
        print(valores.to_string())

    if resultado["correlacao"] is not None:
        print("\n🔗 CORRELAÇÃO ENTRE VARIÁVEIS NUMÉRICAS")
        print("-" * 40)
        print(resultado["correlacao"].round(2).to_string())

    print("\n📦 MÉDIA POR GRUPO")
    print("-" * 40)
    for cat, tabela in resultado["media_por_grupo"].items():
        print(f"\n  Agrupado por [{cat}]:")
        print(tabela.round(2).to_string())