# modificado para python 3.x, mayo 2020
# mayo 14 2008 - corregido para convertir str variable to bytes

# The client program sets up its socket differently from the way a server does. Instead of binding to a port and listening, it uses connect() to attach the socket directly to the remote address.

import socket
import sys

# Create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#
# Connect the socket to the port where the server is listening
server_address = ('localhost', 10000)
print ( 'connecting to %s port %s' % server_address)
sock.connect(server_address)

# After the connection is established, data can be sent through the socket with sendall() and received with recv(), just as in the server.

messages = ['un mensaje...', 'otro mensaje...']
try:
  # Send data
  for m in messages:
    print ('client sending "%s"' % m)
    sock.sendall(m.encode('utf-8'))	# a string variable needs to be encoded
# to utf-8 to convert it to a byte string
# only bytes travel through network
		# Look for the response
    
  respuesta = sock.recv(256)
  print ( 'client received "%s"' % respuesta.decode('utf-8')) # bytes to string
finally:
    print ( 'closing socket')
    sock.close()

def main(args):
  return 0

if __name__ == '__main__':
  import sys
  sys.exit(main(sys.argv))
