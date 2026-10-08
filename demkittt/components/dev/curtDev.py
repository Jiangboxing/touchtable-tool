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


from dev.loadDev import LoadDev
from dev.device import Device


class CurtDev(LoadDev):
	def __init__(self,  name,  host, influx=False, reader=None):
		LoadDev.__init__(self,  name,  host, influx, reader)
		
		self.devtype = "Curtailable"
		self.onOffDevice = False

		self.originalConsumption = {}

	def timeTick(self,  time):
		self.prunePlan()

		self.lockState.acquire()
		self.originalConsumption = dict(self.consumption)

		# Perform curtailment / load shedding
		if not self.strictComfort:
			for c in self.commodities:
				#see if we need to override by lower planning:
				if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
					if self.onOffDevice:
						if self.plan[c][0][1].real < 0.001 and self.plan[c][0][1].real > -0.001:
							self.consumption[c] = complex(0.0, 0.0)
					else:
						p = self.plan[c][0][1]
						#check for up / down:
						if self.consumption[c].real > 0.0001:
							self.consumption[c] = complex(max(0.0, min(self.consumption[c].real, p.real)), 0.0)
						else:
							self.consumption[c] = complex(min(0.0, max(self.consumption[c].real, p.real)), 0.0)

		self.lockState.release()
				
	def logStats(self, time):
		LoadDev.logStats(self, time)

		self.lockState.acquire()
		try:
			for c in self.commodities:
				self.logValue("W-power.original.c." + c, self.originalConsumption[c].real)
		except:
			pass
		self.lockState.release()

#### INTERFACING
	def getProperties(self):
		r = Device.getProperties(self) 	# Get the properties of the overall Device class, which already includes global properties

		self.lockState.acquire()
		# Populate the result dict
		r['filename'] = self.filename
		r['filenameReactive'] = self.filenameReactive
		r['scaling'] = self.scaling
		r['onOffDevice'] = self.onOffDevice
		r['originalConsumption'] = self.originalConsumption
		self.lockState.release()

		return r