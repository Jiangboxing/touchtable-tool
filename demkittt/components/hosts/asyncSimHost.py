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

class AsyncSimHost(ZHost):
	def __init__(self, name): 
		ZHost.__init__(self, name)

	def startSimulation(self):
		self.zInit()

		Host.startSimulation(self)
		self.asyncStartup()

		self.zSubscribe()
		self.connState = False

		# Start the socket loop
		while True:
			while not self.zGetConnectionState():
				connState = False
				tm.sleep(10)

			if connState == False:
				self.zCall("bus", "connectSlave")
				connState = True

			self.zPoll()


	def shutdown(self):
		Host.shutdown(self)

		# Properly disconnect from the Bus
		self.zCall("bus", "disconnectSlave")

	# Trick to provide async startup
	def startup(self):
		self.restoreStates()

	def asyncStartup(self):
		ZHost.startup(self)

	# Everything runs asynchronous, based on incoming data / events from elsewhere
	# Hence, one needs (small) custom made devices that handle a lot more stuff
	# Ticks
	def preTickEnvs(self, time):
		pass

	def preTickDevs(self, time):
		pass

	def preTickCtrl(self, time):
		pass

	def preTickComps(self, time):
		pass

	def timeTickEnvs(self, time):
		pass

	def timeTickDevs(self, time):
		pass

	def timeTickCtrl(self, time):
		pass

	def timeTickComps(self, time):
		pass

	def timeTickMeters(self, time):
		pass

	def simulateCosts(self, time):
		pass

	def simulateFlows(self, time):
		pass

	def postTickLogging(self, time):
		pass

	def time(self):
		#return system time instead:
		return int(tm.time())