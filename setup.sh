#!/bin/bash
set -e

echo "=========================================="
echo "🔧 Instalador + Executor do Projeto"
echo "=========================================="

VENV_NAME=".venv"

# Verifica Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado!"
    exit 1
fi

# Cria .venv se não existir
if [ ! -d "$VENV_NAME" ]; then
    echo "📂 Criando ambiente virtual..."
    python3 -m venv "$VENV_NAME"
else
    echo "✅ Ambiente virtual já existe"
fi

# Ativa
echo "🔌 Ativando ambiente..."
source "$VENV_NAME/bin/activate"

# Atualiza pip e instala dependências
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install python-dotenv mysql-connector-python pika PyJWT requests cryptography flask flask-cors
fi

echo ""
echo "✅ Instalação concluída! Iniciando aplicação..."
echo "=========================================="

# Executa a aplicação
python3 app.py