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


from dev.device import Device

class ThermalDevice(Device):
	def __init__(self,  name,  host):
		Device.__init__(self,  name, host)
		
		self.devtype = "Thermal" #change in device self
		self.type = "devices"
		
		#state
		self.totalConsumption = 0.0
		self.temperature = 0.0
		self.commodities = ['HEAT']
	
	# def preTick(self, time):
	# 	pass
	#
	# def timeTick(self,  time):
	# 	pass
	#
	# def postTick(self, time):
	# 	pass
	#
	# def startup(self):
	# 	pass
	#
	# def shutdown(self):
	# 	pass
	#
	# def logStats(self, time):
	# 	pass

	def getProperties(self):
		# Get the properties of this device
		r = dict(Device.getProperties(self))

		self.lockState.acquire()
		# Populate the result dict
		r['temperature'] = self.temperature
		self.lockState.release()

		return r