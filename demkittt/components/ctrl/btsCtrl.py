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


from ctrl.tsCtrl import TsCtrl
from opt.optAlg import OptAlg

import copy
import math

#Electrical vehicle controller
class BtsCtrl(TsCtrl):
	#Make some init function that requires the host to be provided
	def __init__(self,  name,  dev,  ctrl,  host):
		TsCtrl.__init__(self,   name,  dev,  ctrl,  host)

		self.devtype = "BufferTimeshiftableController"

	def doJobPlanning(self, signal, job, weight, profileResult, devData=None):
		# Select the right section of the desired profile and limits based on the job times
		startIdx = max(0, int(math.ceil((job['startTime']-signal.time)/signal.timeBase)))
		endIdx = max(0,  int(math.floor((job['endTime']-signal.time)/signal.timeBase)))

		if devData is None:
			devData = self.updateDeviceProperties()

		# Work to be done for power limits in case of curtailment / load shedding with EVs:
		# Need to alter the steering signal as this is an iterative process where predicted jobs may overlap
		# We need to take care of the result generated so far to allow for proper power limits
		# Important that we add the negative profileResult:

		# Either works for planning without events
		s = copy.deepcopy(signal)

		charge = job['charge']
		if charge > devData['capacity']:
			print("charge too big")
			charge = devData['capacity']

		chargingPowers  = list(devData['chargingPowers'])
		for i in range(0,  len(chargingPowers)):
			chargingPowers[i] *= weight

		targetSoC = weight*devData['capacity']*(3600.0/signal.timeBase)

		# First we need to weave the input data:
		# The idea is to weave the different commodities to provide vectors to the buffer planning
		# This results in minor loss of options, but should give reasonable good results in little time
		commodities = list(set.intersection(set(self.commodities), set(signal.commodities)))

		# also, we need to scale the indexes
		startIdx *= len(commodities)
		endIdx *= len(commodities)

		desired = self.weaveDict(s.desired, commodities)
		prices = self.weaveDict(s.prices, commodities)

		upperLimits = []
		lowerLimits = []
		if len(signal.upperLimits) > 0:
			upperLimits = self.weaveDict(s.upperLimits, commodities)
		if len(signal.lowerLimits) > 0:
			lowerLimits = self.weaveDict(s.lowerLimits, commodities)

		if s.allowDiscomfort and not self.strictComfort and len(upperLimits) > 0 and len(lowerLimits) > 0:
			desiredCharge = weight*charge*(3600.0/signal.timeBase)

			# Perform load shedding / curtailment
			upper = 0
			lower = 0
			for val in upperLimits[startIdx:endIdx]:
				upper += max(chargingPowers[0], min(val.real, chargingPowers[-1]) )
			for val in lowerLimits[startIdx:endIdx]:
				lower += min(chargingPowers[-1], max(val.real, chargingPowers[0]) )

			possible = ( weight*(devData['capacity']-charge)*(3600.0/signal.timeBase) ) + ( max(lower, min(desiredCharge, upper) ) )
			targetSoC = max(0, min(possible, weight*devData['capacity']*(3600.0/signal.timeBase)))

		# Now we call Thijs vd Klauw's buffer planning magic
		# But we scale all to Wtau instead of Wh
		opt = OptAlg()
		
		if devData['discrete']:
			p = opt.bufferPlanning(desired[startIdx:endIdx],
								   targetSoC, #weight*devData['capacity']*(3600.0/signal.timeBase),
								   weight*(devData['capacity']-charge)*(3600.0/signal.timeBase),
								   weight*devData['capacity']*(3600.0/signal.timeBase),
								   [0.0] * (endIdx-startIdx),
								   chargingPowers, 0, 0,
								   lowerLimits[startIdx:endIdx], upperLimits[startIdx:endIdx],
								   self.useReactiveControl,
								   prices[startIdx:endIdx],
								   s.profileWeight,
								   intervalMerge = [1]*len(desired) ) # <- Here we need to do some magic.
		else:
			if len(chargingPowers) == 3:
				# Martijn's bound-algorithm here, charging powers are: [0, min, max] with min and max positive.
				assert(chargingPowers[0] >= -0.0001 and chargingPowers[0] <= 0.0001)
				chargingPowers[0] = 0
				assert(chargingPowers[1] > 0.0 and chargingPowers[2] >= chargingPowers[1])
				p = opt.continuousBufferPlanningBounds(desired[startIdx:endIdx],
									weight*charge*(3600.0/signal.timeBase),
									chargingPowers[1], chargingPowers[2],
									upperLimits[startIdx:endIdx])
				
			else:
				assert(len(chargingPowers) == 2)
				# Thijs vd Klauw's algorithms only take a [min, max]
				# p = opt.continuousBufferPlanningPositive(desired[startIdx:endIdx], weight*(charge)*(3600.0/signal.timeBase), chargingPowers[-1])
				p = opt.bufferPlanning(desired[startIdx:endIdx],
									   targetSoC, #weight*devData['capacity']*(3600.0/signal.timeBase),
									   weight*(devData['capacity']-charge)*(3600.0/signal.timeBase),
									   weight*devData['capacity']*(3600.0/signal.timeBase),
									   [0.0] * (endIdx-startIdx),
									   [], chargingPowers[0], chargingPowers[-1],
									   lowerLimits[startIdx:endIdx], upperLimits[startIdx:endIdx],
									   self.useReactiveControl,
									   prices[startIdx:endIdx],
									   s.profileWeight )

		# Sort back the result
		pr = self.unweaveVec(p, commodities)

		#now add the profile to the result vector
		for c in commodities:
			for i in range(0,  len(pr[c])):
				profileResult[c][i + int(startIdx/len(commodities))] += pr[c][i]

		return profileResult



	def requestCancelation(self):
		assert(False) # Unimplemented at this moment
		# Some example code as inspiration for this function
		# self.updateDeviceProperties()
		# result = {}
		# profile = []
		#
		# endIdx = max(0,  int(math.floor((self.devData['currentJob']['endTime']-self.host.time()/self.timeBase))))
		#
		# for i in range(0, endIdx):
		# 	time = (self.host.time() - (self.host.time()%self.timeBase)) + i*self.timeBase
		# 	profile.append(self.plan[time])
		#
		# result['profile'] = list(profile)
		#
		# self.zCall(self.parent, 'requestCancelation', result)


##### PREDICTION
	def doPrediction(self,  startTime,  endTime):
		# Synchronize the device state:
		self.updateDeviceProperties()

		result = []

		#first check if we need to add a running job:
		if not self.useEventControl:
			#also add the current job if it applies:
			if self.devDataPlanning['available'] and self.devDataPlanning['soc'] < self.devDataPlanning['capacity']:
				j = {}
				j['startTime'] = self.host.time()
				j['endTime'] = self.devDataPlanning['currentJob']['endTime']
				j['charge'] = self.devDataPlanning['capacity'] - self.devDataPlanning['soc']
				d = (j,  1) #add weight
				result.append(d)

		if self.perfectPredictions:
			#Since we use predictions, we may have overlap with already scheduled (realized) jobs
			#Hence we need to change the start time if a current job is running:
			if self.devDataPlanning['available']:
				startTime = self.devDataPlanning['currentJob']['endTime']

			for job in self.devDataPlanning['jobs']:
				if(job[1]['startTime'] >= startTime and job[1]['endTime'] <= endTime):
					#Need to create a new job for the sake of time in the controller
					j = {}
					j['startTime'] = job[1]['startTime']
					j['endTime'] = job[1]['endTime']
					j['charge'] = job[1]['charge']
					d = (j,  1) #add weight
					result.append(d)

				if(job[1]['startTime'] > endTime):
					break

		#real predictions
		else:
			#Since we use predictions, we may have overlap with already scheduled (realized) jobs
			#Hence we need to change the start time if a current job is running:
			if self.devDataPlanning['available']:
				startTime = self.devDataPlanning['currentJob']['endTime']

			for job in self.devDataPlanning['jobs']:
				for week in range(1,  5):
					w = 0.125
					if week == 1:
						w = 0.5
					if week == 2:
						w = 0.25

					offset = 3600*24*7*week
					if(job[1]['startTime'] >= startTime-offset and min(job[1]['endTime'], job[1]['startTime']+24*3600) <= endTime-offset):
						j = {}
						j['startTime'] = max(job[1]['startTime']+offset, startTime)
						j['endTime'] = job[1]['endTime']+offset
						j['charge'] = job[1]['charge']
						d = (j,  w)
						result.append(d)

					if(job[1]['startTime'] > endTime-offset):
						break

		return result