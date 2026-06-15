import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


"""
domain_analysis.py
Gera KPIs, gráficos e insights automáticos para cada domínio detectado.
Cada função de análise é tolerante a falhas: retorna o que conseguir
mesmo se algumas colunas esperadas não existirem ou tiverem dados ruins.
"""


# ── Placeholder de erro reutilizado de charts.py ────────────────────────────
def _fig_vazio(msg: str) -> go.Figure:
  fig = go.Figure()
  fig.add_annotation(
    text=msg, xref="paper", yref="paper", x=0.5, y=0.5,
    showarrow=False, font=dict(size=13, color="#6c757d"), align="center",
  )
  fig.update_layout(
    template="plotly_white",
    xaxis=dict(visible=False), yaxis=dict(visible=False),
    margin=dict(t=40, b=20, l=20, r=20), height=280,
  )
  return fig


# ── KPI helper ───────────────────────────────────────────────────────────────
def _kpi(label: str, valor: str, destaque: bool = False) -> dict:
  return {"label": label, "valor": valor, "destaque": destaque}


# ── Dispatcher principal ─────────────────────────────────────────────────────
def analisar_dominio(df: pd.DataFrame, deteccao: dict) -> dict:
  """
  Roteia para a análise correta e adiciona série temporal se houver data.
  Retorna {"kpis": [...], "graficos": [...], "insights": [...]}
  """
  dominio = deteccao.get("dominio", "generico")
  roles = deteccao.get("roles", {})
  colunas_data = deteccao.get("colunas_data", [])

  resultado = {"kpis": [], "graficos": [], "insights": []}

  analisadores = {
    "financeiro": _analisar_financeiro,
    "rh":         _analisar_rh,
    "vendas":     _analisar_vendas,
  }

  if dominio in analisadores:
    resultado = analisadores[dominio](df, roles)

  # Série temporal é transversal — aparece em qualquer domínio que tenha data
  if colunas_data:
    figs_tempo = _analisar_serie_temporal(df, colunas_data)
    resultado["graficos"].extend(figs_tempo)

  return resultado


# ── Financeiro ───────────────────────────────────────────────────────────────
def _analisar_financeiro(df: pd.DataFrame, roles: dict) -> dict:
  kpis, graficos, insights = [], [], []

  receita_col = _col_valida(df, roles, "receita", "preco")
  custo_col   = _col_valida(df, roles, "custo")
  margem_col  = _col_valida(df, roles, "margem")
  lucro_col   = _col_valida(df, roles, "lucro")

  # KPIs de receita
  if receita_col:
    total = df[receita_col].sum()
    media = df[receita_col].mean()
    kpis.append(_kpi("Receita Total",  f"R$ {total:,.2f}", destaque=True))
    kpis.append(_kpi("Ticket Médio",   f"R$ {media:,.2f}"))

    graficos.append(px.histogram(
      df, x=receita_col, nbins=20,
      title=f"Distribuição de {receita_col}",
      color_discrete_sequence=["#2E86AB"], template="plotly_white",
    ))

  # Receita vs Custo → calcula lucro implícito
  if receita_col and custo_col:
    try:
      tot_rec = df[receita_col].sum()
      tot_cus = df[custo_col].sum()
      lucro   = tot_rec - tot_cus
      margem  = (lucro / tot_rec * 100) if tot_rec > 0 else 0

      kpis.append(_kpi("Custo Total", f"R$ {tot_cus:,.2f}"))
      kpis.append(_kpi("Lucro Calculado", f"R$ {lucro:,.2f}", destaque=True))
      kpis.append(_kpi("Margem", f"{margem:.1f}%"))

      cmp = pd.DataFrame({
        "Métrica": [receita_col, custo_col, "Lucro"],
        "Valor":   [tot_rec,     tot_cus,    lucro],
      })
      graficos.append(px.bar(
        cmp, x="Métrica", y="Valor",
        title="Receita × Custo × Lucro",
        color="Métrica",
        color_discrete_sequence=["#2E86AB", "#E63946", "#3BB273"],
        template="plotly_white",
      ))

      if lucro < 0:
        insights.append("⚠️ Prejuízo identificado: custos superam a receita.")
      if 0 <= margem < 10:
        insights.append("⚠️ Margem abaixo de 10% — avaliar eficiência operacional.")
    except Exception:
      pass

  # Margem direta (se coluna existir)
  if margem_col:
    try:
      media_m = df[margem_col].mean()
      kpis.append(_kpi("Margem Média", f"{media_m:.1f}%"))
      graficos.append(px.histogram(
        df, x=margem_col, nbins=15,
        title=f"Distribuição de {margem_col}",
        color_discrete_sequence=["#3BB273"], template="plotly_white",
      ))
    except Exception:
      pass

  return {"kpis": kpis, "graficos": graficos, "insights": insights}


# ── RH ───────────────────────────────────────────────────────────────────────
def _analisar_rh(df: pd.DataFrame, roles: dict) -> dict:
  kpis, graficos, insights = [], [], []

  salario_col = _col_valida(df, roles, "salario")
  dept_col    = _col_valida(df, roles, "departamento")
  genero_col  = _col_valida(df, roles, "genero")
  idade_col   = _col_valida(df, roles, "idade")
  cargo_col   = _col_valida(df, roles, "cargo")

  kpis.append(_kpi("Total de Funcionários", f"{len(df):,}", destaque=True))

  if salario_col:
    try:
      media   = df[salario_col].mean()
      mediana = df[salario_col].median()
      kpis.append(_kpi("Salário Médio",   f"R$ {media:,.2f}", destaque=True))
      kpis.append(_kpi("Salário Mediano", f"R$ {mediana:,.2f}"))

      graficos.append(px.histogram(
        df, x=salario_col, nbins=20,
        title=f"Distribuição de {salario_col}",
        color_discrete_sequence=["#6A4C93"], template="plotly_white",
      ))

      if media > mediana * 1.3:
        insights.append(
            "📊 Média salarial muito acima da mediana — "
            "existem outliers altos distorcendo a média."
          )
    except Exception:
      pass

  if salario_col and dept_col:
    try:
      por_dept = (
        df.groupby(dept_col)[salario_col]
        .mean().sort_values(ascending=False).reset_index()
      )
      graficos.append(px.bar(
        por_dept, x=dept_col, y=salario_col,
        title=f"Salário Médio por {dept_col}",
        color_discrete_sequence=["#6A4C93"], template="plotly_white",
      ))
    except Exception:
      pass

  if dept_col:
    try:
      headcount = df[dept_col].value_counts().reset_index()
      headcount.columns = [dept_col, "Headcount"]
      graficos.append(px.bar(
        headcount, x=dept_col, y="Headcount",
        title=f"Headcount por {dept_col}",
        color_discrete_sequence=["#1982C4"], template="plotly_white",
      ))
      kpis.append(_kpi("Departamentos", str(df[dept_col].nunique())))
    except Exception:
      pass

  if genero_col:
    try:
      dist = df[genero_col].value_counts()
      graficos.append(px.pie(
        values=dist.values, names=dist.index,
        title=f"Distribuição por {genero_col}", template="plotly_white",
      ))
    except Exception:
      pass

  if idade_col:
    try:
      graficos.append(px.histogram(
        df, x=idade_col, nbins=15,
        title=f"Distribuição de {idade_col}",
        color_discrete_sequence=["#FF595E"], template="plotly_white",
      ))
      kpis.append(_kpi("Idade Média", f"{df[idade_col].mean():.1f} anos"))
    except Exception:
      pass

  return {"kpis": kpis, "graficos": graficos, "insights": insights}


# ── Vendas ───────────────────────────────────────────────────────────────────
def _analisar_vendas(df: pd.DataFrame, roles: dict) -> dict:
  kpis, graficos, insights = [], [], []

  produto_col = _col_valida(df, roles, "produto")
  cliente_col = _col_valida(df, roles, "cliente")
  qtd_col     = _col_valida(df, roles, "quantidade")
  cat_col     = _col_valida(df, roles, "categoria")
  desc_col    = _col_valida(df, roles, "desconto")

  # Detecta coluna de valor — pode não estar mapeada diretamente
  receita_col = _detectar_coluna_valor(df)

  kpis.append(_kpi("Total de Pedidos", f"{len(df):,}", destaque=True))

  if receita_col:
    total  = df[receita_col].sum()
    ticket = df[receita_col].mean()
    kpis.append(_kpi("Receita Total", f"R$ {total:,.2f}", destaque=True))
    kpis.append(_kpi("Ticket Médio",  f"R$ {ticket:,.2f}"))

  if produto_col and receita_col:
    try:
      top = (
        df.groupby(produto_col)[receita_col]
        .sum().sort_values(ascending=False).head(10).reset_index()
      )
      graficos.append(px.bar(
        top, x=produto_col, y=receita_col,
        title=f"Top 10 {produto_col} por Receita",
        color_discrete_sequence=["#E76F51"], template="plotly_white",
      ))
    except Exception:
      pass

  if cat_col:
    try:
      valores  = df.groupby(cat_col)[receita_col].sum() if receita_col else df[cat_col].value_counts()
      graficos.append(px.pie(
        values=valores.values, names=valores.index,
        title=f"Receita por {cat_col}", template="plotly_white",
      ))
    except Exception:
      pass

  if cliente_col and receita_col:
    try:
      top_cli = (
        df.groupby(cliente_col)[receita_col]
        .sum().sort_values(ascending=False).head(10).reset_index()
      )
      graficos.append(px.bar(
        top_cli, x=cliente_col, y=receita_col,
        title=f"Top 10 Clientes por Receita",
        color_discrete_sequence=["#4ECDC4"], template="plotly_white",
      ))
    except Exception:
      pass

  if qtd_col:
    try:
      kpis.append(_kpi("Unidades Vendidas", f"{int(df[qtd_col].sum()):,}"))
    except Exception:
      pass

  if desc_col:
    try:
      media_desc = df[desc_col].mean()
      kpis.append(_kpi("Desconto Médio", f"{media_desc:.1f}%"))
      if media_desc > 20:
        insights.append(
          "⚠️ Desconto médio acima de 20% — pode estar comprimindo a margem."
        )
    except Exception:
      pass

  return {"kpis": kpis, "graficos": graficos, "insights": insights}


# ── Série temporal (transversal) ─────────────────────────────────────────────
def _analisar_serie_temporal(df: pd.DataFrame, colunas_data: list[str]) -> list:
  """Gráfico de linha temporal — funciona em qualquer domínio com data."""
  col_data = colunas_data[0]
  numericas = df.select_dtypes(include="number").columns.tolist()

  if not numericas:
    return []

  try:
    df = df.copy()
    df[col_data] = pd.to_datetime(df[col_data], errors="coerce")
    df = df.dropna(subset=[col_data])
    if df.empty:
      return []

    col_valor = numericas[0]
    serie = df[[col_data, col_valor]].sort_values(col_data)

    # Agrega por mês se houver muitos pontos (>60)
    if len(serie) > 60:
      serie = serie.copy()
      serie[col_data] = serie[col_data].dt.to_period("M").dt.to_timestamp()
      serie = serie.groupby(col_data)[col_valor].sum().reset_index()

    fig = px.line(
      serie, x=col_data, y=col_valor,
      title=f"Evolução Temporal — {col_valor}",
      markers=True, template="plotly_white",
      color_discrete_sequence=["#2D6A4F"],
    )
    fig.update_traces(line=dict(width=2))
    return [fig]

  except Exception:
    return []


# ── Helpers internos ─────────────────────────────────────────────────────────
def _col_valida(df: pd.DataFrame, roles: dict, *nomes_roles: str) -> str | None:
	"""Retorna a primeira coluna mapeada que realmente existe no df."""
	for role in nomes_roles:
		col = roles.get(role)
		if col and col in df.columns:
			return col
	return None


def _detectar_coluna_valor(df: pd.DataFrame) -> str | None:
	"""
	Heurística para encontrar coluna de valor de venda quando não está mapeada.
	Procura por palavras-chave numéricas nas colunas.
	"""
	keywords = ["valor", "venda", "receita", "total", "preco", "price", "amount"]
	for col in df.columns:
		col_norm = col.lower()
		if (any(kw in col_norm for kw in keywords)
				and pd.api.types.is_numeric_dtype(df[col])):
			return col
	# Fallback: primeira coluna numérica
	nums = df.select_dtypes(include="number").columns.tolist()
	return nums[0] if nums else None

