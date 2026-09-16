FROM python:3.11-slim

# Evita criação de arquivos .pyc e ativa buffer de saída imediato
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Instala ferramentas essenciais do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instala dependências Python primeiro para aproveitar o cache de camadas
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copia o código da aplicação
COPY . .

# Comando padrão
CMD ["python", "gatekeeper.py"]
