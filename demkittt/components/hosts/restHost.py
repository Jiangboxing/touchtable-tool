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


from hosts.host import Host
from api.eveApi import EveApi

class RestHost(Host):
	def __init__(self, name="host", port = 5000):
		self.liveOperation = True
		Host.__init__(self, name="host") 
		
		self.enableFlowSim = False
		self.port = port
		self.address = "http://localhost"
		#FIXME: Need some mechanism to obtain the IP Address of the system, for now we hardcode default to localhost. T200


			
	def startup(self):
		Host.startup(self)	
		
		self.restApi = EveApi(self, self.port)

	def timeTick(self, time, absolute = False):
		if not self.pause:
			Host.timeTick(self, time, absolute)

			#Now simulate the time
			self.preTickEnvs(time)
			self.preTickDevs(time)
			self.preTickCtrl(time)
			self.preTickComps(time)

			self.timeTickCtrl(time)
			self.timeTickEnvs(time)
			self.timeTickDevs(time)
			self.timeTickMeters(time)
			self.timeTickComps(time)

			self.simulateCosts(time)
			self.simulateFlows(time)

			self.storeStates()

			self.postTickLogging(time)

		self.executeCmdQueue()

