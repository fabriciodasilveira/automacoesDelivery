import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def consolidar_csvs():
    # 1. Configuração da janela oculta do Tkinter para o seletor
    root = tk.Tk()
    root.withdraw()  # Esconde a janela principal do Tkinter

    # 2. Abrir seletor de arquivos (múltipla escolha)
    caminhos_arquivos = filedialog.askopenfilenames(
        title="Selecione os arquivos CSV",
        filetypes=[("Arquivos CSV", "*.csv")]
    )

    if not caminhos_arquivos:
        messagebox.showwarning("Aviso", "Nenhum arquivo foi selecionado.")
        return

    lista_dataframes = []

    try:
        # 3. Leitura e empilhamento dos dados
        for arquivo in caminhos_arquivos:
            # sep=None com engine='python' detecta automaticamente o separador (; ou ,)
            # encoding='latin1' evita erros de acentuação comuns no Excel/Windows
            df = pd.read_csv(arquivo, sep=None, engine='python', encoding='latin-1')
            
            # Adiciona o nome do arquivo para conferência
            df['Fonte'] = os.path.basename(arquivo)
            
            lista_dataframes.append(df)

        # Concatena os dados
        # O pandas tentará alinhar as colunas mesmo que os arquivos sejam um pouco diferentes
        df_final = pd.concat(lista_dataframes, ignore_index=True, sort=False)

        # 4. Salvar em Excel
        nome_saida = "consolidado_final.xlsx"
        df_final.to_excel(nome_saida, index=False, engine='openpyxl')

        messagebox.showinfo("Sucesso", f"Arquivos consolidados!\nSalvo como: {nome_saida}")

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro durante a consolidação:\n{e}")

if __name__ == "__main__":
    consolidar_csvs()