#!/bin/bash

# Interrompe o script caso ocorra algum erro
set -e

echo "==> Atualizando o sistema e instalando dependências..."
sudo apt update && sudo apt upgrade -y
sudo apt install curl gnupg apt-transport-https -y

echo "==> Configurando repositórios oficiais do Erlang e RabbitMQ..."
curl -s https://packagecloud.io/install/repositories/rabbitmq/rabbitmq-server/script.deb.sh | sudo bash

echo "==> Atualizando lista de pacotes..."
sudo apt update

echo "==> Instalando o RabbitMQ Server..."
sudo apt install rabbitmq-server -y

echo "==> Habilitando e iniciando o serviço..."
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server

echo "==> Habilitando o painel de gerenciamento web (Management Plugin)..."
sudo rabbitmq-plugins enable rabbitmq_management

echo "==> Criando o usuário administrador (admin / admi1)..."
# Verifica se o usuário já existe para evitar erro caso rode o script mais de uma vez
if sudo rabbitmqctl list_users | grep -q "^admin\b"; then
    echo "O usuário 'admin' já existe. Atualizando senha e permissões..."
    sudo rabbitmqctl change_password admin admi1
else
    sudo rabbitmqctl add_user admin admi1
fi

sudo rabbitmqctl set_user_tags admin administrator
sudo rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"

echo "==> Instalação e configuração concluídas com sucesso!"
echo "O painel web está disponível em http://<IP_DO_RASPBERRY>:15672 (Login: admin / Senha: admi1)"