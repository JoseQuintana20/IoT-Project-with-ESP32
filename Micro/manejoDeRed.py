import network  #Netwwork para el manejo de redes
import utime
import machine
from machine import Pin
import usocket

ledUno = Pin(2, Pin.OUT) #Declaro el pin2 como salida
def conexionRed(ssid="red", password="123456789"): #Define por defecto (red y 123456789)si no se ingresa ningún parametro
    sta_if = network.WLAN(network.STA_IF)   #AP_IF creo mi propia red y (STAF_IF connectarse a una red), creo mi objeto de conexión
    sta_if.active(True)
    try:
        sta_if.connect(ssid, password) #Connect to an AP
    except(OSError):
        print("ERROR DENTRO DE LA FUNCION DE RED")
        utime.sleep(2)
        machine.reset()
    conteoDeConexion = 0
    while not sta_if.isconnected():                      # Check for successful connection
        print("Connectando")
        ledUno.on()
        utime.sleep(1)
        ledUno.off()
        utime.sleep(1)
        conteoDeConexion += 1
        if conteoDeConexion == 3:
            break
    if conteoDeConexion < 3:
        print("Connectado")
        print(f'Parametro de red {sta_if.ifconfig()}')
        ledUno.on()
        utime.sleep(5)
        ledUno.off()
    else:
        ledUno.off()
        # Generar nuestra propia Red
        sta_if.active(False)
        ap_if = network.WLAN(network.AP_IF) # Genera un acccess point
        ap_if.active(True)
        ap_if.config(ssid="NAME", authmode=2, password="123456789") #authmode: 0 abierta, 1 web, 2 wpk pca, 3 wp. PAra ocultar Red: hidden = True
        print(f'Lanzando Red, parametros del ESP {ap_if.ifconfig()}')
        # Generación de un socket
        tcp_socket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        dirPuer = ('',80) #dirección y puerto
        tcp_socket.bind(dirPuer) #enlazarse o conectarse (vincular a la dirección y al puerto)
        tcp_socket.listen(2) #el número de escuchar
        while True:
            conn, addr = tcp_socket.accept()  #conn: conexión - addr: la dirección
            print(f'Conexion establecida de desde {addr}')
            requests = str(conn.recv(2048)) #Solictud de que estoy recepcionando #1024

            if requests.find("GET"):
                print(requests)
                paginaWeb = open("configuracion.html", "r")
                datosPaginaWeb = paginaWeb.read()
                paginaWeb.close()
                conn.send('HTTP/1.1 200 OK\n')
                conn.send('Content-Type: text/html\n')
                conn.send('Connection: keep-alive\n\n')
                conn.sendall(datosPaginaWeb)
                conn.close()

                if requests.find("GET /?") > 0:
                    #Extracción de valor de "red" y "clave"
                    print(requests.find("GET /?"))
                    reducido = requests[requests.find("GET /?")+len("GET /?")::]
                    print(f'Primer Corte {reducido}')
                    datosUnidos = reducido[0:reducido.find((" "))]
                    print(f'Segundo Corte {datosUnidos}')
                    datosSeparados = datosUnidos.split('&')
                    red = datosSeparados[0].replace("red=", "") #valor de "red"
                    clave = datosSeparados[1].replace("clave=", "") #valor de "clave"
                    print(f'Mi nueva red es {red} y la constraseña es {clave}')
                    nuevo = f'{{"red": "{red}","contrasenha": "{clave}"}}' #Reescrbiendo en formato JSON
                    print(nuevo)
                    dato = open("configuracion", "w")
                    dato.write(nuevo) #Escribiendo en el archivo "configuracion"
                    dato.close()

                    machine.reset() #Reset para conectarse con la nueva red y  contraseña configurada


