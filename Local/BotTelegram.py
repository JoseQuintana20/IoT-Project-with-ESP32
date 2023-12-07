import telebot
import re
import paho.mqtt.client as mqtt
import paho.mqtt.publish as pub
import threading as Hilo
import psycopg2
import json
from paho.mqtt.publish import single

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from base64 import b64encode, urlsafe_b64decode
import hashlib


#################################################################################################################################################################################################
#######################################################        ENCRIPTADO        ################################################################################################################
#################################################################################################################################################################################################

def aes_encrypt(key, iv, plaintext):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    encryptor = cipher.encryptor()

    return encryptor.update(plaintext)


def aes_decrypt(key, iv, ciphertext):
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
    decryptor = cipher.decryptor()

    return decryptor.update(ciphertext)

key = b'0123456789ABCDEF'
iv = b'0123456789ABCDEF'

#################################################################################################################################################################################################
######################################################          DATA BASE        ################################################################################################################
#################################################################################################################################################################################################
# Función de conexión a la base de datos
def connect_to_database():
    return psycopg2.connect(
        host="127.0.0.1",
        port=5432,
        user="postgres",
        password="73121490",
        database="Maestria"
    )

#################################################################################################################################################################################################
#######################################################        BOT TELEGRAM      ################################################################################################################
#################################################################################################################################################################################################
# TOKEN
bot = telebot.TeleBot("6410303536:AAHqCMNLlhcNEbb4qaTduQqiQHBm_EDxtQ8")


#################################################################################################################################################################################################
#######################################################          REGISTRO        ################################################################################################################
#################################################################################################################################################################################################

# Verificar si el ID de Telegram está registrado en la base de datos
def is_registered(chat_id):
    # Conectar a la base de datos
    conexion = connect_to_database()
    cursor = conexion.cursor()

    # Construir y ejecutar la consulta SQL
    query = "SELECT chat_id FROM public.login;"
    cursor.execute(query)
    chat_ids = cursor.fetchall()  # Obtener todos los chat_id

    # Verificar si el chat_id coincide con algún dato de la columna chat_id
    for row in chat_ids:
        if chat_id == row[0]:
            cursor.close()
            conexion.close()
            return True

    # Cerrar la conexión a la base de datos
    cursor.close()
    conexion.close()

    return False


# Ejecutar solamente cuando el usuario esté registrado
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if is_registered(message.chat.id):
        bot.reply_to(message,
                     "Hola, escribe /on para encender el Led. \nEscribe /off para apagar el Led. \nEscribe /estado para saber en qué estado está el Led.")
    else:
        bot.reply_to(message,
                     "Hola, para usar el Bot, requiere registrarse. \nEscribe /registrar para registrarte")


@bot.message_handler(commands=['registrar'])
def register_user(message):
    if is_registered(message.chat.id):
        bot.reply_to(message, "Ya estás registrado.")
    else:
        bot.reply_to(message, "Por favor, ingrese la contraseña de acceso:")
        bot.register_next_step_handler(message, verify_password)

def verify_password(message):
    key = "123456789"
    password = message.text
    if password == key:
        bot.reply_to(message, "Contraseña correcta. Registrado.")
        # Registrar el siguiente paso con la función de manejo correspondiente
        chat_id = message.chat.id

        # Establecer la conexión a la base de datos
        conexion = psycopg2.connect(
            host="127.0.0.1",
            port=5432,
            user="postgres",
            password="73121490",
            database="Maestria"
        )
        cursor = conexion.cursor()

        # Construir y ejecutar la consulta SQL
        query = "INSERT INTO public.login(chat_id) VALUES (%s);"
        cursor.execute(query, (chat_id,))

        # Confirmar los cambios en la base de datos y cerrar la conexión
        conexion.commit()
        cursor.close()
        conexion.close()

        # Ejecutar el comando start/help después de registrar al usuario
        send_welcome(message)
    else:
        bot.reply_to(message, "Contraseña incorrecta. Por favor, intenta nuevamente.")
        bot.register_next_step_handler(message, verify_password)


#################################################################################################################################################################################################
#######################################################           ESTADO         ################################################################################################################
#################################################################################################################################################################################################

# Procesar mensajes MQTT
@bot.message_handler(commands=['estado'])
def check_led_state(message):
    if is_registered(message.chat.id):
        # Conectar a la base de datos
        conexion = connect_to_database()
        cursor = conexion.cursor()

        # Construir y ejecutar la consulta SQL
        query = "SELECT estado FROM public.led ORDER BY fecha DESC LIMIT 1;"
        cursor.execute(query)
        estado = cursor.fetchone()[0]  # Obtener directamente el valor del estado

        if estado == "on":
            bot.reply_to(message, "LED encendido")
        else:
            bot.reply_to(message, "LED apagado")

        # Cerrar la conexión a la base de datos
        cursor.close()
        conexion.close()
    else:
        bot.reply_to(message, "Debes estar registrado para usar este comando.")

#################################################################################################################################################################################################
#######################################################          /ON/OFF         ################################################################################################################
#################################################################################################################################################################################################
def publicar():
    # encriptar MENSAJE
    host = "broker.hivemq.com"  # Este es el broker gratuito utilizado
    puerto = 1883
    topico = "ESP2"

    @bot.message_handler(commands=['on', 'off'])
    def control_led(message):
        if is_registered(message.chat.id):
            estado = message.text[1:]  # Obtener el estado del mensaje (/on o /off)

            data = {
                'estado': estado,
                'metodo': 'Telegram'
            }

            # Convertir los datos a JSON
            data_json = json.dumps(data)
            # Asegurar que la cadena tenga una longitud múltiplo de 16
            padded_length = (len(data_json) // 16 + 1) * 16
            padded = data_json + ' ' * (padded_length - len(data_json))
            plaintext_bytes = padded.encode()

            ciphertext = aes_encrypt(key, iv, plaintext_bytes)
            print("Texto original:", plaintext_bytes)
            print("Texto encriptado:", ciphertext)

            single(hostname=host, topic=topico, port=puerto, payload=ciphertext)
            if estado == "on":
                bot.reply_to(message, "LED encendido")
            else:
                bot.reply_to(message, "LED apagado")
        else:
            bot.reply_to(message, "Debes estar registrado para usar este comando.")


#################################################################################################################################################################################################
######################################################       BUCLES - /ON/OFF     ###############################################################################################################
#################################################################################################################################################################################################

# Suscripción MQTT
b = Hilo.Thread(target=publicar)
print("\n")
b.start()

#################################################################################################################################################################################################
#######################################################           ECHO           ################################################################################################################
#################################################################################################################################################################################################

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "No entiendo el comando. Prueba /start para controlar el LED.")

#################################################################################################################################################################################################
######################################################         BUCLES - BOT      ###############################################################################################################
#################################################################################################################################################################################################

# Iniciar el bot
bot.infinity_polling()