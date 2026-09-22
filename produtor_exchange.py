import pika
import json
from dotenv import load_dotenv
import os

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

def configurar_exchange_e_filas(canal):
    """Cria Exchange e vincula todas as filas a ele"""
    exchange = os.getenv("RABBITMQ_EXCHANGE")
    tipo = os.getenv("RABBITMQ_EXCHANGE_TYPE", "fanout")
    filas = [f.strip() for f in os.getenv("RABBITMQ_FILAS_DESTINO").split(",")]

    canal.exchange_declare(exchange=exchange, exchange_type=tipo, durable=True)

    for fila_nome in filas:
        canal.queue_declare(queue=fila_nome, durable=True)
        canal.queue_bind(queue=fila_nome, exchange=exchange)
        print(f"🔗 Fila '{fila_nome}' vinculada ao Exchange '{exchange}'")
    
    return exchange

def publicar_resposta(resposta):
    try:
        conexao = conectar()
        canal = conexao.channel()

        exchange = configurar_exchange_e_filas(canal)
        
        # Envia UMA VEZ → Exchange distribui para TODAS as filas
        canal.basic_publish(
            exchange=exchange,
            routing_key='',  # no fanout não precisa de chave
            body=json.dumps(resposta, ensure_ascii=False),
            properties=pika.BasicProperties(
                delivery_mode=pika.DeliveryMode.Persistent,
                content_type='application/json'
            )
        )

        print(f"\n✅ Resposta enviada para TODAS as filas via Exchange '{exchange}'")
        print(f"Conteúdo: {json.dumps(resposta, indent=2, ensure_ascii=False)}\n")

        conexao.close()

    except Exception as e:
        print(f"❌ Erro ao publicar: {e}")

if __name__ == "__main__":
    # Sua resposta/dados a salvar nas filas
    resposta_final = {
        "evento": "processamento_concluido",
        "status": "sucesso",
        "dados_entrada": "dados do seu processo",
        "resultado": "valor calculado ou resposta gerada",
        "data_hora": "2026-09-22T15:54:00-03:00"
    }

    publicar_resposta(resposta_final)