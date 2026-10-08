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

class SimHost(Host):
	def __init__(self, name = "host"):
		self.liveOperation = False

		Host.__init__(self, name)

		self.enablePersistence = False

	def startSimulation(self):
		#startup all entities
		Host.startSimulation(self)
		
		#simulate time
		for t in range(0,  self.intervals):
			self.timeTick(self.currentTime)
			self.currentTime = self.currentTime + self.timeBase
		
		#do a soft shutdown
		self.shutdown()
			
	def timeTick(self,  time, absolute = True):
		# Modify the state
		self.executeCmdQueue()

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


