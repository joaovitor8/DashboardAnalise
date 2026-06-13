import pandas as pd

def inspect_data(df: pd.DataFrame) -> None:
  print("-" * 100)
  print("INSPEÇÃO DOS DADOS")
  print("-" * 100)

  print(f"{df.shape[0]} linhas x {df.shape[1]} colunas")
  print("-" * 40)

  print(df.head(10))
  print("-" * 40)

  print(df.shape)
  print("-" *40)

  print(df.describe())
  print("-" *40)
  
  print(df.shape)
  print("-" *40)


  print("Tipos de dados:")
  print(df.dtypes.to_string())

  print("Valores nulos por coluna:")
  nulos = df.isnull().sum()
  percentual = (nulos / len(df) * 100).round(1)
  relatorio = pd.DataFrame({"Nulos": nulos, "Percentual (%)": percentual})
  print(relatorio[relatorio["Nulos"] > 0].to_string() if nulos.sum() > 0 else "  Nenhum valor nulo!")

  print(f"Duplicatas: {df.duplicated().sum()}")

  print("Resumo estatístico:")
  print(df.describe().round(2).to_string())


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    print("\n🧹 LIMPEZA DOS DADOS")
    print("-" * 40)

    # 1. Remover duplicatas
    antes = df.shape[0]
    df.drop_duplicates(inplace=True)
    removidas = antes - df.shape[0]
    print(f"  Duplicatas removidas: {removidas}")

    # 2. Nulos numéricos → média
    for col in df.select_dtypes(include="number").columns:
        qtd = df[col].isnull().sum()
        if qtd > 0:
            df[col] = df[col].fillna(df[col].mean())
            print(f"  '{col}': {qtd} nulos preenchidos com média ({df[col].mean():.2f})")

    # 3. Nulos categóricos → "Não informado"
    for col in df.select_dtypes(include="object").columns:
        qtd = df[col].isnull().sum()
        if qtd > 0:
            df[col] = df[col].fillna("Não informado")
            print(f"  '{col}': {qtd} nulos preenchidos com 'Não informado'")

    # 4. Padronizar texto
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip().str.title()

    print("\n✅ Limpeza concluída!")
    return df