#!/usr/bin/env python
# -*- coding: utf-8 -*-

# modified for python 3.x may 2020
# modified 14 may to convert/deconvert str to bytes

# This sample program, based on the one in the standard library documentation, receives incoming messages and echos them back to the sender. It starts by creating a TCP/IP socket.

import socket
import sys
import time
import threading
import time
import random
import queue

#semaphore for changing free places variable
sem = threading.Semaphore()
lugares = 0
globalTime = 0.0

class Peticion():
    def __init__(self):
        self.timestamp = 0
        self.ident = "apertura"
        self.numPuerta = -1
        self.detalle = []

class PuertaEntrada():
    def __init__(self):
        self.requestQueue = queue.Queue(100)  # Entrance queue that handles requests

    def activaPuerta(self):
        while True:
            # Waits for a request to arrive to the entrance
            req = self.requestQueue.get()
            if req is None:
                break
            # Attends oprimeBoton, recogeTarjeta, laserOffE, laserOnE
            if req.ident == "oprimeBoton" or req.ident == "recogeTarjeta" or req.ident == "laserOnE" or req.ident == "laserOffE":
                # critical section to modify available spaces and global time
                sem.acquire()

                print("in critical section")
                time.sleep(1)
                
                sem.release()

            # signals that entrance finishes processing request
            self.requestQueue.task_done
            time.sleep(1)


class PuertaSalida():
    def __init__(self):
        self.requestQueue = queue.Queue(100)  # Queue of the entrance

    def activaPuerta(self):
        while True:
            # Waits for a request to arrive to the entrance
            req = self.requestQueue.get()
            if req is None:
                break
            # Attends meteTarjeta, laserOffS, laserOnS
            if req.ident == "meteTarjeta" or req.ident == "laserOnS" or req.ident == "laserOffS":
                # critical section to modify available spaces and global time
                sem.acquire()

                print("In critical section")
                time.sleep(1)

                sem.release()

            # signals that entrance finishes processing request
            self.requestQueue.task_done
            time.sleep(1)

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Then bind() is used to associate the socket with the server address. In this case, the address is localhost, referring to the current server, and the port number is 10000.

# Bind the socket to the port
server_address = ('localhost', 10000)
print('starting up on %s port %s' % server_address)
sock.bind(server_address)

# Calling listen() puts the socket into server mode, and accept() waits for an incoming connection.

# Listen for incoming connections
sock.listen(1)

# Wait for a connection
print('waiting for a connection')
connection, client_address = sock.accept()

# accept() returns an open connection between the server and client, along with the address of the client. The connection is actually a different socket on another port (assigned by the kernel). Data is read from the connection with recv() and transmitted with sendall().

try:
    print('connection from', client_address)

    # First client message
    data = connection.recv(256)
    dataStr = data.decode('utf-8')
    print('Servidor recibe "%s"' % dataStr)  # data bytes back to st

    peticion = Peticion()
    peticion.timestamp = float(dataStr.split()[0])
    peticion.ident = dataStr.split()[1]
    globalTime = peticion.timestamp
    lugares = int(dataStr.split()[2])
    numPuertasEntrada = int(dataStr.split()[3])
    numPuertasSalida = int(dataStr.split()[4])

    # Initializes proceses and they wait for response
    puertasEntrada = []
    puertasSalida = []
    threads = []

    for i in range(numPuertasEntrada):
        puertasEntrada.append(PuertaEntrada())
        t = threading.Thread(target=puertasEntrada[i].activaPuerta)
        t.start()
        threads.append(t)
    for i in range(numPuertasSalida):
        puertasSalida.append(PuertaSalida())
        t = threading.Thread(target=puertasSalida[i].activaPuerta)
        t.start()
        threads.append(t)
    print( "Servidor inicializa puertas ... " )
    connection.sendall(bytes(peticion.ident, 'utf-8'))
    while True:
        data = connection.recv(256)
        dataStr = data.decode('utf-8')
        print('Servidor recibe "%s"' % dataStr)  # data bytes back to st
    
        if data:
            peticion = Peticion()
            peticion.timestamp = float(dataStr.split()[0])
            peticion.ident = dataStr.split()[1]
            peticion.numPuerta = int(dataStr.split()[2])
            peticion.detalle = dataStr.split()[3:]
            
            if peticion.ident == "meteTarjeta" or peticion.ident == "laserOffS" or peticion.ident == "laserOnS":
                puertasSalida[peticion.numPuerta - 1].requestQueue.put(peticion)
            elif peticion.ident == "cierre":
                break
            else:
                puertasEntrada[peticion.numPuerta - 1].requestQueue.put(peticion)


            print('sending answer back to the client')
            # b converts str to bytes
            connection.sendall(b'va de regreso...' +
                               bytes(peticion.ident, 'utf-8'))
        else:
            print('no data from', client_address)
            connection.close()
            sys.exit()

finally:
    # Clean up the connection
    print('se fue al finally')
    connection.close()

# When communication with a client is finished, the connection needs to be cleaned up using close(). This example uses a try:finally block to ensure that close() is always called, even in the event of an error.
