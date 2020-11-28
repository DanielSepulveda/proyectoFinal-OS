#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket, sys, time
# network initialization
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create socket
server_address = ('localhost', 10000) 					 # connect socket to port
print ( 'connecting to %s port %s' % server_address)
sock.connect(server_address)                             # ready. Connection established

messages = [
'0.00 apertura 50 2 1',
'1.00 oprimeBoton 1',
'15.00 recogeTarjeta 1',
'21.00 laserOffE 1',
'22.00 laserOnE 1',
'29.0 oprimeBoton 1',
'32.0 oprimeBoton 2',
'44.00 recogeTarjeta 1',
'47.00 recogeTarjeta 2',
'49.00 meteTarjeta 1 29.0',
'52.00 laserOffE 1',
'53.00 laserOnE 1',
'55.00 laserOffE 2',
'56.00 laserOnE 2',
'57.00 laserOffS 1',
'58.00 laserOnS 1',
'60.00 cierre'
]

try:
    globalTime = 0.00
    # Send data
    for m in messages:
        print ( 'client sending "%s"' % m)
        print(m[0:7])
        timestamp = float(m[0:4])        # timestamp of command
        toSleep = timestamp - globalTime # seconds;
        time.sleep(toSleep)
        globalTime += toSleep
										 # send message to server
        sock.sendall(m.encode('utf-8'))  # a string variable needs to be encoded to utf-8 to convert it to a byte string
        data = sock.recv(256)
        print ('received from server "%s"' % data.decode('utf-8')) # data bytes back to str
									   
finally:
    print ( 'closing socket')
    sock.close()
