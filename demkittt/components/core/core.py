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

from core.components import *

from database.influxDB import InfluxDB
from usrconf import *
import util.helpers

import threading
import time
import sys
from queue import *

class Core:
	def __init__(self, name):
		self.name = name

		#should contain a list with all devices, controllers etc to distribute ticks
		self.entities = []
		self.devices = []
		self.controllers = []
		self.meters = []
		self.flows = []
		self.costs = []
		self.environments = []
		self.components = []

		self.db = InfluxDB(self)
		self.enablePersistence = True

		# Simulation messages
		self.enableMsg = True
		self.enableWarning = True
		self.enableError = True
		self.enableDebug = True

		self.writeData = True

		#Stats Logging
		self.logDevices = False
		self.logControllers = False
		self.logFlow = False
		self.logCosts = True

		# How to deal with multithreading / concurrency
		self.useThreads = False	# By default we use the state of the host
		self.maxThreads = 100

		# Named locks allow the dynamic creation of locks for single access blocks.
		self.namedLocks = {}
		self.accessNamedLock = threading.Lock()

		# Threads bookkeeping
		self.activeThreads = []

		# Locking
		self.locks = {}
		self.accessLock = threading.Lock()

		# External commands
		self.cmdQueue = Queue()
		self.syncMode = True # Run external commands in synchronized manner

		self.quitOnError = True


# Logging functions
	def logValue(self,  measurement,  tags,  values, time=None):
		if self.writeData:
			if time is None:
				self.db.appendValue(measurement,  tags,  values,  self.time())
			else:
				self.db.appendValue(measurement,  tags,  values, time)

	def logValuePrepared(self, data, time=None):
		if time is None:
			self.db.appendValuePrepared(data, self.time())
		else:
			self.db.appendValuePrepared(data, time)

	def logCsvLine(self, file, line):
		util.helpers.writeCsvLine(file, line)

	def logMsg(self, msg):
		if self.enableMsg:
			sys.stderr.write("MESSAGE: "+msg+"\n")
			sys.stderr.flush()

	def logWarning(self, warning):
		if self.enableWarning:
			sys.stderr.write("WARNING: "+warning+"\n")
			sys.stderr.flush()

	def logError(self, error):
		if self.enableError:
			sys.stderr.write("ERROR: "+error+"\n")
			sys.stderr.flush()
		if self.quitOnError:
			quit()

	def logDebug(self, msg):
		if self.enableDebug:
			sys.stderr.write("DEBUG: "+msg+"\n")
			sys.stderr.flush()

# Get object references, set/get variables and call functions, used for the API
	def entityByName(self, name):
		result = None

		if name == "host":
			result = self

		for e in self.entities:
			if e.name == name:
				result = e
				break

		return result

	def getObj(self, obj):
		try:
			return self.entityByName(self, obj)
		except:
			return None

	def getVar(self, obj, var):
		if obj != self.name:
			o = self.entityByName(obj)
		else:
			o = self

		if o != None:
			if hasattr(o, var):
				return getattr(o, var)
			else:
				return None
		else:
			return None

	def setVar(self, obj, var, val):
		if obj != self.name:
			o = self.entityByName(obj)
		else:
			o = self

		if val == "True" or val == "true":
			val = True
		elif val == "False" or val == "false":
			val = False
		elif val == "None" or val == "none" or val == "null" or val == "Null":
			val = None

		if o != None:
			if hasattr(o, var):
				v = getattr(o, var)
				try:
					if isinstance(v, int):
						setattr(o, var, int(val))
					elif isinstance(v, float):
						setattr(o, var, float(val))
					else:
						setattr(o, var, val)
				except:
					setattr(o, var, val)
				return True
			else:
				return False
		else:
			return False

	def setObj(self, obj, var, val):
		if obj != self.name:
			o = self.entityByName(obj)
		else:
			o = self

		v = self.entityByName(val)
		if v is None or o is None:
			return False
		else:
			if hasattr(o, var):
				setattr(o, var, v)
				return True
			else:
				return False


	def callFunction(self, obj, func, *args):
		if obj != self.name:
			o = self.entityByName(obj)
		else:
			o = self
		if o != None:
			try:
				return getattr(o, func)(*args)
			except:
				return None
		else:
			return None

	# The other one should be removed someday
	def callFunction2(self, obj, func, *args):
		if obj != self.name:
			o = self.entityByName(obj)
		else:
			o = self

		params = []
		if o != None:
			try:
				for key, value in args[0].items():
					if key == "obj":
						params.append(self.entityByName(value))
					elif key == "self" or key=="host":
						params.append(self)
					else:
						params.append(value)
				return getattr(o, func)(*params)
			except:
				return getattr(o, func)(*args)
		else:
			return None

	# Create an object. Note that the startup command must be issued explicitly!
	def createObject(self, obj, args):
		params = []
		if True: #try:
			try:
				for d in args:
					for key, value in d.items():
						if key == "obj":
							params.append(self.entityByName(value))
						elif key == "self" or key=="host":
							params.append(self)
						else:
							params.append(value)
			except:
				self.logWarning("Could not parse arguments for object: "+obj)

			if len(params) == 0:
				instance = eval(obj)()
			else:
				instance = eval(obj)(*params)

			# instance.startup()
			return instance
		# except:
		# 	self.logWarning("Could not create object: "+obj)
		# 	return False

	def removeObject(self, obj):
		try:
			o = self.entityByName(obj)
			if o is not None:
				o.shutdown()

				# Now try to find all object references and delete them.
				# This can be a quite exhaustive search. We may need to make this more efficient by local tracking
				for e in self.entities:
					for key, value in vars(e).items():
						if value == o:
							# remove the reference
							setattr(e, key, None)
						elif isinstance(value, list):
							if o in value:
								value.remove(o)
						elif isinstance(value, dict):
							for k,v in value.items():
								if v == o:
									del(value[k])

				# Note that this may not fix all problems!
				# FIXME: All components should properly handle a shutdown command and ideally already perform the garbage collection required!

				self.removeEntity(o)

				# delete the object
				del o

				return True

			else:
				self.logWarning("Could not remove object: "+obj)
				return False
		except:
			self.logWarning("Could not remove object: "+obj)
			return False

# Executing cmds in the cmdQueue
	def executeCmdQueue(self):
		while not self.cmdQueue.empty():
			r = self.cmdQueue.get(True)
			if True: #try:
				cmd = r['cmd']

				# Decoding the function call
				if cmd == "callFunction":
					entity = r['entity']
					func = r['func']
					args = r['args']
					if args is None:
						self.callFunction2(entity, func)
					else:
						self.callFunction2(entity, func, args)

				elif cmd == "setVar":
					entity = r['entity']
					var = r['var']
					val = r['val']
					self.setVar(entity, var, val)

				elif cmd == "setObj":
					entity = r['entity']
					var = r['var']
					val = r['val']
					self.setObj(entity, var, val)

				elif cmd == "createObj":
					entity = r['entity']
					val = r['val']
					self.createObject(entity, val)

				elif cmd == "removeObj":
					entity = r['entity']
					self.removeObject(entity)

				else:
					self.logWarning("Unknown command.")
					print(r)

			# except:
			# 	self.logWarning("External command could not be exectuted.")
			# 	print(r)



# Connecting entities to the host
	def addEntity(self, entity):
		if not isinstance(entity, str):
			if self.entityByName(entity.name):
				self.logError("Entity with this name already exists: "+entity.name)
			else:
				self.entities.append(entity)
		else:
			assert(False) #Impossible, entities live local only

	def addDevice(self, entity):
		self.devices.append(entity)

	def addController(self, entity):
		self.controllers.append(entity)

	def addMeter(self, entity):
		self.meters.append(entity)

	def addFlow(self, entity):
		self.flows.append(entity)

	def addEnv(self, entity):
		self.environments.append(entity)

	def addCost(self, entity):
		self.costs.append(entity)

	def addComponent(self, entity):
		self.components.append(entity)

	def removeEntity(self, entity):
		l = [self.entities, self.devices, self.controllers, self.flows, self.costs, self.environments, self.components, self.meters]
		for lst in l:
			if entity in lst:
				lst.remove(entity)

		# Check if we need to detach a controller.  Should not be needed but not tested for the touchtable
		for controller in self.controllers:
			if entity in controller.children:
				controller.children.remove(entity)
			if entity.name in controller.children:
					controller.children.remove(entity.name)

		# Check if we need to detach a controller.  Should not be needed but not tested for the touchtable
			for meter in self.meters:
				if entity in meter.devices:
					meter.devices.remove(entity)
				if entity.name in meter.devices:
					meter.devices.remove(entity.name)

		return True


	def clearDatabase(self):
		self.db.clearDatabase()



### Locking mechanism using object references
	def acquireLock(self, var, obj=None, blocking=True, timeout=None):
		result = True
		if self.useThreads:
			if obj is None:
				obj = self

			# Note: timeout is unused at the moment
			obj.accessLock.acquire()

			if var not in obj.locks:
				obj.locks[var] = threading.Lock()

			obj.accessLock.release()

			# Set the lock we need
			result = obj.locks[var].acquire(blocking=blocking)

		return result

	def releaseLock(self, var, obj=None, timeout=None):
		if self.useThreads:
			if obj is None:
				obj = self

			# release the lock we have
			try:
				obj.locks[var].release()
			except:
				pass

		return True

	# Get the state of a lock
	def getLock(self, var, obj=None, timeout=None):
		if self.useThreads:
			if obj is None:
				obj = self

			r = None

			self.accessdLock.acquire()

			if obj in self.locks:
				if var in self.locks[obj]:
					r = self.locks[obj][var]

			self.accessLock.release()

			return r
		return False


	def acquireNamedLock(self, name, obj=None, blocking=True, timeout=None):
		result = True

		if self.useThreads:
			if obj is None:
				obj = self

			# Note: timeout is unused at the moment
			self.accessNamedLock.acquire()

			if obj not in self.namedLocks:
				self.namedLocks[obj] = {}

			if name not in self.namedLocks[obj]:
				self.namedLocks[obj][name] = threading.Lock()

			self.accessNamedLock.release()

			# Set the lock we need
			result = self.namedLocks[obj][name].acquire(blocking=blocking)

		return result

	def releaseNamedLock(self, name, obj=None, timeout=None):
		if self.useThreads:
			if obj is None:
				obj = self

			try:
				self.namedLocks[obj][name].release()
			except:
				pass

		return True

	# Get the state of a lock
	def getNamedLock(self, name, obj=None, timeout=None):
		if self.useThreads:
			if obj is None:
				obj = self

			r = None

			# Note: timeout is unused at the moment
			self.accessNamedLock.acquire()

			if obj in self.namedLocks:
				if name in self.namedLocks[obj]:
					r = self.namedLocks[obj][name]

			self.accessNamedLock.release()

			return r
		else:
			return False #Unlocked




	# Easy functions for threading
	def runInThread(self, obj, func, *args):
		if self.useThreads:
			if threading.active_count() > self.maxThreads:
				self.logWarning("Too many threads running. Total threads: "+str(threading.active_count()))

				while threading.active_count() > self.maxThreads:
					time.sleep(0.001) # Wait a little time

			t = threading.Thread(target=self.zCallSingle, args=[obj, func, *args])
			self.activeThreads.append(t)
			t.start()
			return t
		else:
			self.zCallSingle(obj, func, *args)
			return None

	# Easy functions for threading on external function calls
	def zRunInThread(self, receivers, func, *args):
		if isinstance(receivers, list):
			if self.useThreads:
				ts = []

				for recv in receivers:
					ts.append(self.zCallThread(recv, func, *args))

				return ts
			else:
				self.zCallSingle(receivers, func, *args)
				return None
		else:
			if self.useThreads:
				if threading.active_count() > self.maxThreads:
					self.logWarning("Too many threads running. Total threads: "+str(threading.active_count()))

					while threading.active_count() > self.maxThreads:
						time.sleep(0.001) # Wait a little time

				t = threading.Thread(target=self.zCallSingle, args=[receivers, func, args])
				self.activeThreads.append(t)
				t.start()
				return t
			else:
				self.zCallSingle(receivers, func, *args)
				return None




### Function calls with possibility to extend for usage in sockets ###
	def zDecodeFunc(self, data):
		print("This function requires a socket implementation")
		assert(False)

	def zDecodeBroadcast(self, data):
		print("This function requires a socket implementation")
		assert(False)

	def zDecodeGetVar(self, data):
		print("This function requires a socket implementation")
		assert(False)

	def zDecodeSetVar(self, data):
		print("This function requires a socket implementation")
		assert(False)

	def zReturn(self, ret, func, receiver, sender, msgid, r):
		print("This function requires a socket implementation")
		assert(False)

	#calls are blocking and expect a return values
	def zCall(self, receivers, func, *args):
		if isinstance(receivers, list):
			return self.zCallList(receivers, func, *args)
		else:
			return self.zCallSingle(receivers, func, *args)

	#call a function on the bus and get the result(s). Requires the objects as a list!
	def zCallList(self, receivers, func, *args):
		result = {}

		#cast out the function calls locally and over the bus
		for recv in receivers:
			if isinstance(recv, str):
				#first check if it lives locally....
				e = self.entityByName(recv)
				if e != None:
					result[recv] = getattr(e, func)(*args)
			#assuming object here!
			else:
				result[recv] = getattr(recv, func)(*args)

		return result

	def zCallSingle(self, recv, func, *args):
		if isinstance(recv, str):
			e = self.entityByName(recv)
			if e != None:
				return getattr(e, func)(*args)
		#assuming object here!
		else:
			return getattr(recv, func)(*args)

	#Casts are nonblocking and do not expect a return value, they will just drop
	def zCast(self, receivers, func, *args):
		if isinstance(receivers, list):
			return self.zCastList(receivers, func, *args)
		else:
			return self.zCastSingle(receivers, func, *args)

	#call a function on the bus and get the result(s). Requires the objects as a list!
	def zCastList(self, receivers, func, *args):
		#cast out the function calls locally and over the bus
		for recv in receivers:
			if isinstance(recv, str):
				#first check if it lives locally....
				e = self.entityByName(recv)
				if e != None:
					getattr(e, func)(*args)
			#assuming object here!
			else:
				getattr(recv, func)(*args)

	def zCastSingle(self, recv, func, *args):
		if isinstance(recv, str):
			e = self.entityByName(recv)
			if e != None:
				getattr(e, func)(*args)
		#assuming object here!
		else:
			getattr(recv, func)(*args)

	#Variable setting is blocking:
	def zSet(self, receivers, var, val, lock=True):
		if isinstance(receivers, list):
			return self.zSetList(receivers, var, val, lock)
		else:
			return self.zSetSingle(receivers, var, val, lock)

	#call a function on the bus and get the result(s). Requires the objects as a list!
	def zSetList(self, receivers, var, val, lock=True):
		result = {}

		#cast out the function calls locally and over the bus
		for recv in receivers:
			if isinstance(recv, str):
				#first check if it lives locally....
				e = self.entityByName(recv)
				if e != None:
					if hasattr(e, var):
						if self.useThreads and lock:
							self.acquireLock(var, e)

						setattr(e, var, val)

						if self.useThreads and lock:
							self.releaseLock(var, e)

						result[recv] = True
					else:
						result[recv] = False
				else:
					assert(False)

			#assuming object here!
			else:
				if hasattr(recv, var):
					if self.useThreads and lock:
						self.acquireLock(var, recv)

					setattr(recv, var, val)

					if self.useThreads and lock:
						self.releaseLock(var, recv)

					result[recv] = True
				else:
					result[recv] = False

		return result

	def zSetSingle(self, recv, var, val, lock=True):
		if isinstance(recv, str):
			e = self.entityByName(recv)
			if e != None:
				if hasattr(e, var):
					if self.useThreads and lock:
						self.acquireLock(var, e)

					setattr(e, var, val)

					if self.useThreads and lock:
						self.releaseLock(var, e)
					return True
				else:
					return False
			else:
				assert(False)
		else:
			if hasattr(recv, var):
				if self.useThreads and lock:
					self.acquireLock(var, recv)

				setattr(recv, var, val)

				if self.useThreads and lock:
					self.releaseLock(var, recv)

				return True
			else:
				return False

	#Variable getting is blocking:
	def zGet(self, receivers, var, lock=True):
		if isinstance(receivers, list):
			return self.zGetList(receivers, var, lock)
		else:
			return self.zGetSingle(receivers, var, lock)

	#call a function on the bus and get the result(s). Requires the objects as a list!
	def zGetList(self, receivers, var, lock=True):
		result = {}

		#cast out the function calls locally and over the bus
		for recv in receivers:
			if isinstance(recv, str):
				#first check if it lives locally....
				e = self.entityByName(recv)
				if e != None:
					if hasattr(e, var):
						if self.useThreads and lock:
							self.acquireLock(var, e)

						result[recv] = getattr(e, var)

						if self.useThreads and lock:
							self.releaseLock(var, e)
					else:
						result[recv] = None

			#assuming object here!
			else:
				if hasattr(recv, var):
					if self.useThreads and lock:
						self.acquireLock(var, recv)

					result[recv] = getattr(recv, var)

					if self.useThreads and lock:
						self.releaseLock(var, recv)

				else:
					result[recv] = None

		return result

	def zGetSingle(self, recv, var, lock=True):
		if isinstance(recv, str):
			e = self.entityByName(recv)
			if e != None:
				if hasattr(e, var):
					if self.useThreads and lock:
						self.acquireLock(var, e)

					r =  getattr(e, var)

					if self.useThreads and lock:
						self.releaseLock(var, e)

					return r
				else:
					return None

		#assuming object here!
		else:
			if hasattr(recv, var):
				if self.useThreads and lock:
					self.acquireLock(var, recv)

				r = getattr(recv, var)

				if self.useThreads and lock:
					self.releaseLock(var, recv)

				return r
			else:
				return None


	def zInit(self):
		print("This function requires a socket implementation")
		assert(False)

	def zSubscribe(self):
		print("This function requires a socket implementation")
		assert(False)

	def zSendData(self, recvh, what, func, data, msgId = -1, retdict = None):
		print("This function requires a socket implementation")
		assert(False)

	def zRetData(self):
		print("This function requires a socket implementation")
		assert(False)

	def zRetCollector(self, msgId, answers, timeout = 10):
		print("This function requires a socket implementation")
		assert(False)

	def zHandle(self, data):
		print("This function requires a socket implementation")
		assert(False)

	def zPoll(self):
		print("This function requires a socket implementation")
		assert(False)
