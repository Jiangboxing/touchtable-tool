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

class MasterSimHost(ZHost):
	def __init__(self, name): 
		ZHost.__init__(self, name)

		self.enableFlowSim = False
		self.slaves = [] #List of slave hosts

		self.networkMaster = True
		self.liveOperation = True

		self.connState = False
		
	def startSimulation(self):
		self.zInit()
		self.zSubscribe()

		#startup all entities
		self.startup()
		
		#simulate time
		for t in range(0,  self.intervals):
			self.timeTick(self.currentTime)
			self.currentTime = self.currentTime + self.timeBase

		#do a soft shutdown
		self.shutdown()
	
	def startup(self):
		while not self.zGetConnectionState():
			self.connState = False
			time.sleep(10)

		if self.connState is False:
			self.zCall("bus", "connectMaster")
			self.connState = True

		try:
			self.slaves = self.zCall('bus', 'listOfSlaves')
			Host.startup(self)
			self.zCall(self.slaves, 'startup')
		except:
			exit()


	def shutdown(self):
		Host.shutdown(self)

		try:
			self.zCall(self.slaves, 'shutdown')
			self.zCall("bus", "disconnectMaster")
		except:
			pass

			
	def timeTick(self,  time, absolute = True):
		while not self.zGetConnectionState():
			self.connState = False
			time.sleep(10)

		if self.connState == False:
			self.zCall("bus", "connectMaster")
			self.connState = True

		try:
			Host.timeTick(self, time, absolute)

			#Update the time in other hosts for synchronization
			self.zCall(self.slaves, 'timeTick', self.currentTime)

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
		except:
			pass