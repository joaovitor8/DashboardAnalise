import argparse
from src.loader import load_file
from src.clean import inspect_data, clean_data
from src.analyzer import analyze, print_analise
from src.charts import gerar_graficos


def main():
  print("-" * 100)
  print("Dashboard de Análise de Dados")
  print("-" * 100)

  df = None

  while True:
    try:
      opcoes = int(input("Oque deseja fazer? \n[1] Carregar Arquivo \n[2] Inspecionar Dados \n[3] Limpar Dados \n[4] Análise \n[5] Gerar Gráficos \n[6] Sair \nEscolha: "))
      print("-" * 40)
    except ValueError:
      print("Digite apenas números!")
      continue

    if opcoes == 1:
      df = load_file()
      if df is not None:
        print(f"Arquivo carregado com sucesso! ({df.shape[0]} linhas x {df.shape[1]} colunas)")
        print("-" * 40)
    elif opcoes == 2:
      if df is None:
        print("Carregue um arquivo")
        print("-" * 40)
      else:
        inspect_data(df)
    elif opcoes == 3:
      if df is None:
        print("Carregue um arquivo")
        print("-" * 40)
      else:
        df = clean_data(df)

    elif opcoes == 4:
      if df is None:
        print("Carregue um arquivo")
      else:
        resultado = analyze(df)
        print_analise(resultado)

    elif opcoes == 5:
      if df is None:
        print("Carregue um arquivo")
      else:
        gerar_graficos(df)

    elif opcoes == 6:
      print("Saindo...")
      break

    else:
      print("Opção inválida!")

  print("-" * 60)


if __name__ == "__main__":
  main()

