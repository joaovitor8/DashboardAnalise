import pandas as pd
import tkinter as tk
from pathlib import Path
from tkinter import filedialog


def load_file():
  tk.Tk().withdraw()
  caminho = filedialog.askopenfilename(
    title="Selecione o arquivo",
    filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")]
  )

  if not caminho:
    print("Nenhum arquivo selecionado.")
    print("-" * 40)
    return None

  path = Path(caminho)
  extensao = path.suffix.lower()

  if extensao == ".csv":
    df = pd.read_csv(path)
  elif extensao in [".xlsx", ".xls"]:
    df = pd.read_excel(path)
  else:
    print(f"Formato não suportado: {extensao}")
    return None

  return df
