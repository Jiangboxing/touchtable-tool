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


from ctrl.loadCtrl import LoadCtrl
import util.helpers
import copy

class CurtCtrl(LoadCtrl):
	def __init__(self,  name,  dev, parent,  host):
		LoadCtrl.__init__(self,  name,  dev,  parent,  host)

		self.devtype = "CurtailableCtrl"

	def doPlanning(self,  signal,  requireImprovement = True):
		self.lockPlanning.acquire()
		result = {}

		assert(self.timeBase >= self.devDataPlanning['timeBase']) # The other direction is untested and probably broken!
		assert(self.timeBase % self.devDataPlanning['timeBase'] == 0) # Again, otherwise things are very likely to break

		time = signal.time
		timeBase = signal.timeBase
		signal = self.preparePlanningData(signal, copy.deepcopy(self.candidatePlanning[self.name]))

		if self.predictionPlanningTime < time:
			p = {}

			#just obtain the profile from a prediction. There is no flex to change this anyways
			for c in self.commodities:
				p[c] = self.doPrediction(time-(time%timeBase),  time-(time%timeBase)+(timeBase*len(signal.desired[c])))
				if len(p[c]) != signal.planHorizon:
					p[c] = util.helpers.interpolate(p[c], signal.planHorizon)

			# Condirm bookkeeping
			self.predictionPlanning = copy.deepcopy(p)
			self.predictionPlanningTime = time


		p = copy.deepcopy(self.predictionPlanning)

		# Just obtain the profile from a prediction. There is no flex to change this anyways
		for c in self.commodities:
			# Perform load shedding or curtailment, keeping the sign of the load however.
			# E.g. producers can only curtail and are <= 0 W, loads will only shed and are >= 0 W
			if signal.allowDiscomfort and not self.strictComfort and c in signal.upperLimits:
				for i in range(0, len(p[c])):
					if p[c][i].real > signal.upperLimits[c][i].real:
						if self.devDataPlanning['onOffDevice']:
							p[c][i] = complex(0.0, 0.0)
						else:
							# FIXME We do not support reactive control here yet
							if p[c][i].real <= 0:
								p[c][i] = complex( min(0, max(p[c][i].real, signal.upperLimits[c][i].real) ), p[c][i].imag)
							else:
								p[c][i] = complex( max(0, min(p[c][i].real, signal.upperLimits[c][i].real) ), p[c][i].imag)

			if signal.allowDiscomfort and not self.strictComfort and c in signal.lowerLimits:
				for i in range(0, len(p[c])):
					if p[c][i].real < signal.lowerLimits[c][i].real:
						if self.devDataPlanning['onOffDevice']:
							p[c][i] = complex(0.0, 0.0)
						else:
							if p[c][i].real <= 0:
								p[c][i] = complex(min(0, max(p[c][i].real, signal.lowerLimits[c][i].real) ), p[c][i].imag)
							else:
								p[c][i] = complex(max(0, min(p[c][i].real, signal.lowerLimits[c][i].real) ), p[c][i].imag)

		#calculate the improvement
		# improvement = 0.0
		# if requireImprovement:
		# 	improvement = self.calculateImprovement(signal.desired,  copy.deepcopy(self.candidatePlanning[self.name]),  p)
		#
		# 	if improvement <= 0.0 and signal.allowDiscomfort:
		# 		# Obeying limits may result in a negative improvement, but considering the case, it can be seen as a positive one.
		# 		# Especially if, by shifting other devices, a consuming device such as a washing machine or EV can increase its power consumption
		# 		# This does indicate increased comfort and therefore can be seen as an improvement to us.
		# 		improvement = 0.0
		# 		for c in self.commodities:
		# 			for j in range(0, len(p)):
		# 				improvement += (p[c][j] - self.candidatePlanning[self.name][c][j]).real
		#
		# 	if improvement > 0.0:
		# 		self.candidatePlanning[self.name] = dict(p)
		#
		# else:
		# 	self.candidatePlanning[self.name] = dict(p)
		#
		# #send out the result
		# result['improvement'] = max(0.0, improvement)
		# result['profile'] = copy.deepcopy(self.candidatePlanning[self.name])
		#
		# self.lockPlanning.release()
		#
		# return result

		#calculate the improvement
		improvement = 0.0
		bimp = 0.0
		if requireImprovement:
			improvement = self.calculateImprovement(signal.desired,  copy.deepcopy(self.candidatePlanning[self.name]),  p)
			bimp = self.calculateBoundImprovement(copy.deepcopy(self.candidatePlanning[self.name]), p, signal.upperLimits, signal.lowerLimits, norm=2)

			if signal.allowDiscomfort:
				# Obeying limits may result in a negative improvement, but considering the case, it can be seen as a positive one.
				# Especially if, by shifting other devices, a consuming device such as a washing machine or EV can increase its power consumption
				# This does indicate increased comfort and therefore can be seen as an improvement to us.
				improvement = max(bimp, improvement)

			if bimp < -1:
				improvement = 0.0

			if improvement > 0.0:
				self.candidatePlanning[self.name] = dict(p)

		else:
			self.candidatePlanning[self.name] = dict(p)

		#send out the result
		result['boundsImprovement'] = bimp
		result['improvement'] = max(0.0, improvement)
		result['profile'] = copy.deepcopy(self.candidatePlanning[self.name])

		self.lockPlanning.release()

		return result
