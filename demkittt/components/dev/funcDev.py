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


import random
import math

from dev.device import Device

class FuncDev(Device):
	def __init__(self, name, host):
		Device.__init__(self, name, host)
		self.devtype = "Load"

		# params
		self.functionType = "block"  # choose: block, sin, sawtooth, const, noise
		self.period = 60*60
		self.amplitude = 1000.0
		self.dutyCycle = 0.5
		self.timeOffset = 0.0
		self.powerOffset = 0.0
		
		# Compatibility to couple to uncontrollable controller
		self.filename = None
		self.filenameReactive  = None
		self.column = 0


	def timeTick(self, time):
		self.prunePlan()

		self.lockState.acquire()
		cons = self.readValue(time)

		for c in self.commodities:
			self.consumption[c] = complex(cons, 0.0)
		self.lockState.release()

	def logStats(self, time):
		self.lockState.acquire()
		try:
			for c in self.commodities:
				self.logValue("W-power.real.c." + c, self.consumption[c].real)
				self.logValue("W-power.imag.c." + c, self.consumption[c].imag)
				if c in self.plan and len(self.plan[c]) > 0:
					self.logValue("W-power.plan.real.c."+c, self.plan[c][0][1].real)
					self.logValue("W-power.plan.imag.c."+c, self.plan[c][0][1].imag)
		except:
			pass
		self.lockState.release()

	def shutdown(self):
		pass

#### INTERFACING
	def getProperties(self):
		r = Device.getProperties(self) 	# Get the properties of the overall Device class, which already includes global properties

		self.lockState.acquire()
		# Populate the result dict
		r['filename'] = None
		r['filenameReactive'] = None
		r['scaling'] = 1.0

		self.lockState.release()

		return r

#### LOCAL HELPERS
# Using the LoadDev structure to support uncontrollable controllers
	def readValueLineCache(self, time, filename=None):
		return self.readValue(time, filename)

	def readValue(self, time, filename=None):
		assert(filename == None)

		cons = 0.0
		relativeTime = (time + self.timeOffset) % self.period
		switchPoint = self.dutyCycle * self.period

		if self.functionType == "block":
			if relativeTime < switchPoint:
				cons = self.powerOffset + self.amplitude
			else:
				cons = self.powerOffset

		elif self.functionType == "sin":  # ignores dutyCycle
			cons = self.powerOffset + self.amplitude * math.sin(relativeTime * 2.0*math.pi/self.period)

		elif self.functionType == "sawtooth":
			if relativeTime < switchPoint:
				cons = self.powerOffset + self.amplitude * relativeTime/switchPoint
			else:
				cons = self.powerOffset

		elif self.functionType == "const":
			cons = self.powerOffset + self.amplitude

		elif self.functionType == "noise":
			cons = self.powerOffset + ((-0.5 + random.random()) * 2 * self.amplitude)

		else:
			assert(False)  # Unknown function type

		return cons

	def readValues(self, startTime, endTime, filename=None, timeBase=None):
		if timeBase is None:
			timeBase = self.timeBase

		result = []
		time = startTime
		while time < endTime:
			result.append(self.readValue(time, None))
			time += timeBase

		return result