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


from hosts.zhost import ZHost
import time as tm

class ClockHost(ZHost):
	def __init__(self, name): 
		ZHost.__init__(self, name)

		self.slaves = [] #List of slave hosts
		self.networkMaster = True

		self.tickInterval = 1 # 1/frequency for the tickrate
		
	def startSimulation(self):
		self.zInit()
		self.startup()

		self.logMsg("Clock is running")

		old = int(tm.time())
		while True:
			now = int(tm.time())
			if now - old >= self.tickInterval:
				self.currentTime = now
				self.timeTick(now)
				old = now
			else:
				tm.sleep(0.001)

		#do a soft shutdown
		self.shutdown()
	
	def startup(self):
		self.zCall("bus", "connectMaster")

		# retrieve list of connected slaves to the bus
		self.slaves = self.zCall('bus', 'listOfSlaves')

		Host.startup(self)

		# cast a startup to this list
		self.zCall(self.slaves, 'startup')
			
	def timeTick(self,  time, absolute = True):	
		Host.timeTick(self, time, absolute)
		
		#Update the time in other hosts for synchronization
		self.zCall(self.slaves, 'timeTick', self.currentTime, True)

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
