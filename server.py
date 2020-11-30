import socket
import sys
import time
import threading
import random
import queue
from enum import Enum
from tabulate import tabulate

comandosParaEntrada = ['oprimeBoton', 'recogeTarjeta', 'laserOffE', 'laserOnE']
comandosParaSalir = ['meteTarjeta', 'laserOffS', 'laserOnS']
comandosParaTerminar = ['cierre']

puertasEntrada = []
puertasSalida = []
threads = []
global estacionamiento
startTime = time.time()
def getTimeStamp():
  return time.time() - startTime

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
  
  def recogeTarjeta(self, req):
    if self.estado == EstadosPuertaEntrada.TARJETA_IMPRESA:
      estacionamiento.nuevoRegistro(req.comando)
      print('recoge tarjeta')
      time.sleep(5)
      self.estado = EstadosPuertaEntrada.BARRERA_ARRIVA

  def laserOff(self, req):
    if self.estado == EstadosPuertaEntrada.BARRERA_ARRIVA:
      estacionamiento.nuevoRegistro(req.comando)
      print('laser off')
      self.estado = EstadosPuertaEntrada.CARRO_PASANDO
  
  def laserOn(self, req):
    if self.estado == EstadosPuertaEntrada.CARRO_PASANDO:
      print('laser on')
      estacionamiento.lugaresDisponibles -= 1
      estacionamiento.sem.release()
      estacionamiento.nuevoRegistro(req.comando, '', True)
      time.sleep(5)
      self.estado = EstadosPuertaEntrada.IDLE

  def oprimeBoton(self, req):
    if self.estado == EstadosPuertaEntrada.IDLE:
      estacionamiento.nuevoRegistro(req.comando)
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
      comandoARealizar(req)

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
    self.estado = EstadosPuertaSalida.IDLE

  def laserOn(self, req):
    if self.estado == EstadosPuertaSalida.CARRO_PASANDO:
      print('laser on')
      estacionamiento.lugaresDisponibles += 1
      estacionamiento.sem.release()
      estacionamiento.nuevoRegistro(req.comando, '', True)
      time.sleep(5)
      self.estado = EstadosPuertaSalida.IDLE

  def laserOff(self, req):
    if self.estado == EstadosPuertaSalida.BARRERA_ARRIVA:
      estacionamiento.nuevoRegistro(req.comando)
      print('laser off')
      self.estado = EstadosPuertaSalida.CARRO_PASANDO

  def meteTarjeta(self, req):
    if self.estado == EstadosPuertaSalida.IDLE:
      estacionamiento.nuevoRegistro(req.comando)
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
    self.registros = []

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
  
  def nuevoRegistro(self, comando, mensaje = '', conLugares = False):
    nR = [getTimeStamp(), comando, mensaje]
    if conLugares:
      nR.append(self.lugaresDisponibles)
      nR.append(self.lugares - self.lugaresDisponibles)
    self.registros.append(nR)

class Peticion():
  def __init__(self, comando):
    self.comando = comando
    comandoArr = comando.split()
    self.comandoArr = comandoArr
    self.ident = comandoArr[1]
    if not self.ident in comandosParaTerminar:
      self.puerta = int(comandoArr[2])

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
  estacionamiento.nuevoRegistro(initDataStr, f'Se abre un estacionamiento de {lugares}, {numPuertasEntrada} puertas de entrada y {numPuertasSalida} de salida', True)

  while True:
    data = connection.recv(256)
    if data:
      dataStr = data.decode('utf-8')
      print ( 'server received "%s"' % dataStr)
      nuevaPeticion = Peticion(dataStr)

      if nuevaPeticion.ident in comandosParaEntrada:
        puertasEntrada[nuevaPeticion.puerta - 1].requestQueue.put(nuevaPeticion)
      elif nuevaPeticion.ident in comandosParaSalir:
        puertasSalida[nuevaPeticion.puerta - 1].requestQueue.put(nuevaPeticion)
      elif nuevaPeticion.ident in comandosParaTerminar:
        break
    else:
      print ( 'no data from', client_address)
      connection.close()
      sys.exit()
except:
  print("Unexpected error:", sys.exc_info()[0])
  raise
finally:
  print('finally')
  connection.close()

  for i in range(estacionamiento.entradas):
    puertasEntrada[i].requestQueue.join()
    puertasEntrada[i].requestQueue.put(None)

  for i in range(estacionamiento.salidas):
    puertasSalida[i].requestQueue.join()
    puertasSalida[i].requestQueue.put(None)

  for t in threads:
    t.join()
  
  estacionamiento.nuevoRegistro(nuevaPeticion.comando)

  print(tabulate(estacionamiento.registros, headers=['Timestamp', 'Comando', 'El servidor despliega', 'Libres', 'Ocupados'], tablefmt="psql"))
  
  sys.exit()
