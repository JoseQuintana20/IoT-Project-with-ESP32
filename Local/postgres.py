import psycopg2
import paho.mqtt.client as mqtt
import json

# Función de conexión a la base de datos
def connect_to_database():
    return psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        password="73121490",
        database="Maestria"
    )

# Suscripción MQTT
def on_connect(client, userdata, flags, rc):
    client.subscribe("DB_ESP2")

# Procesar mensajes MQTT
def on_message(client, userdata, msg):
    print(str(msg.topic) + " : " + str(msg.payload))

    # Extraer datos del mensaje MQTT (suponiendo que el mensaje es una cadena en formato CSV)
    payload_json = json.loads(msg.payload.decode('utf-8'))

    # Extraer valores del JSON
    estado = payload_json["estado"]
    metodo = payload_json["metodo"]
    # estado, metodo = payload
    print("Estado:", estado)
    print("Método:", metodo)

    # Conectar a la base de datos
    conexion = connect_to_database()
    cursor = conexion.cursor()

    # Construir y ejecutar la consulta SQL
    query = f"INSERT INTO public.led(metodo, estado, fecha) VALUES (%s, %s, now());"
    cursor.execute(query, (metodo, estado))

    # Commit y cierre de la conexión a la base de datos
    conexion.commit()
    cursor.close()
    conexion.close()


cliente = mqtt.Client()
cliente.on_connect = on_connect
cliente.on_message = on_message
cliente.connect("broker.hivemq.com", 1883, 60)
cliente.loop_forever()