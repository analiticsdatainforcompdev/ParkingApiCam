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

# Remove .venv se existir
if [ -d "$VENV_NAME" ]; then
    echo "🗑️  Ambiente virtual existente encontrado. Removendo..."
    rm -rf "$VENV_NAME"
fi

# Cria novo .venv
echo "📂 Criando novo ambiente virtual..."
python3 -m venv "$VENV_NAME"

# Ativa
echo "🔌 Ativando ambiente..."
source "$VENV_NAME/bin/activate"

# Flags para ignorar o bloqueio de SSL legado do Python 3.5
PIP_FLAGS="--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host www.piwheels.org"

if [ -f "requirements.txt" ]; then
    echo "📄 Instalando dependências do requirements.txt..."
    pip install $PIP_FLAGS -r requirements.txt
else
    echo "⚠️  requirements.txt não encontrado. Instalando dependências padrão..."
    # Nota: python-dotenv fixado na 0.18.0 para garantir compatibilidade com Python 3.5
    pip install $PIP_FLAGS python-dotenv==0.18.0 mysql-connector-python pika PyJWT requests cryptography flask flask-cors
fi

echo ""
echo "✅ Instalação concluída! Iniciando aplicação..."
echo "=========================================="

# Executa aplicação
python3 app.py