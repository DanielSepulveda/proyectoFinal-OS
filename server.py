import socket
import sys
import time
import threading
import random
import queue
from enum import Enum

comandosParaEntrada = ['oprimeBoton', 'recogeTarjeta', 'laserOffE', 'laserOnE']
comandosParaSalir = ['meteTarjeta', 'laserOffS', 'laserOnS']
comandosParaTerminar = ['cierre']

puertasEntrada = []
puertasSalida = []
threads = []
global estacionamiento


class EstadosPuertaEntrada(Enum):
    IDLE = 'idle'
    TARJETA_IMPRESA = 'tarjetaImpresa'
    BARRERA_ARRIBA = 'barreraArriba'
    CARRO_PASANDO = 'carroPasando'


class PuertaEntrada():
    def __init__(self):
        self.requestQueue = queue.Queue(100)
        self.funciones = {
            'oprimeBoton': self.oprimeBoton,
            'recogeTarjeta': self.recogeTarjeta,
            'laserOffE': self.laserOff,
            'laserOnE': self.laserOn
        }
        self.laserOffSem = threading.Semaphore(0)
        self.laserOnSem = threading.Semaphore(0)
        self.recogeTarjetaSem = threading.Semaphore(0)
        self.entrySem = threading.Semaphore(1)
        # Control de estado para evitar comandos invalidos
        self.estado = EstadosPuertaEntrada.IDLE

    def recogeTarjeta(self):
        self.recogeTarjetaSem.acquire()
        print('recoge tarjeta')
        time.sleep(5)
        self.laserOffSem.release()

    def laserOff(self):
        self.laserOffSem.acquire()
        print('laser off')
        self.laserOnSem.release()

    def laserOn(self):
        self.laserOnSem.acquire()
        print('laser on')
        
        estacionamiento.sem.acquire()
        estacionamiento.lugaresDisponibles -= 1
        time.sleep(5)
        estacionamiento.sem.release()

        self.entrySem.release()

    def oprimeBoton(self):
        self.entrySem.acquire()

        if estacionamiento.lugaresDisponibles > 0:
            print('imprime tarjeta')
            time.sleep(5)

            self.recogeTarjetaSem.release()

        else:
            print('No hay lugar, espera un poco y vuelve a oprimir el botón')
            self.entrySem.release()

    def run(self):
        while True:
            req = self.requestQueue.get()

            if req is None:
                break

            assert (req.ident in comandosParaEntrada)

            comandoARealizar = self.funciones.get(req.ident)
            comandoARealizar()

            self.requestQueue.task_done()
            time.sleep(1)


class PuertaSalida():
    def __init__(self):
        self.requestQueue = queue.Queue(100)

        self.funciones = {
            'meteTarjeta': self.meteTarjeta,
            'laserOffS': self.laserOff,
            'laserOnS': self.laserOn
        }

        self.exitSem = threading.Semaphore(1)
        self.laserOffSem = threading.Semaphore(0)
        self.laserOnSem = threading.Semaphore(0)

    def meteTarjeta(self, req):
        self.exitSem.acquire()
        print('mete tarjeta')
        if req.pago:
            if req.timestamp - req.tiempoPago <= 15:
                
                print('pagado a tiempo')
                time.sleep(5)
                self.laserOffSem.release()
            else:
                print('pasaron más de 15 mins desde el pago')
                self.exitSem.release()
        else:
            print("No pagaste")
            self.exitSem.release

    def laserOff(self):
        self.laserOffSem.acquire()
        print('laser off salida')
        self.laserOnSem.release()

    def laserOn(self):
        self.laserOnSem.acquire()
        print('laser on salida')
        
        estacionamiento.sem.acquire()

        estacionamiento.lugaresDisponibles += 1
        time.sleep(5)

        estacionamiento.sem.release()
        self.exitSem.release()

    def run(self):
        while True:
            req = self.requestQueue.get()

            if req is None:
                break
            assert (req.ident in comandosParaSalir)

            if req.ident == "meteTarjeta":
                self.meteTarjeta(req)
            else:
                comandoARealizar = self.funciones.get(req.ident)
                comandoARealizar()
            
            self.requestQueue.task_done
            time.sleep(1)


class Estacionamiento():
    def __init__(self, lugares=50, entradas=2, salidas=2):
        self.lugares = lugares
        self.entradas = entradas
        self.salidas = salidas
        self.lugaresDisponibles = lugares
        # Semaphore used to avoid race condition on available places
        self.sem = threading.Semaphore(1)

        for i in range(numPuertasEntrada):
            puertasEntrada.append(PuertaEntrada())
            t = threading.Thread(target=puertasEntrada[i].run)
            t.start()
            threads.append(t)

        for i in range(numPuertasSalida):
            puertasSalida.append(PuertaSalida())
            t = threading.Thread(target=puertasSalida[i].run)
            t.start()
            threads.append(t)


class Peticion():
    def __init__(self, timestamp, ident, puerta, detalle):
        self.ident = ident
        self.timestamp = timestamp
        self.puerta = puerta
        if len(detalle) == 2:
            self.pago = True
            self.tiempoPago = detalle[1]
        else:
            self.pago = False


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('localhost', 10000)
print('starting up on %s port %s' % server_address)
sock.bind(server_address)

sock.listen(1)

print('waiting for a connection')
connection, client_address = sock.accept()

try:
    print('connection from', client_address)

    initData = connection.recv(256)
    initDataStr = initData.decode('utf-8')
    print('Servidor recibe "%s"' % initDataStr)
    initDataArr = initDataStr.split()
    lugares = int(initDataArr[2])
    numPuertasEntrada = int(initDataArr[3])
    numPuertasSalida = int(initDataArr[4])

    estacionamiento = Estacionamiento(
        lugares, numPuertasEntrada, numPuertasSalida)

    while True:
        data = connection.recv(256)
        if data:
            dataStr = data.decode('utf-8')
            print('server received "%s"' % dataStr)
            dataArr = dataStr.split()
            nuevaPeticion = Peticion(dataArr[0], dataArr[1], int(dataArr[2]), dataArr[3:])

            if nuevaPeticion.ident in comandosParaEntrada:
                puertasEntrada[nuevaPeticion.puerta -
                               1].requestQueue.put(nuevaPeticion)
            elif nuevaPeticion.ident in comandosParaSalir:
                puertasSalida[nuevaPeticion.puerta -
                              1].requestQueue.put(nuevaPeticion)
            elif nuevaPeticion.ident in comandosParaTerminar:
                break
        else:
            print('no data from', client_address)
            connection.close()
            sys.exit()
finally:
    connection.close()
