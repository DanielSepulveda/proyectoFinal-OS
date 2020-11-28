#!/usr/bin/env python
# -*- coding: utf-8 -*-

# modified for python 3.x may 2020
# modified 14 may to convert/deconvert str to bytes

# This sample program, based on the one in the standard library documentation, receives incoming messages and echos them back to the sender. It starts by creating a TCP/IP socket.

import socket
import sys
import time

# Definición de clases
#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Simula el manejo de préstamos bancarios. El gerente envía rápidamente una solicitud de préstamo ("aRequest") que lee de la
	terminal, a uno de tres analistas según la cantidad solicitada. Utiliza Queues para amontonarles las solicitudes en orden a
	cada uno de los analistas. Ellos corren en paralelo, cada uno en un thread
"""

import threading
import time
import random
import queue


class Peticion():
    def __init__(self):
        self.timestamp = 0
        self.ident = "Hola"
        self.detalle = []

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

    # Receive the data
    while True:
        data = connection.recv(256)
        dataStr = data.decode('utf-8')
        print('server received "%s"' % dataStr)  # data bytes back to st

        peticion = Peticion()
        peticion.timestamp = float(dataStr.split()[0])
        peticion.ident = dataStr.split()[1]
        peticion.detalle = dataStr.split()[2:]

        if data:
            print('sending answer back to the client')
            # b converts str to bytes
            connection.sendall(b'va de regreso...' + bytes(peticion.ident, 'utf-8'))
        else:
            print('no data from', client_address)
            connection.close()
            sys.exit()

finally:
    # Clean up the connection
    print('se fue al finally')
    connection.close()

# When communication with a client is finished, the connection needs to be cleaned up using close(). This example uses a try:finally block to ensure that close() is always called, even in the event of an error.
