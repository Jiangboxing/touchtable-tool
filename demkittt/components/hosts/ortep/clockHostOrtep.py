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


from hosts.clockHost import ClockHost

from drv.ortep.sstSensorReader import SstSensorReader

class ClockHostOrtep(ClockHost):
	def __init__(self, name): 
		ClockHost.__init__(self, name)

		self.slaves = [] #List of slave hosts
		self.networkMaster = True

		self.tickInterval = 1 # 1/frequency for the tickrate
		
	def startSimulation(self):
		self.zInit()

		print("Syncing time to a full control interval")
		self.sstDevice = SstSensorReader("tcp://localhost", 5564)
		self.sstDevice.startup()

		old = 0

		while True:
			t = int(self.sstDevice.readSample()['time'])
			if t > old:
				old = t
				print("current timestamp obtained from SST device: "+str(t))
			if t % 60 == 0:
				print("Time synced on full planner interval")
				old = t
				break

		self.startup()
		self.logMsg("Clock is running")

		while True:
			now = int(self.sstDevice.readSample()['time']) # Luckily, this is a blocking unit :)
			if now - old >= self.tickInterval:
				self.currentTime = now
				self.timeTick(now)
				old = now

		#do a soft shutdown
		self.shutdown()