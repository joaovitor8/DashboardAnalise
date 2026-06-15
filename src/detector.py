import re
import unicodedata
import pandas as pd


"""
detector.py
Detecta automaticamente o domínio dos dados analisando os nomes das colunas.
Suporta: Financeiro, RH, Vendas (+ série temporal em qualquer domínio).
"""


DOMINIOS = {
  "financeiro": {
    "label": "Financeiro",
    "emoji": "💰",
    "cor": "#2E86AB",
    "descricao": "Colunas de receita, custo ou margem detectadas",
    "roles": {
      "receita":  ["receita", "revenue", "faturamento", "vendas"],
      "custo":    ["custo", "cost", "despesa", "expense", "gasto"],
      "lucro":    ["lucro", "profit", "resultado", "ganho"],
      "margem":   ["margem", "margin"],
      "preco":    ["preco", "price", "valor", "value"],
      "saldo":    ["saldo", "balance", "ativo", "passivo"],
    },
  },
  "rh": {
    "label": "Recursos Humanos",
    "emoji": "👥",
    "cor": "#6A4C93",
    "descricao": "Colunas de salário, departamento ou funcionários detectadas",
    "roles": {
      "salario":      ["salario", "salary", "remuneracao", "wage"],
      "departamento": ["departamento", "department", "setor", "area"],
      "cargo":        ["cargo", "position", "funcao", "role", "titulo"],
      "funcionario":  ["funcionario", "employee", "colaborador", "nome"],
      "genero":       ["genero", "gender", "sexo"],
      "idade":        ["idade", "age"],
    },
  },
  "vendas": {
      "label": "Vendas",
      "emoji": "🛒",
      "cor": "#E76F51",
      "descricao": "Colunas de produto, cliente ou pedidos detectadas",
      "roles": {
        "produto":    ["produto", "product", "item", "sku", "mercadoria"],
        "cliente":    ["cliente", "customer", "comprador", "buyer"],
        "quantidade": ["quantidade", "quantity", "qtd", "qtde", "units"],
        "categoria":  ["categoria", "category", "segmento"],
        "pedido":     ["pedido", "order", "compra", "purchase"],
        "desconto":   ["desconto", "discount"],
      },
  },
}

DATE_KEYWORDS = [
  "data", "date", "mes", "ano", "year", "month",
  "periodo", "period", "dia", "day", "hora", "time", "timestamp",
]


def _norm(texto: str) -> str:
  texto = texto.lower().strip()
  texto = unicodedata.normalize("NFD", texto)
  texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
  return re.sub(r"[^a-z0-9]", "", texto)


def _detectar_colunas_data(df: pd.DataFrame) -> list[str]:
  por_tipo = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
  por_nome = [
    col for col in df.columns
    if col not in por_tipo and any(kw in _norm(col) for kw in DATE_KEYWORDS)
  ]
  return por_tipo + por_nome


def _mapear_roles(df: pd.DataFrame, dominio: str) -> dict[str, str | None]:
  roles_config = DOMINIOS[dominio]["roles"]
  colunas_norm = [(col, _norm(col)) for col in df.columns]
  return {
    role: next(
      (col for col, col_n in colunas_norm if any(kw in col_n for kw in keywords)),
      None,
    )
    for role, keywords in roles_config.items()
  }


def detectar_dominio(df: pd.DataFrame) -> dict:
  """
  Analisa nomes de colunas e retorna o domínio mais provável com roles mapeados.

  Confiança:  alta (≥3 roles com match), media (2), baixa (1), nenhuma (0)
  """
  scores, roles_por_dominio = {}, {}
  for dominio in DOMINIOS:
    roles = _mapear_roles(df, dominio)
    scores[dominio] = sum(1 for v in roles.values() if v is not None)
    roles_por_dominio[dominio] = roles

  melhor = max(scores, key=scores.get)
  melhor_score = scores[melhor]
  colunas_data = _detectar_colunas_data(df)

  if melhor_score == 0:
    return {
      "dominio": "generico", "label": "Genérico",
      "emoji": "📊", "cor": "#6c757d",
      "descricao": "Nenhum domínio específico detectado",
      "confianca": "nenhuma", "roles": {},
      "colunas_data": colunas_data,
      "tem_serie_temporal": bool(colunas_data),
      "scores": scores,
    }

  cfg = DOMINIOS[melhor]
  return {
    "dominio": melhor,
    "label": cfg["label"], "emoji": cfg["emoji"],
    "cor": cfg["cor"],     "descricao": cfg["descricao"],
    "confianca": "alta" if melhor_score >= 3 else "media" if melhor_score >= 2 else "baixa",
    "roles": roles_por_dominio[melhor],
    "colunas_data": colunas_data,
    "tem_serie_temporal": bool(colunas_data),
    "scores": scores,
  }

