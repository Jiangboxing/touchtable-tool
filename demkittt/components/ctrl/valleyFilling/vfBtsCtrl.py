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

from ctrl.btsCtrl import BtsCtrl
from opt.optAlg import OptAlg
import math

#Electrical vehicle controller
class VfBtsCtrl(BtsCtrl):
	#Make some init function that requires the host to be provided
	def __init__(self,  name,  dev,  ctrl,  host):
		BtsCtrl.__init__(self,   name,  dev,  ctrl,  host)

		self.devtype = "VfBufferTimeshiftableController"

		self.chargeLevels = {}
		for c in self.commodities:
			self.chargeLevels[c] = [0]

	def timeTick(self,  time):
		if len(self.parent.runningJobs) > 0:
			for c in self.commodities:
				result = []
				result.append(self.parent.chargeLevel / len(self.parent.runningJobs))
				self.chargeLevels[c] = result

		self.setPlan(self.chargeLevels, time, self.timeBase)

	def logStats(self, time):
		# logging:
		for c in self.commodities:
			self.logValue("W-power.plan.c." + c, self.chargeLevels[c][0])

	def doJobPlanning(self, signal, startTime, endTime, job, weight):
		# Select the right section of the desired profile and limits based on the job times
		startIdx = 0
		endIdx = int((endTime - startTime) / self.timeBase)

		# Work to be done for power limits in case of curtailment / load shedding with EVs:
		# Need to alter the steering signal as this is an iterative process where predicted jobs may overlap
		# We need to take care of the result generated so far to allow for proper power limits
		# Important that we add the negative profileResult:

		# Either works for planning without events

		charge = job['remainingCharge']
		if charge > self.devData['capacity']:
			print("charge too big")
			charge = self.devData['capacity']

		chargingPowers = list(self.devData['chargingPowers'])
		for i in range(0, len(chargingPowers)):
			chargingPowers[i] *= weight

		targetSoC = weight * self.devData['capacity'] * (3600.0 / self.timeBase)

		# First we need to weave the input data:
		# The idea is to weave the different commodities to provide vectors to the buffer planning
		# This results in minor loss of options, but should give reasonable good results in little time
		#commodities = list(set.intersection(set(self.commodities), set(signal.commodities)))
		commodities = self.commodities

		# also, we need to scale the indexes
		startIdx *= len(commodities)
		endIdx *= len(commodities)

		desired = signal
		upperLimits = []
		lowerLimits = []

		'''
		desired = self.weaveDict(s.desired, commodities)
		upperLimits = []
		lowerLimits = []
		if len(signal.upperLimits) > 0:
			upperLimits = self.weaveDict(s.upperLimits, commodities)
		if len(signal.lowerLimits) > 0:
			lowerLimits = self.weaveDict(s.lowerLimits, commodities)

		if s.allowDiscomfort and not self.strictComfort and len(upperLimits) > 0 and len(lowerLimits) > 0:
			desiredCharge = weight * (self.devData['capacity'] - charge) * (3600.0 / signal.timeBase)

			# Perform load shedding / curtailment
			upper = 0
			lower = 0
			for val in upperLimits[startIdx:endIdx]:
				upper += min(val, chargingPowers[-1])
			for val in lowerLimits[startIdx:endIdx]:
				lower += max(val, chargingPowers[0])

			possible = max(lower, min(desiredCharge, upper))

			# Now se the target within SoC bounds:
			targetSoC = max(0, min(possible, weight * self.devData['capacity'] * (3600.0 / signal.timeBase)))
		'''

		# Now we call Thijs vd Klauw's buffer planning magic
		# But we scale all to Wtau instead of Wh
		opt = OptAlg()

		if self.devData['discrete']:
			p = opt.bufferPlanning(desired[startIdx:endIdx],
								   targetSoC,  # weight*self.devData['capacity']*(3600.0/signal.timeBase),
								   weight * (self.devData['capacity'] - charge) * (3600.0 / self.timeBase),
								   weight * self.devData['capacity'] * (3600.0 / self.timeBase),
								   [0.0] * (endIdx - startIdx),
								   chargingPowers, 0, 0,
								   lowerLimits[startIdx:endIdx], upperLimits[startIdx:endIdx],
								   self.useReactiveControl)
		else:
			if len(chargingPowers) == 3:
				# Martijn's bound-algorithm here, charging powers are: [0, min, max] with min and max positive.
				assert (chargingPowers[0] >= -0.0001 and chargingPowers[0] <= 0.0001)
				chargingPowers[0] = 0
				assert (chargingPowers[1] > 0.0 and chargingPowers[2] >= chargingPowers[1])
				p = opt.continuousBufferPlanningBounds(desired[startIdx:endIdx],
													   weight * self.devData['capacity'] * (3600.0 / self.timeBase),
													   chargingPowers[1], chargingPowers[2],
													   upperLimits[startIdx:endIdx])

			else:
				assert (len(chargingPowers) == 2)
				# Thijs vd Klauw's algorithms only take a [min, max]
				# p = opt.continuousBufferPlanningPositive(desired[startIdx:endIdx], weight*(charge)*(3600.0/signal.timeBase), chargingPowers[-1])
				p = opt.bufferPlanning(desired[startIdx:endIdx],
									   targetSoC,  # weight*self.devData['capacity']*(3600.0/signal.timeBase),
									   weight * (self.devData['capacity'] - charge) * (3600.0 / self.timeBase),
									   weight * self.devData['capacity'] * (3600.0 / self.timeBase),
									   [0.0] * (endIdx - startIdx),
									   [], chargingPowers[0], chargingPowers[-1],
									   lowerLimits[startIdx:endIdx], upperLimits[startIdx:endIdx],
									   self.useReactiveControl)

		return opt.fillLevel