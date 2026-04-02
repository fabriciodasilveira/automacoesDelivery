# Usa uma imagem estável e leve do Python
FROM python:3.9-slim

# Define o diretório de trabalho
WORKDIR /app

# Instala apenas o essencial para o Python e limpeza de cache
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia os requisitos e instala as bibliotecas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY app.py .

# Expõe a porta do Streamlit
EXPOSE 8501

# Comando para rodar a aplicação
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]