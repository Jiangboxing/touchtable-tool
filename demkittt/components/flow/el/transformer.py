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

from flow.el.elNode import ElNode
from flow.el.mvCable import MvCable
from flow.el.mvNode import MvNode

import math

# TODO implement checkViolations(). See T199

# Dyn5 MV-LV Distribution Transformer
# Convention: attributes without suffix are from the LV/secondary side, attributes with suffix 'primary' are from the MV side.
# Only logs values and checks violations from secondary side (LV).

class Transformer(ElNode):
	def __init__(self,  name,  flowSim, host):
		ElNode.__init__(self,  name,  flowSim, host)
		
		self.devtype = "ElectricityTransformer"

		# Bookkeeping
		self.load = 0.0  # VA
		
		# Parameters
		self.nominalVoltage = [0.0, 230.0, 230.0, 230.0]
		self.angles = [0.0, -150.0, 90.0, -30.0]
		
		self.nominalVoltagePrimary = [0.0, 6062.0, 6062.0, 6062.0]  # =10.5kV line-to-line
		self.anglesPrimary = [0.0, 0.0, -120.0, 120.0]

		self.turnRatio = max(self.nominalVoltagePrimary) / max(self.nominalVoltage)

		# Taps
		self.taps = [2, 1, 0, -1, -2]  # positive implies higher LV voltage
		self.tapStep = 250.0 / 10500.0
		self.tap = 2
		
		# Limits
		self.maxVoltage = 253.0
		self.minVoltage = 207.0
		self.maxVuf = 2 # %
		
		self.maxVoltagePrimary = 6062.0 * 1.1
		self.minVoltagePrimary = 6062.0 * 0.9
		self.maxVufPrimary = 2.0 # %
	
		# Reference: "Netten voor distributie van electriciteit" by Phase to Phase, 2012, section 8.3 onwards
		# https://phasetophase.nl/boek/index.html
        # Proper values can be obtained through the Types.xlsx file provided with the Gaia Demo download

		# These are some example values
		self.ratedLoad = 250000.0  # VA
		self.noLoadLosses = 350.0  # W
		self.ratedLoadLosses = 2200.0  # W

	@property
	def tap(self):
		return self.__tap

	@tap.setter
	def tap(self, val):
		# Update turn ratio
		defaultTurnRatio = max(self.nominalVoltagePrimary) / max(self.nominalVoltage)
		self.turnRatio = (1. - self.taps[val] * self.tapStep) * defaultTurnRatio

		self.__tap = val

	def conductors(self):
		# Convention used here is that the first index is always the neutral conductor, even for nodes without a neutral conductor.
		return range(0, len(self.voltage))

	def conductorsPrimary(self):
		return range(1, len(self.voltage))
		
	def doForwardSweep(self, previousNode, cable):
		assert(isinstance(cable, MvCable))
		assert(isinstance(previousNode, MvNode))

		# Save the previous voltage
		self.prevVoltage = list(self.voltage)

		# Calculate the voltage on the primary side
		voltagePrimary = [complex(0.0, 0.0)] * 4
		for conductor in self.conductorsPrimary():
			voltagePrimary[conductor] = previousNode.voltage[conductor] - cable.voltageDrop(conductor)

		# Transform voltages
		assert(len(self.voltage) == 4 and len(self.nominalVoltagePrimary) == 4)
		self.voltage[0] = complex(0.0, 0.0) # Grounded
		self.voltage[1] = (voltagePrimary[2] - voltagePrimary[1]) / math.sqrt(3.0) / self.turnRatio
		self.voltage[2] = (voltagePrimary[3] - voltagePrimary[2]) / math.sqrt(3.0) / self.turnRatio
		self.voltage[3] = (voltagePrimary[1] - voltagePrimary[3]) / math.sqrt(3.0) / self.turnRatio
	
	def doBackwardSweep(self, cable):
		current = [complex(0.0, 0.0)] * 4
		currentPrimary = [complex(0.0, 0.0)] * 4
		
		assert(isinstance(cable, MvCable))
		
		# Devices connected to the transformer
		for meter in self.meters:
			for i in range(1, len(self.voltage)):
				current[i] += ( (meter.consumption/3) / self.getLNVoltage(i)).conjugate()
		for meter in self.metersL1:
			current[1] += (meter.consumption / self.getLNVoltage(1)).conjugate()
		for meter in self.metersL2:
			current[2] += (meter.consumption / self.getLNVoltage(2)).conjugate()
		for meter in self.metersL3:
			current[3] += (meter.consumption / self.getLNVoltage(3)).conjugate()
		
		# Add the losses of the transformer
		losses = self.getLosses()
		for i in range(1, len(self.voltage)):
			current[i] += ( (losses/3) / self.getLNVoltage(i)).conjugate()
		
		# Sum the currents from all LV cables:
		for outCable in self.edges:
			if outCable != cable:
				for conductor in self.conductors():
					current[conductor] += outCable.current[conductor]

		current[0] = (-current[1] + -current[2] + -current[3])

		# Transform to primary side
		currentBA = current[1] / self.turnRatio
		currentCB = current[2] / self.turnRatio
		currentAC = current[3] / self.turnRatio
		
		currentPrimary[1] = (currentAC - currentBA) / math.sqrt(3.0)
		currentPrimary[2] = (currentBA - currentCB) / math.sqrt(3.0)
		currentPrimary[3] = (currentCB - currentAC) / math.sqrt(3.0)
		
		# Set the result on the MV cable
		cable.current = list(currentPrimary)
		
		# Store load
		self.load = 0.0
		for i in range(1, len(self.voltage)):
			self.load += abs(self.getLNVoltage(i)*current[i].conjugate())
		
	def getLosses(self):
		# Simple losses model according to IEEE Std C57.91
		# Note: does not compensate for different tap positions
		K = self.load/self.ratedLoad

		result = self.noLoadLosses
		result += K*K * self.ratedLoadLosses
		
		return result

	def logStats(self, time):
		self.logValue("W-power.", self.load)
		self.logValue("W-losses", self.getLosses())

		ElNode.logStats(self, time)
