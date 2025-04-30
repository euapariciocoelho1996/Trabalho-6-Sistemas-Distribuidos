FROM python:3.11-slim

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia os arquivos do diretório do produtor para o contêiner
COPY . .

# Copia as dependências e instala os pacotes necessários
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Define o comando padrão para rodar o produtor
CMD ["python", "produtor.py"]
