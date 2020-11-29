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
    self.estado = EstadosPuertaEntrada.IDLE # Control de estado para evitar comandos invalidos
  
  def recogeTarjeta(self):
    self.recogeTarjetaSem.acquire()
    if self.estado == EstadosPuertaEntrada.TARJETA_IMPRESA:
      print('recoge tarjeta')
      time.sleep(5)
      self.estado = EstadosPuertaEntrada.BARRERA_ARRIBA
      self.laserOffSem.release()

  def laserOff(self):
    self.laserOffSem.acquire()
    if self.estado == EstadosPuertaEntrada.BARRERA_ARRIBA:
      print('laser off')
      self.estado = EstadosPuertaEntrada.CARRO_PASANDO
      self.laserOnSem.release()
  
  def laserOn(self):
    self.laserOnSem.acquire()
    if self.estado == EstadosPuertaEntrada.CARRO_PASANDO:
      print('laser on')
      estacionamiento.sem.acquire()
      estacionamiento.lugaresDisponibles -= 1
      time.sleep(5)
      
      self.estado = EstadosPuertaEntrada.IDLE

      estacionamiento.sem.release()
      self.entrySem.release()
      

  def oprimeBoton(self):
    self.entrySem.acquire() # Bloquea por recurso compartido de lugares
    if self.estado == EstadosPuertaEntrada.IDLE:
      estacionamiento.sem.acquire()
      if estacionamiento.lugaresDisponibles > 0:
        print('imprime tarjeta')
        time.sleep(5)
        self.estado = EstadosPuertaEntrada.TARJETA_IMPRESA
        estacionamiento.sem.release()
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
    self.laserOff = threading.Semaphore(1)
    self.laserOn = threading.Semaphore(1)

  def run(self):
    while True:
      req = self.requestQueue.get()

      if req is None:
        break

      assert (req.ident in comandosParaSalir)

      time.sleep(1)

      self.requestQueue.task_done
      time.sleep(1)

class Estacionamiento():
  def __init__(self, lugares = 50, entradas = 2, salidas = 2):
    self.lugares = lugares
    self.entradas = entradas
    self.salidas = salidas
    self.lugaresDisponibles = lugares
    self.sem = threading.Semaphore(1) # Semaphore used to avoid race condition on available places

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
  def __init__(self, timestamp, ident, puertaEntrada):
    self.ident = ident
    self.timestamp = timestamp
    self.puertaEntrada = puertaEntrada

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('localhost', 10000)
print ( 'starting up on %s port %s' % server_address)
sock.bind(server_address)

sock.listen(1)

print ( 'waiting for a connection')
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

  estacionamiento = Estacionamiento(lugares, numPuertasEntrada, numPuertasSalida)

  while True:
    data = connection.recv(256)
    if data:
      dataStr = data.decode('utf-8')
      print ( 'server received "%s"' % dataStr)
      dataArr = dataStr.split()
      nuevaPeticion = Peticion(dataArr[0], dataArr[1], int(dataArr[2]))

      if nuevaPeticion.ident in comandosParaEntrada:
        puertasEntrada[nuevaPeticion.puertaEntrada - 1].requestQueue.put(nuevaPeticion)
      elif nuevaPeticion.ident in comandosParaSalir:
        puertasSalida[nuevaPeticion.puertaEntrada - 1].requestQueue.put(nuevaPeticion)
      elif nuevaPeticion.ident in comandosParaTerminar:
        break
    else:
      print ( 'no data from', client_address)
      connection.close()
      sys.exit()
finally:
  connection.close()
