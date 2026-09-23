sudo rabbitmqctl add_user admin admin
sudo rabbitmqctl set_user_tags admin administrator
sudo rabbitmqctl set_permissions -p / admin ".*" ".*" ".*"

pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host www.piwheels.org python-dotenv

sudo apt update
sudo apt install --allow-unauthenticated python3-dev python3-cffi python3-cryptography -y

sudo apt install --allow-unauthenticated python3-psutil -y



echo "# ParkingApiCam" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:analiticsdatainforcompdev/ParkingApiCam.git
git push -u origin main







///Comandos para api cam

#Envio
    
    #[M:1]     ->  realizar medicao do sensor 1 e retorna o valor para o serviço

#Resposta

    #[M:1]R|256

    








curl -X POST http://192.168.24.104:5000/enviar \
  -H "Content-Type: application/json" \
  -d '{
    "fila": "fila_resposta_1",
    "mensagem": {"texto": "Olá, RabbitMQ!", "prioridade": "alta"}
  }'



  curl -X POST http://192.168.24.104:5000/enviar \
  -H "Content-Type: application/json" \
  -d '{
    "fila": "fila_resposta_1",
    "mensagem": {"comando": "#M:1", "prioridade":0}
  }'












  