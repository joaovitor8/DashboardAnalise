import pandas as pd


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Executa limpeza e retorna (df_limpo, lista_de_mensagens).
    SEM print() — quem exibe as mensagens é o main.py no browser.
    """
    df = df.copy()
    mensagens = []

    # 1. Remover duplicatas
    antes = df.shape[0]
    df.drop_duplicates(inplace=True)
    removidas = antes - df.shape[0]
    mensagens.append(f"Duplicatas removidas: **{removidas}**")

    # 2. Nulos numéricos → média
    for col in df.select_dtypes(include="number").columns:
        qtd = int(df[col].isnull().sum())
        if qtd > 0:
            media = round(df[col].mean(), 2)
            df[col] = df[col].fillna(df[col].mean())
            mensagens.append(f"'{col}': {qtd} nulos preenchidos com média ({media})")

    # 3. Nulos categóricos → "Não informado"
    for col in df.select_dtypes(include="object").columns:
        qtd = int(df[col].isnull().sum())
        if qtd > 0:
            df[col] = df[col].fillna("Não informado")
            mensagens.append(f"'{col}': {qtd} nulos preenchidos com 'Não informado'")

    # 4. Padronizar texto
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip().str.title()

    return df, mensagens