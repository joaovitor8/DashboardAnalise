import pandas as pd

# Limite: colunas com mais de X% de nulos recebem aviso em vez de preenchimento silencioso
LIMITE_NULOS_AVISO = 0.5   # 50% → aviso
LIMITE_NULOS_DROP  = 0.99  # 99% → remove a coluna automaticamente


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Limpeza robusta. Retorna (df_limpo, mensagens).

    Casos tratados que o código anterior ignorava:
    - Coluna 100% nula: mean() retorna NaN → fillna(NaN) não faz nada
    - Coluna 99%+ nula: mais prejudicial do que útil, removida com aviso
    - Coluna 50%+ nula: preenchida, mas com aviso de qualidade
    """
    df = df.copy()
    mensagens = []

    # ── 1. Duplicatas ────────────────────────────────────────────────────────
    antes = df.shape[0]
    df.drop_duplicates(inplace=True)
    removidas = antes - df.shape[0]
    mensagens.append(f"Duplicatas removidas: {removidas}")

    # ── 2. Colunas com nulos críticos (≥99%) → remove antes de qualquer coisa
    colunas_removidas = []
    for col in df.columns:
        pct_nulo = df[col].isnull().mean()
        if pct_nulo >= LIMITE_NULOS_DROP:
            colunas_removidas.append(col)

    if colunas_removidas:
        df.drop(columns=colunas_removidas, inplace=True)
        mensagens.append(
            f"⚠️ Colunas removidas (≥99% nulos): {', '.join(colunas_removidas)}"
        )

    # ── 3. Nulos numéricos → média (com guarda para NaN) ────────────────────
    for col in df.select_dtypes(include="number").columns:
        qtd = int(df[col].isnull().sum())
        if qtd == 0:
            continue

        pct = df[col].isnull().mean()
        media = df[col].mean()  # pode ser NaN se todos os valores são nulos

        if pd.isna(media):
            # Coluna 100% nula: fillna(NaN) não faria nada — avisa e pula
            mensagens.append(
                f"⚠️ '{col}': 100% nulos — não foi possível calcular média, coluna mantida vazia"
            )
            continue

        df[col] = df[col].fillna(media)

        if pct >= LIMITE_NULOS_AVISO:
            mensagens.append(
                f"⚠️ '{col}': {pct:.0%} nulos preenchidos com média ({media:.2f}) "
                f"— qualidade dos dados baixa"
            )
        else:
            mensagens.append(f"'{col}': {qtd} nulos preenchidos com média ({media:.2f})")

    # ── 4. Nulos categóricos → "Não informado" ──────────────────────────────
    for col in df.select_dtypes(include="object").columns:
        qtd = int(df[col].isnull().sum())
        if qtd > 0:
            pct = df[col].isnull().mean()
            df[col] = df[col].fillna("Não informado")
            if pct >= LIMITE_NULOS_AVISO:
                mensagens.append(
                    f"⚠️ '{col}': {pct:.0%} nulos preenchidos com 'Não informado' "
                    f"— qualidade dos dados baixa"
                )
            else:
                mensagens.append(f"'{col}': {qtd} nulos preenchidos com 'Não informado'")

    # ── 5. Padronizar texto ──────────────────────────────────────────────────
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip().str.title()

    return df, mensagens