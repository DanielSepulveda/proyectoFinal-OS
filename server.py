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
  BARRERA_ARRIVA = 'barreraArriva'
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
    self.estado = EstadosPuertaEntrada.IDLE # Control de estado para evitar comandos invalidos
  
  def recogeTarjeta(self):
    if self.estado == EstadosPuertaEntrada.TARJETA_IMPRESA:
      print('recoge tarjeta')
      time.sleep(5)
      self.estado = EstadosPuertaEntrada.BARRERA_ARRIVA

  def laserOff(self):
    if self.estado == EstadosPuertaEntrada.BARRERA_ARRIVA:
      print('laser off')
      self.estado = EstadosPuertaEntrada.CARRO_PASANDO
  
  def laserOn(self):
    if self.estado == EstadosPuertaEntrada.CARRO_PASANDO:
      print('laser on')
      estacionamiento.lugaresDisponibles -= 1
      estacionamiento.sem.release()
      time.sleep(5)
      self.estado = EstadosPuertaEntrada.IDLE

  def oprimeBoton(self):
    if self.estado == EstadosPuertaEntrada.IDLE:
      estacionamiento.sem.acquire() # Bloquea por recurso compartido de lugares

      if estacionamiento.lugaresDisponibles > 0:
        print('imprime tarjeta')
        time.sleep(5)
        self.estado = EstadosPuertaEntrada.TARJETA_IMPRESA
      else:
        print('No hay lugar, espera un poco y vuelve a oprimir el botón')
        estacionamiento.sem.release()

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

class EstadosPuertaSalida(Enum):
  IDLE = 'idle'
  BARRERA_ARRIVA = 'barreraArriva'
  CARRO_PASANDO = 'carroPasando'

class PuertaSalida():
  def __init__(self):
    self.requestQueue = queue.Queue(100)
    self.funciones = {
      'meteTarjeta': self.meteTarjeta,
      'laserOffS': self.laserOff,
      'laserOnS': self.laserOn
    }

  def laserOn(self):
    if self.estado == EstadosPuertaSalida.CARRO_PASANDO:
      print('laser on')
      estacionamiento.lugaresDisponibles += 1
      estacionamiento.sem.release()
      time.sleep(5)
      self.estado = EstadosPuertaSalida.IDLE

  def laserOff(self):
    if self.estado == EstadosPuertaSalida.BARRERA_ARRIVA:
      print('laser off')
      self.estado = EstadosPuertaSalida.CARRO_PASANDO

  def meteTarjeta(self, req):
    if self.estado == EstadosPuertaSalida.IDLE:
      estacionamiento.sem.acquire() # Bloquea por recurso compartido de lugares

      if estacionamiento.lugaresDisponibles < estacionamiento.lugares:
        print('recibe tarjeta')
        time.sleep(5)
        self.estado = EstadosPuertaSalida.BARRERA_ARRIVA
      else:
        estacionamiento.sem.release()

  def run(self):
    while True:
      req = self.requestQueue.get()

      if req is None:
        break

      assert (req.ident in comandosParaSalir)

      comandoARealizar = self.funciones.get(req.ident)
      comandoARealizar(req)

      self.requestQueue.task_done()
      time.sleep(1)

class Estacionamiento():
  def __init__(self, lugares = 50, entradas = 2, salidas = 2):
    self.lugares = lugares
    self.entradas = entradas
    self.salidas = salidas
    self.lugaresDisponibles = lugares
    self.sem = threading.Semaphore()

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
