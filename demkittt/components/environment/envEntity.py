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


from core.entity import Entity

import threading

class EnvEntity(Entity):
	def __init__(self,  name,  host):
		Entity.__init__(self,  name, host)
		
		self.devtype = "environment" #change in the entity self
		self.type = "environment"

		self.supportsForecast = False

		self.lockState = threading.Lock()
	
	def preTick(self, time):
		pass
		
	def timeTick(self,  time):	
		pass
	
	def postTick(self, time):
		pass
	
	def startup(self):
		if self.host != None:
			self.host.addEnv(self)

		Entity.startup(self)
		
	def shutdown(self):
		pass	
	
	def logStats(self, time):
		pass
		
	def logValue(self, measurement,  value, time=None):
#		Old, code which is more generic, but slower. Kept for reference.
# 		tags = {'devtype':self.devtype,  'name':self.name}
# 		values = {measurement:value}
# 		self.host.logValue(self.type,  tags,  values, time)

		data = self.type+",devtype="+self.devtype+",name="+self.name+" "+measurement+"="+str(value)
		self.host.logValuePrepared(data, time)

	def getProperties(self):
		# Get the properties of this device
		r = {}

		self.lockState.acquire()
		r['name'] = self.name
		r['timeBase'] = self.timeBase
		r['devtype'] = self.devtype
		self.lockState.release()

		return r