from flask import Flask, jsonify, request
from flask_cors import CORS
import psutil
import platform
import socket
import pika
import json
import os
import time
import threading
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)


# ===================== RABBITMQ CONSUMER =====================

class RabbitMQConsumer:
    def __init__(self, fila):
        self.fila = fila
        self.conexao = None
        self.canal = None
        self.thread = None
        self.rodando = False

    def conectar(self):
        credentials = pika.PlainCredentials(
            os.getenv("RABBITMQ_USER"),
            os.getenv("RABBITMQ_PASSWORD")
        )
        params = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST"),
            port=int(os.getenv("RABBITMQ_PORT")),
            virtual_host=os.getenv("RABBITMQ_VHOST"),
            credentials=credentials
        )
        return pika.BlockingConnection(params)

    def processar(self, ch, method, props, body):
        dados = json.loads(body.decode("utf-8"))
      #  print(f"\n📥 [{method.routing_key}] Mensagem recebida:")
        print(json.dumps(dados, indent=2, ensure_ascii=False))
        time.sleep(1)
        print("✅ Processada com sucesso!\n")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def _run(self):
        try:
            self.conexao = self.conectar()
            self.canal = self.conexao.channel()
            self.canal.queue_declare(queue=self.fila, durable=True)
            self.canal.basic_qos(prefetch_count=1)
            self.canal.basic_consume(queue=self.fila, on_message_callback=self.processar)
            self.rodando = True

            #print("🔄 Escutando fila: {self.fila}")
            self.canal.start_consuming()

        except Exception as e:
            print(e)

            print("Erro no consumer:")
        finally:
            self.rodando = False
            if self.conexao and not self.conexao.is_closed:
                self.conexao.close()

    def iniciar(self):
        if self.rodando:
            print("⚠️ Consumer já está rodando")
            return

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def parar(self):
        self.rodando = False
        if self.canal and self.canal.is_open:
            self.canal.stop_consuming()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)


# Inicia o consumer em background
consumer = RabbitMQConsumer("sensores")
consumer.iniciar()


# ===================== RABBITMQ PRODUCER =====================

def publicar_na_fila(fila, mensagem):
    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER"),
        os.getenv("RABBITMQ_PASSWORD")
    )
    params = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST"),
        port=int(os.getenv("RABBITMQ_PORT")),
        virtual_host=os.getenv("RABBITMQ_VHOST"),
        credentials=credentials
    )

    conexao = pika.BlockingConnection(params)
    canal = conexao.channel()
    canal.queue_declare(queue=fila, durable=True)

    body = json.dumps(mensagem, ensure_ascii=False)
    canal.basic_publish(
        exchange='',
        routing_key=fila,
        body=body,
        properties=pika.BasicProperties(
            delivery_mode=2  # mensagem persistente
        )
    )

    conexao.close()
    return True


# ===================== ROTAS FLASK =====================

def get_device_info():
    mem = psutil.virtual_memory()
    memory_info = {
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "percent_used": mem.percent
    }

    disk = psutil.disk_usage('/')
    disk_info = {
        "total_gb": round(disk.total / (1024 ** 3), 2),
        "used_gb": round(disk.used / (1024 ** 3), 2),
        "free_gb": round(disk.free / (1024 ** 3), 2),
        "percent_used": disk.percent
    }

    cpu_info = {
        "percent_used": psutil.cpu_percent(interval=1),
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True)
    }

    system_info = {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine()
    }

    return {
        "system": system_info,
        "memory": memory_info,
        "disk": disk_info,
        "cpu": cpu_info
    }


@app.route('/info', methods=['GET'])
def info():
    return jsonify(get_device_info())


@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "consumer_ativo": consumer.rodando,
        "fila": consumer.fila
    })


@app.route('/enviar', methods=['POST'])
def enviar():
    dados = request.get_json()

    if not dados or 'fila' not in dados or 'mensagem' not in dados:
        return jsonify({"erro": "Campos 'fila' e 'mensagem' são obrigatórios"}), 400

    fila = dados['fila']
    mensagem = dados['mensagem']

    try:
        publicar_na_fila(fila, mensagem)
        return jsonify({"status": "enviado", "fila": fila}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
