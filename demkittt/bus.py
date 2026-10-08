#!/usr/bin/python3

# DEMKit software
# Copyright (C) 2020 CAES and MOR Groups, University of Twente, Enschede, The Netherlands

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON
# INFRINGEMENT; IN NO EVENT SHALL LICENSOR BE LIABLE FOR ANY
# CLAIM, DAMAGES OR ANY OTHER LIABILITY ARISING FROM OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE THEREOF.


# Permission is hereby granted, non-exclusive and free of charge, to any person,
# obtaining a copy of the DEMKit-software and associated documentation files,
# to use the Software for NON-COMMERCIAL SCIENTIFIC PURPOSES only,
# subject to the conditions mentioned in the DEMKit License:

# You should have received a copy of the DEMKit License
# along with this program.  If not, contact us via email:
# demgroup-eemcs@utwente.nl.


import zmq
import pickle
import sys

sys.path.insert(0, 'conf')
from usrconf import *

context = zmq.Context()

print("using socket ip/port or path:")
print(sockPath)

rx = context.socket(zmq.SUB)
# rx.bind("tcp://130.89.15.54:9010")
rx.bind(sockPath+"rsub")

tx = context.socket(zmq.PUB)
# tx.bind("tcp://130.89.15.54:9011")
tx.bind(sockPath+"rpub")

# Subscribe on everything
rx.setsockopt(zmq.SUBSCRIBE, b'')

#List of slaves and the name of the master
slaves = []
master = ""
nodes = {}

#List of controllers
controllers = []

#Here we go!
print("Message bus is up and running")

# Shunt messages out to our own subscribers
while True:
	# Process all parts of the message
	try:
		data = rx.recv_multipart()

		# Uncomment the next line for debugging
		# print(data)

		receiver = data[0].decode()

		#See if there is something we need to do with it:
		if(receiver == "bus#"):
			sender = data[1].decode()
			msgid = data[2].decode()
			what = data[5].decode()
			args = pickle.loads(data[6])
			ret = pickle.loads(data[3])
			zContext = zmq.Context()
			results = zContext.socket(zmq.PUSH)
			if ret != None:
				results.connect(ret)


			if(what == "listOfSlaves"):
				#print("list of slaves wanted")
				results.send(pickle.dumps([b"listOfSlaves", receiver.encode(), msgid.encode(), sender.encode(), pickle.dumps(slaves)]) )

			elif(what == "heartbeat"):
				print("receiving a heartbeat")
				results.send(pickle.dumps([b"heartbeat", receiver.encode(), msgid.encode(), sender.encode(), pickle.dumps("alive")]) )
				nodes[sender] = int(time.time())
				print(nodes)

			elif(what == "listOfNodes"):
				#print("list of slaves wanted")
				results.send(pickle.dumps([b"listOfNodes", receiver.encode(), msgid.encode(), sender.encode(), pickle.dumps(nodes)]) )

			elif(what == "nodesAlive"):
				#print("list of slaves wanted")
				r = []
				for k,v in nodes.items():
					if v > int(time.time()) - 60:
						r.append(k)
				print(r)
				results.send(pickle.dumps([b"nodesAlive", receiver.encode(), msgid.encode(), sender.encode(), pickle.dumps(r)]) )

			else:
				if(what == "connectSlave"):
					print("connecting slave: "+sender)
					if not sender in slaves:
						slaves.append(sender)
					nodes[sender] = int(time.time())
					results.send(pickle.dumps([what.encode(), receiver.encode(), msgid.encode(), sender.encode(), pickle.dumps(None)]) )
				elif(what == "disconnectSlave"):
					print("disconnecting slave: "+sender)
					if sender in slaves:
						slaves.remove(sender)
					results.send(pickle.dumps([what.encode(), receiver.encode(), msgid.encode(), sender.encode(), pickle.dumps(None)]) )
				elif(what == "connectMaster"):
					print("connecting master: "+sender)
					master = sender
					nodes[sender] = int(time.time())
					results.send(pickle.dumps([what.encode(), receiver.encode(), msgid.encode(), sender.encode(), pickle.dumps(None)]) )
				elif(what == "disconnectMaster"):
					print("disconnecting master: "+sender)
					master = ""
					del nodes[sender]
					results.send(pickle.dumps([what.encode(), receiver.encode(), msgid.encode(), sender.encode(), pickle.dumps(None)]) )
				elif(what == "connectCtrl"):
					print("connecting controller: "+args[0])
					if not args[0] in controllers:
						controllers.append(args[0])
					results.send(pickle.dumps([what.encode(), receiver.encode(), msgid.encode(), sender.encode(), pickle.dumps(controllers)]) )
				elif(what == "disconnectCtrl"):
					print("disconnecting controller: "+args[0])
					if args[0] in controllers:
						controllers.remove(args[0])
					#No ret value, this is a cast!
				elif(what == "timeoutChild"):
					print("disconnecting child: "+args[0])
					print(slaves)
					if args[0] in slaves:
						slaves.remove(args[0])
					del nodes[sender]
					print(slaves)

		else:
			tx.send_multipart(data)
	except:
		print("Some error, continue")
