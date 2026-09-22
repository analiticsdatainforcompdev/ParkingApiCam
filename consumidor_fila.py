import pika
import json
from dotenv import load_dotenv
import os
import time

load_dotenv()




def conectar():
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

def processar(ch, method, props, body):
    dados = json.loads(body.decode("utf-8"))
    print(f"\n📥 [{method.routing_key}] Mensagem recebida:")
    print(json.dumps(dados, indent=2, ensure_ascii=False))
    time.sleep(1)
    print(f"✅ Processada com sucesso!\n")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar(fila_especifica):
    try:
        conexao = conectar()
        canal = conexao.channel()
        canal.queue_declare(queue=fila_especifica, durable=True)
        canal.basic_qos(prefetch_count=1)
        canal.basic_consume(queue=fila_especifica, on_message_callback=processar)
        
        print(f"🔄 Escutando fila: {fila_especifica}")
        print("(Ctrl+C para sair)\n")
        canal.start_consuming()
    except KeyboardInterrupt:
        print("\n⏹️ Encerrado")
        if 'conexao' in locals(): conexao.close()

if __name__ == "__main__":
    # Defina qual fila quer escutar
    iniciar("fila_resposta_1")
    # Ou fila_resposta_2, fila_resposta_3, etc.