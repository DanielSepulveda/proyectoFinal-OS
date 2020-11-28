""" Simula el manejo de préstamos bancarios. El gerente envía rápidamente una solicitud de préstamo ("aRequest") que lee de la 
	terminal, a uno de tres analistas según la cantidad solicitada. Utiliza Queues para amontonarles las solicitudes en orden a
	cada uno de los analistas. Ellos corren en paralelo, cada uno en un thread
"""

import threading, time, random, queue

class Request():     #se utiliza para agrupar en un solo objeto el numero de cliente y la cantidad solicitada
	def __init__(self):
		self.numCliente = 0  #ambos son números enteros
		self.amount = 0

class Analista():
	def __init__(self, probability=100, timeApproval=100, minAmount=1, maxAmount=100000000):
		self.probability = probability   #probabilidad de que se apruebe el prestamo - between 0.0 and 1.0
		self.timeApproval = timeApproval #tempo para que se apruebe el prestamo, en segundos. integer
		self.minAmount = minAmount       #this analist takes requests between min and max amounts. integers
		self.maxAmount = maxAmount
		self.requestQueue = queue.Queue(100)  #queue of pending requests, maximum 100
	
	def analizaPrestamo (self):
		while True:
			item = self.requestQueue.get() #se espera hasta que aparezca un "request" en la cola, Non busy wait
			if item is None:
				break
			assert (item.amount >= self.minAmount and item.amount < self.maxAmount)
        
			time.sleep(self.timeApproval) #decidiendo si aprueba el prestamo...
			
			resultado = random.uniform (0.0,1.0)
			if resultado >= 1.0 - self.probability:
				print('\n--------Felicidades %s, préstamo de $%s aprobado!!' % (item.numCliente, item.amount))
			else:
				print('\n--------Lo sentimos %s, su préstamo de $%s no fué aprobado' % (item.numCliente, item.amount))
			
			self.requestQueue.task_done #señala que se termino de procesar esta solicitud de préstamo
			time.sleep(1)
			
# --------------
# inicialización
# --------------			
analistas = []
numAnalistas = 3					
analistas.append(Analista(0.10,10,1000000,100000000)) # aprueba prestamos > 1000000 con probabilidad 0.10 en 10 segundos
analistas.append(Analista(0.50,7,100000,1000000))    # entre 100k y 1m-1, con probabilidad 0.5 en 7 segundos
analistas.append(Analista(0.80,4,1,100000))    	    # entre 1 y 100k -1, con probabilidad 0.80 en 4 segundos

threads = []
for i in range(numAnalistas):
  t = threading.Thread(target=analistas[i].analizaPrestamo) #all  threads start while true loops waiting for a request
  t.start()
  threads.append(t) #aqui juntamos las threads para matarlas al final.
  
# -----------------   
# loop del gerente:
# -----------------
    
while True:  
	line = input('NumeroDeCliente y cantidadSolicitada:\n')
	if not line: #ya no hay mas peticiones al gerente
		break
	
	time.sleep(1) # El gerente platica 1 segundo con el cliente
	
	aRequest = Request() #solicitud de prestmo 
	aRequest.numCliente = int( line.split()[0] )
	aRequest.amount = int( line.split()[1] )
	print ('cliente %s solicita un préstamo de %s' % (aRequest.numCliente, aRequest.amount) )
	
	if aRequest.amount >= 1000000: #lo envia a la cola del analista adecuado, según la cantidad soliltitads
		analistas[0].requestQueue.put(aRequest)
	elif aRequest.amount >= 100000:
		analistas[1].requestQueue.put(aRequest)
	else:
		analistas[2].requestQueue.put(aRequest)

# -------------
# Final cleanup so as not to leave anything in queues or running processes:
# -------------
print ("llego aqui")
for i in range(numAnalistas):
	analistas[i].requestQueue.join()    # finish up pending requests in queues
	print("after join", i)
	analistas[i].requestQueue.put(None) # break while loops of threads after pending requests
	print("after none", i)
	
	 
    
for t in threads:
  t.join() # finish up threads
