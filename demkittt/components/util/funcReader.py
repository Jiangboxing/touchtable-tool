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

from itertools import islice
from util.reader import Reader
import math

class FuncReader(Reader):
	def __init__(self,  dataSource=None, timeBase = 900, column = -1, timeOffset=0):
		Reader.__init__(self, timeBase, column, timeOffset)

		# params
		self.functionType = "const"  # choose: block, sin, sawtooth, const, noise
		self.period = 60*60
		self.amplitude = 0.0
		self.dutyCycle = 0.5
		self.timeOffset = timeOffset
		self.powerOffset = 0.0

	def retrieveValues(self, startTime, endTime = None, value = None, tags = None):
		result = []
		for i in range(startTime, endTime, self.timeBase):
			result.append(self.getValue(i))

		return result

	def getValue(self, time):
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

		return complex(cons, 0.0)