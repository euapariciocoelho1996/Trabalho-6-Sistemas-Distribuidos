import pika, time
import os
import cv2
import joblib
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split

host = os.getenv('RABBITMQ_HOST', 'localhost')
modelo_path = "modelo_time.pkl"
classes_time = ["Flamengo", "Corinthians"]
img_size = 32
data_dir = "imagens_time"

# Treina o modelo se ainda não existir
def treinar_ou_carregar_modelo():
    if os.path.exists(modelo_path):
        print("✅ Modelo de time carregado do disco.")
        return joblib.load(modelo_path)

    print("🔧 Treinando modelo de time...")
    dados = []
    labels = []

    for i, classe in enumerate(classes_time):
        pasta = os.path.join(data_dir, classe)
        for arquivo in os.listdir(pasta):
            img_path = os.path.join(pasta, arquivo)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            img = cv2.resize(img, (img_size, img_size))
            dados.append(img.flatten())
            labels.append(i)

    X_train, _, y_train, _ = train_test_split(dados, labels, test_size=0.2, random_state=42)
    modelo = KNeighborsClassifier(n_neighbors=3)
    modelo.fit(X_train, y_train)

    joblib.dump((modelo, classes_time), modelo_path)
    print("✅ Modelo treinado e salvo.")
    return modelo, classes_time

# Carrega ou treina o modelo
modelo_time, classes_time = treinar_ou_carregar_modelo()

# Processa imagem recebida
def processar_imagem(body):
    img_array = np.frombuffer(body, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return "Imagem inválida"
    img = cv2.resize(img, (img_size, img_size))
    pred = modelo_time.predict([img.flatten()])[0]
    return f"Time identificado: {classes_time[pred]}"

# 🧠 Espera o RabbitMQ estar disponível
while True:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host))
        break
    except pika.exceptions.AMQPConnectionError:
        print("Aguardando RabbitMQ...")
        time.sleep(3)  # Espera 3 segundos antes de tentar de novo

# Conexão com RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters(host))
channel = connection.channel()

channel.exchange_declare(exchange='logs_topic', exchange_type='topic')
channel.queue_declare(queue='queue_time')
channel.queue_bind(exchange='logs_topic', queue='queue_time', routing_key='time')

def callback(ch, method, properties, body):
    resultado = processar_imagem(body)
    filename = properties.headers.get('filename', 'desconhecido')
    print(f"[TIME] {filename} → {resultado}")
    time.sleep(0.5)
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='queue_time', on_message_callback=callback, auto_ack=False)
print("[*] Consumidor TIME aguardando imagens...")
channel.start_consuming()
