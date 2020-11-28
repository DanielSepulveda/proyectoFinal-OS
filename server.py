import socket
import sys
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('localhost', 10000)
print ( 'starting up on %s port %s' % server_address)
sock.bind(server_address)

sock.listen(1)

print ( 'waiting for a connection')
connection, client_address = sock.accept()

try:
	print ( 'connection from', client_address)

	while True:
		data = connection.recv(256)
		if data:
			print ( 'server received "%s"' % data.decode('utf-8'))
		else:
			print ( 'no data from', client_address)
			connection.close()
			sys.exit()
finally:
	connection.close()
