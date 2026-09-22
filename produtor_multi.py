import pika
from dotenv import load_dotenv
import os

load_dotenv()

def conectar():
    credentials = pika.PlainCredentials(
        username=os.getenv("RABBITMQ_USER"),
        password=os.getenv("RABBITMQ_PASSWORD")
    )
    params = pika.ConnectionParameters(
        host=os.getenv("RABBITMQ_HOST"),
        port=int(os.getenv("RABBITMQ_PORT")),
        virtual_host=os.getenv("RABBITMQ_VHOST"),
        credentials=credentials
    )
    return pika.BlockingConnection(params)

def publicar_para_filas(mensagem):
    """Envia a mesma mensagem para TODAS as filas listadas no .env"""
    # Lista de filas do .env
    filas = [f.strip() for f in os.getenv("RABBITMQ_FILAS").split(",")]
    
    try:
        conexao = conectar()
        canal = conexao.channel()

        resultados = []
        for fila_nome in filas:
            # Garante que a fila existe
            canal.queue_declare(queue=fila_nome, durable=True)
            
            # Publica diretamente na fila
            canal.basic_publish(
                exchange='',
                routing_key=fila_nome,
                body=str(mensagem),
                properties=pika.BasicProperties(
                    delivery_mode=pika.DeliveryMode.Persistent
                )
            )
            resultados.append(f"✅ → {fila_nome}")

        print(f"\n📤 Mensagem enviada para {len(filas)} fila(s):")
        for res in resultados:
            print(res)
        print(f"Conteúdo: {mensagem}\n")

        conexao.close()

    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    resposta = {
        "status": "sucesso",
        "codigo": 200,
        "dados": "Seu processamento foi concluído com êxito!",
        "timestamp": "2026-09-22 15:54:00"
    }
    
    # Envia a resposta para TODAS as filas
    publicar_para_filas(resposta)