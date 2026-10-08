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


from ctrl.thermal.thermalBufConvCtrl import ThermalBufConvCtrl
from opt.optAlg import OptAlg
import util.helpers

import copy
import numpy as np
import math

#Buffer converter controller
class ThermalUncontrollableCtrl(ThermalBufConvCtrl):
	def __init__(self,  name,  dev,  ctrl,  host):
		ThermalBufConvCtrl.__init__(self, name, dev, ctrl, host)

		self.devtype = "UncontrollableController"



	def doPrediction(self,  startTime,  endTime, force = False):
		# Synchronize the device state:
		self.updateDeviceProperties()

		if self.lastPrediction < self.host.time() or force:
			result = [0.0] * int((endTime - startTime) / self.timeBase)

			if len(self.dev.thermostats) > 0:
				# Predict heat demand to heat zones
				producingPowers = [ self.dev.producingPowers[0] / float(len(self.dev.thermostats)), self.dev.producingPowers[-1] / float(len(self.dev.thermostats)) ]

				for thermostat in self.dev.thermostats:
					result = list(np.array(result) + np.array(thermostat.doPrediction(startTime, endTime, producingPowers, self.timeBase) ) )

			# Predict hot water demand for taps
			for dhw in self.dev.dhwTaps:
				result = list(np.array(result) + np.array(dhw.doPrediction(startTime, endTime, self.timeBase)) )

			self.predictionCache = list(result)
			self.lastPrediction = self.host.time()

		result = self.predictionCache

		return result



	# Bufferplanning shared between buffers and bufferconverters
	def bufPlanning(self, signal, currentPlanning, consumption=[], requireImprovement = True, devData = None):
		if devData is None:
			devData = self.updateDeviceProperties()

		# Prepare the resultVector
		result = {}

		# Synchronize the device state:
		self.updateDeviceProperties()

		# Fix the data
		s = self.preparePlanningData(signal, currentPlanning)

		p = list(consumption)

		profileResult = {}
		# Now translate into commodities
		for c in self.commodities:
			if c != 'HEAT':
				profileResult[c] = [math.copysign(x/devData['cop'][c], devData['cop'][c]) for x in p]
			else:
				profileResult[c] = list(p)

		#calculate the improvement
		improvement = 0.0

		#send out the result
		result['improvement'] = max(0.0, improvement)
		result['profile'] = copy.deepcopy(profileResult)

		return result

	#Override setPlan to include expected SoC:
	def setPlan(self, plan, time, timeBase):
		assert(self.lockPlanning.acquire(blocking=False) == False)

		self.realized = {}
		result = {}

		for c in self.commodities:
			devPlan = []

			if c not in self.realized:
				self.realized[c] = {}
			if c not in self.plan:
				self.plan[c] = {}

			for i in range(0,  len(plan[c])):
				#create the local plan for the device.
				t = int(time + i*timeBase)
				tup = (t, plan[c][i])
				devPlan.append(tup)

				#create the plan for the controller, which has to synchronize with the timebase of the controller
				if self.useEventControl:
					t = int(time - (time%timeBase) + i*timeBase)
					self.realized[c][t] = plan[c][i]

					if self.forwardLogging:
						self.logValue("W-power.realized.imag.c." + c,self.realized[c][t].real,t)
						self.logValue("W-power.realized.real.c." + c,self.realized[c][t].imag,t)

			devPlan.sort()
			result[c] = list(devPlan)

		self.lastPlannedTime = (len(plan[self.commodities[0]]) * timeBase) + time

		#send this profile to the device
		# HACK: We keep the device "stupid"
		# self.zCall(self.dev, 'setPlan', result)

		#ThermalBufConvCtrl.setPlan(self, plan, time, timeBase)
