import pika
import time
import os
import random

host = os.getenv('RABBITMQ_HOST', 'localhost')
image_folder = './imagens'  # Pasta local com imagens

# Espera ativa até conseguir conectar ao RabbitMQ
while True:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        break
    except pika.exceptions.AMQPConnectionError:
        print("Aguardando RabbitMQ...")
        time.sleep(3)

connection.close()
time.sleep(5)  # Aguarda o RabbitMQ subir completamente

while True:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        channel = connection.channel()

        # Declarando exchange do tipo 'topic'
        channel.exchange_declare(exchange='logs_topic', exchange_type='topic')

        # Lista de imagens disponíveis
        image_files = [
            f for f in os.listdir(image_folder)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]

        if not image_files:
            print("[!] Nenhuma imagem encontrada na pasta './imagens'.")
        else:
            for _ in range(5):  # Enviar 5 imagens por segundo
                image_file = random.choice(image_files)
                prefix = image_file[:4].lower()

                if prefix not in ['face', 'time']:
                    print(f"[!] Ignorando '{image_file}' - prefixo desconhecido.")
                    continue

                routing_key = 'face' if prefix == 'face' else 'time'
                image_path = os.path.join(image_folder, image_file)

                with open(image_path, 'rb') as img:
                    image_data = img.read()

                channel.basic_publish(
                    exchange='logs_topic',
                    routing_key=routing_key,
                    body=image_data,
                    properties=pika.BasicProperties(headers={'filename': image_file})
                )

                print(f"[x] Enviada '{image_file}' pela rota '{routing_key}'")
                time.sleep(0.2)  # Espera para manter taxa de 5 por segundo

        connection.close()

    except pika.exceptions.AMQPConnectionError:
        print("[ERRO] Falha na conexão com o RabbitMQ. Tentando novamente em 5 segundos...")
        time.sleep(5)
