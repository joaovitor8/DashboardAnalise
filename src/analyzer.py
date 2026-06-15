import pandas as pd


"""
  Análise robusta com guards para todos os casos extremos:
  - CSV só com texto (colunas_numericas vazia)
  - Coluna com variância zero (correlação retorna NaN)
  - DataFrame com 0 linhas após limpeza
"""


def analyze(df: pd.DataFrame) -> dict:
  colunas_numericas = df.select_dtypes(include="number").columns.tolist()
  colunas_categoricas = df.select_dtypes(include="object").columns.tolist()


  # ── Resumo estatístico ───────────────────────────────────────────────────
  if colunas_numericas and not df.empty:
    try:
      resumo_estatistico = df[colunas_numericas].describe()
    except Exception:
      resumo_estatistico = None
  else:
    resumo_estatistico = None


  # ── Top valores categóricos ──────────────────────────────────────────────
  top_valores = {}
  for col in colunas_categoricas:
    try:
      top_valores[col] = df[col].value_counts().head(5)
    except Exception:
      pass  # coluna com problema — ignora sem travar tudo


  # ── Correlação ──────────────────────────────────────────────────────────
  correlacao = None
  if len(colunas_numericas) > 1 and not df.empty:
    try:
      corr_raw = df[colunas_numericas].corr()

      # Remove colunas e linhas que ficaram totalmente NaN (variância zero)
      colunas_validas = corr_raw.columns[~corr_raw.isnull().all()].tolist()
      if len(colunas_validas) > 1:
        correlacao = corr_raw.loc[colunas_validas, colunas_validas]
      # else: menos de 2 colunas com variância → não faz sentido exibir
    except Exception:
      correlacao = None


  # ── Média por grupo ──────────────────────────────────────────────────────
  media_por_grupo = {}
  if colunas_numericas:
    for cat in colunas_categoricas:
      try:
        # Evita groupby em colunas com cardinalidade absurda (>200 grupos)
        if df[cat].nunique() > 200:
          continue
        media_por_grupo[cat] = df.groupby(cat)[colunas_numericas].mean().round(2)
      except Exception:
        pass


  return {
    "shape": df.shape,
    "colunas_numericas": colunas_numericas,
    "colunas_categoricas": colunas_categoricas,
    "resumo_estatistico": resumo_estatistico,
    "top_valores": top_valores,
    "correlacao": correlacao,
    "media_por_grupo": media_por_grupo,
  }

