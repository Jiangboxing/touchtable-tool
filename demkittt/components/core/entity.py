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


from util.persistence import Persistence

import threading

class Entity:
	def __init__(self,  name,  host):
		self.host = host
		self.name = name

		self.persistence = None

		if self.host != None:
			self.host.addEntity(self)

			# Persistent data storage for recovery on a crash in demo sites
			if self.host.enablePersistence:
				self.persistence = Persistence(self, self.host)

		self.type = "entity"
		
		#params
		self.timeBase = 60

		# Locking
		self.locks = {}
		self.accessLock = threading.Lock()

	def preTick(self, time):
		pass

	def startup(self):
		pass
		
	def shutdown(self):
		pass

	def logStats(self, time):
		pass
		
	def logValue(self, measurement,  value):
		tags = {'name':self.name}
		values = {measurement:value}
		self.host.logValue(self.type,  tags,  values)

	def storeState(self):
		try:
			if self.persistence is not None:
				self.accessLock.acquire()
				self.persistence.save()
				self.accessLock.release()
		except:
			try:
				self.accessLock.release()
			except:
				pass
			pass

	def restoreState(self):
		try:
			if self.persistence is not None:
				self.accessLock.acquire()
				self.persistence.load()
				self.accessLock.release()
		except:
			try:
				self.accessLock.release()
			except:
				pass
			pass


	def logMsg(self, msg):
		self.host.logMsg("["+self.name+"] "+msg)

	def logWarning(self, warning):
		self.host.logWarning("["+self.name+"] "+warning)

	def logError(self, error):
		self.host.logError("["+self.name+"] "+error)

	def logDebug(self, msg):
		self.host.logDebug("["+self.name+"] "+msg)


# Threading functions
	def acquireLock(self, var, obj=None, blocking=True, timeout=None):
		return self.host.acquireLock(vam, obj, blocking, timeout)

	def releaseLock(self, var, obj=None, timeout=None):
		return self.host.releaseLock(var, obj, timeout)

	def getLock(self, var, obj=None, timeout=None):
		return self.host.getLock(var, obj, timeout)

	def acquireNamedLock(self, name, obj=None, blocking=True, timeout=None):
		return self.host.acquireNamedLock(name, obj, blocking, timeout)

	def releaseNamedLock(self, name, obj=None, timeout=None):
		return self.host.releaseNamedLock(name, obj, timeout)

	def getNamedLock(self, name, obj=None, timeout=None):
		return self.host.getNamedLock(name, obj, timeout)

	def runInThread(self, func, *args):
		return self.host.runInThread(self, func, *args)



	def zCall(self, receivers, func, *args):
		return self.host.zCall(receivers, func, *args)
		
	def zCast(self, receivers, func, *args):
		self.host.zCast(receivers, func, *args)
		
	def zSet(self, receivers, var, val):
		self.host.zSet(receivers, var, val)
		
	def zGet(self, receivers, var):
		return self.host.zGet(receivers, var)

	def zRunInThread(self, receivers, func, *args):
		return self.host.zRunInThread(receivers, func, *args)