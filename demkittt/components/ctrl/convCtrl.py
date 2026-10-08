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


from ctrl.devCtrl import DevCtrl
from opt.optAlg import OptAlg
from ctrl.optCtrl import OptCtrl

import numpy as np
import random
import copy

#Buffer vehicle controller
class ConvCtrl(DevCtrl):
	#Make some init function that requires the host to be provided
	def __init__(self,  name,  dev,  ctrl,  host):
		DevCtrl.__init__(self,   name,  dev,  ctrl,  host)

		self.devtype = "ConverterController"
		self.nextPlan = 0

		self.replanInterval = [4*900, 8*900]
		self.allowReplanning = True # Allow intermediate replanning for event-based planning

		self.priotizedCommodity = 'HEAT' # Default to none

			
	def timeTick(self, time):
		if self.useEventControl:
			if time >= self.nextPlan:
				self.requestIncentive()


	def doPlanning(self, signal, requireImprovement = True):
		self.lockPlanning.acquire()

		result =  self.convPlanning(signal, copy.deepcopy(self.candidatePlanning[self.name]), requireImprovement)
		self.candidatePlanning[self.name] = copy.deepcopy(result['profile'])

		self.lockPlanning.release()

		return result

	def doEventPlanning(self, signal):
		return self.convEventPlanning(signal)

	def convEventPlanning(self, signal):
		assert(False) #Untested!
		self.lockPlanning.acquire()
		self.updateDeviceProperties()

		currentPlan = {}
		for c in self.commodityIntersection(signal.commodities):
			currentPlan[c] = []
			for i in range(0,  len(signal.desired[c])):
				t = int((signal.time - (signal.time%signal.timeBase)) + i*self.timeBase)
				try:
					currentPlan[c].append(self.realized[c][t])
				except:
					currentPlan[c].append(complex(0,0))


		result = self.convPlanning(signal, copy.deepcopy(currentPlan), False)
		plan = copy.deepcopy(result['profile'])

		result['realized'] = {}
		for c in self.commodities:
			result['realized'][c] = list(np.array(result['profile'][c]) - np.array(currentPlan[c]))

		self.setPlan(plan, signal.time, signal.timeBase, True)

		self.lockPlanning.release()

		self.zCall(self.parent, 'updateRealized', copy.deepcopy(result['realized']))

	# Buffer planning shared between buffers and buffer converters
	def convPlanning(self, signal, currentPlanning, requireImprovement = True):
		devData = self.updateDeviceProperties()

		# Prepare the resultVector
		result = {}

		# Fix the data
		s = self.preparePlanningData(signal, currentPlanning)

		profileResult = {} # This is the thing we need to fill.
		for c in self.commodities:
			profileResult[c] = []

		# Obtain the desired target profile converted in the primary commodity
		target = []
		for t in range(0, s.planHorizon):
			desired = complex(0.0, 0.0)
			for c in self.commodities:
				desiredc = s.desired[c][t]

				if c in self.devData['cop']:
					desired += (desiredc * s.weights[c]) / self.devData['cop'][c]
				else:
					desired += desiredc * s.weights[c]

			if s.allowDiscomfort and self.priotizedCommodity is not None:
				for c in [self.priotizedCommodity]:
					if c in s.lowerLimits and c in s.upperLimits:
						desired = max(s.lowerLimits[c][t], min(s.desired[c][t], s.upperLimits[c][t]))
						desired = desired / self.devData['cop'][self.priotizedCommodity]

			target.append(desired)


		power = 0
		for desired in target:
			for c in devData['commoditiesIn']:
				power = max(devData['powers'][0], min(desired, devData['powers'][-1]))
				profileResult[c].append(power)

			for c in devData['commoditiesOut']:
				profileResult[c].append(power * devData['cop'][c])

		# #calculate the improvement
		# improvement = 0.0
		# if requireImprovement:
		# 	improvement = self.calculateImprovement(s.desired,  copy.deepcopy(self.candidatePlanning[self.name]),  profileResult)
		#
		# 	if signal.allowDiscomfort: #improvement <= 0.00001 and signal.allowDiscomfort:
		# 		improvement = self.calculateCommodityImprovement(s.desired[self.priotizedCommodity ],  copy.deepcopy(self.candidatePlanning[self.name][self.priotizedCommodity ]),  profileResult[self.priotizedCommodity ])
		#
		# 	if improvement <= 0.0000001:
		# 		improvement = 0.0
		# 		for c in self.commodities:
		# 			profileResult[c] = copy.deepcopy(self.candidatePlanning[self.name][c])
		#
		# #select a random new plan interval
		# self.nextPlan = self.host.time() + random.randint(self.replanInterval[0], self.replanInterval[1])
		#
		#
		# #send out the result
		# result['improvement'] = max(0.0, improvement)
		# result['profile'] = copy.deepcopy(profileResult)
		#
		# return result

		#calculate the improvement
		improvement = 0.0
		bimp = 0.0
		if requireImprovement:
			improvement = self.calculateImprovement(s.desired,  copy.deepcopy(self.candidatePlanning[self.name]),  profileResult)
			bimp =  self.calculateBoundImprovement(copy.deepcopy(self.candidatePlanning[self.name]), profileResult, signal.upperLimits, signal.lowerLimits, norm=2)

			if signal.allowDiscomfort: #improvement <= 0.00001 and signal.allowDiscomfort:
				improvement = self.calculateCommodityImprovement(s.desired[self.priotizedCommodity ],  copy.deepcopy(self.candidatePlanning[self.name][self.priotizedCommodity ]),  profileResult[self.priotizedCommodity ])
				if bimp >= -1:
					improvement = max(improvement, bimp)
				else:
					improvement = -1

			if improvement <= 0.0000001:
				improvement = 0.0
				for c in self.commodities:
					profileResult[c] = copy.deepcopy(self.candidatePlanning[self.name][c])

		#select a random new plan interval
		self.nextPlan = self.host.time() + random.randint(self.replanInterval[0], self.replanInterval[1])


		#send out the result
		result['boundsImprovement'] = bimp

		result['improvement'] = max(0.0, improvement)
		result['profile'] = copy.deepcopy(profileResult)

		return result