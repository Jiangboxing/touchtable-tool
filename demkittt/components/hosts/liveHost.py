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
import time as tm

class LiveHost(Host):
	def __init__(self, name = "host"):
		self.liveOperation = True

		Host.__init__(self, name)
		self.tickInterval = 1  # 1/frequency for the tickrate

	def startSimulation(self):
		#startup all entities
		self.startTime = int(tm.time())
		Host.startSimulation(self)
		
		#simulate time
		old = int(tm.time())
		old = old - (old%self.timeBase)
		while True:
			now = int(tm.time())
			if now - old >= self.tickInterval:
				self.currentTime = now
				self.logMsg("Simulating at time: "+self.timeHumanReadable())

				self.timeTick(now)
				old = now
			else:
				tm.sleep(0.001)

		#do a soft shutdown
		self.shutdown()
			
	def timeTick(self,  time, absolute = True):
		# FIXME: Maybe it is wise to run certain function calls in separate threads for live situations. See T217

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

		self.postTickLogging(time, True)

		self.executeCmdQueue()
