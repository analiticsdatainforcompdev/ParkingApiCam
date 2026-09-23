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

# Cria novo .venv com herança de sistema
echo "📂 Criando novo ambiente virtual..."
python3 -m venv --system-site-packages "$VENV_NAME"

# Define o caminho absoluto do interpretador Python interno
PYTHON_BIN="$VENV_NAME/bin/python"

# Flags para ignorar o bloqueio de SSL legado e forçar pacotes binários
PIP_FLAGS="--trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host www.piwheels.org --only-binary=:all:"

if [ -f "requirements.txt" ]; then
    echo "📄 Instalando dependências do requirements.txt..."
    "$PYTHON_BIN" -m pip install $PIP_FLAGS -r requirements.txt
else
    echo "⚠️  requirements.txt não encontrado. Instalando dependências padrão..."
    "$PYTHON_BIN" -m pip install $PIP_FLAGS python-dotenv==0.18.0 PyMySQL==0.9.3 pika==1.1.0 PyJWT==1.7.1 requests==2.25.1 Flask==1.1.2 Flask-CORS==3.0.10
fi

echo ""
echo "✅ Instalação concluída! Iniciando aplicação..."
echo "=========================================="

# Executa aplicação usando o python do ambiente virtual
"$PYTHON_BIN" cam.py