import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pdfplumber
import pandas as pd

class ExtratorCertificadosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extrator de Certificados Lenovo")
        self.root.geometry("650x200")
        self.root.resizable(False, False)

        # Variáveis de controle
        self.pasta_alvo = ""
        self.total_arquivos = 0
        self.arquivos_processados = 0

        # Elementos da Interface
        self.lbl_instrucao = tk.Label(root, text="Selecione a pasta raiz contendo os certificados em PDF:", pady=10)
        self.lbl_instrucao.pack()

        self.btn_selecionar = tk.Button(root, text="Selecionar Pasta e Extrair", command=self.iniciar_extracao, width=30)
        self.btn_selecionar.pack(pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100, length=350, mode='determinate')
        self.progress_bar.pack(pady=15)

        self.lbl_status = tk.Label(root, text="Aguardando...", fg="gray")
        self.lbl_status.pack()

    def iniciar_extracao(self):
        # Abre o diálogo para selecionar a pasta
        self.pasta_alvo = filedialog.askdirectory(title="Selecione a pasta raiz")
        
        if not self.pasta_alvo:
            return # Usuário cancelou
        
        self.btn_selecionar.config(state=tk.DISABLED)
        self.lbl_status.config(text="Mapeando arquivos PDF...", fg="blue")
        self.progress_var.set(0)

        # Inicia a thread separada para não travar a interface
        thread = threading.Thread(target=self.processar_arquivos)
        thread.start()

    def extrair_dados_pdf(self, caminho_pdf):
        """Lê o PDF e aplica Regex para encontrar os dados"""
        dados = {
            "Nome da Pessoa": "Não encontrado",
            "Nome do Curso": "Não encontrado",
            "Código do Curso": "Não encontrado",
            "Data de Conclusão": "Não encontrado"
        }
        
        try:
            with pdfplumber.open(caminho_pdf) as pdf:
                texto = pdf.pages[0].extract_text()
                
                if texto:
                    # Regex para encontrar os padrões (ajustados para lidar com quebras de linha dinâmicas)
                    match_nome = re.search(r"Presented to\s*\n\s*(.+)", texto, re.IGNORECASE)
                    match_curso = re.search(r"Upon the successful completion of\s*\n\s*(.+?)\s*\((.*?)\)", texto, re.IGNORECASE | re.DOTALL)
                    match_data = re.search(r"Date of Completion\s*\n\s*(\d{1,2}/\d{1,2}/\d{4})", texto, re.IGNORECASE)

                    if match_nome:
                        dados["Nome da Pessoa"] = match_nome.group(1).strip()
                    if match_curso:
                        # Limpa quebras de linha no meio do nome do curso
                        nome_curso = match_curso.group(1).replace('\n', ' ').strip() 
                        dados["Nome do Curso"] = nome_curso
                        dados["Código do Curso"] = match_curso.group(2).strip()
                    if match_data:
                        dados["Data de Conclusão"] = match_data.group(1).strip()
        except Exception as e:
            print(f"Erro no arquivo {caminho_pdf}: {e}")
            
        return dados

    def processar_arquivos(self):
        lista_dados = []
        arquivos_pdf = []

        # 1. Varre as pastas recursivamente para listar todos os PDFs
        for raiz, dirs, arquivos in os.walk(self.pasta_alvo):
            for arquivo in arquivos:
                if arquivo.lower().endswith('.pdf'):
                    arquivos_pdf.append(os.path.join(raiz, arquivo))

        self.total_arquivos = len(arquivos_pdf)

        if self.total_arquivos == 0:
            self.atualizar_ui("Nenhum arquivo PDF encontrado.", 0)
            messagebox.showwarning("Aviso", "Nenhum arquivo PDF foi encontrado na pasta selecionada.")
            self.root.after(0, lambda: self.btn_selecionar.config(state=tk.NORMAL))
            return

        # 2. Processa cada arquivo e atualiza a barra de progresso
        for i, caminho_pdf in enumerate(arquivos_pdf):
            nome_arquivo = os.path.basename(caminho_pdf)
            
            # Atualiza o status na UI (usando after para ser thread-safe)
            self.root.after(0, self.atualizar_ui, f"Processando: {nome_arquivo} ({i+1}/{self.total_arquivos})", (i / self.total_arquivos) * 100)
            
            dados = self.extrair_dados_pdf(caminho_pdf)
            lista_dados.append(dados)

        # 3. Exporta para Excel
        self.root.after(0, self.atualizar_ui, "Gerando arquivo Excel...", 100)
        df = pd.DataFrame(lista_dados)
        
        caminho_excel = os.path.join(self.pasta_alvo, "Base_Certificados_Lenovo.xlsx")
        df.to_excel(caminho_excel, index=False)

        # Finaliza e avisa o usuário
        self.root.after(0, self.atualizar_ui, "Concluído!", 100)
        self.root.after(0, lambda: self.btn_selecionar.config(state=tk.NORMAL))
        messagebox.showinfo("Sucesso", f"Processamento concluído!\n{self.total_arquivos} certificados lidos.\nArquivo salvo em:\n{caminho_excel}")

    def atualizar_ui(self, texto_status, valor_progresso):
        """Atualiza os elementos da interface de forma segura"""
        self.lbl_status.config(text=texto_status)
        self.progress_var.set(valor_progresso)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExtratorCertificadosApp(root)
    root.mainloop()