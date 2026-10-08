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


import numpy as np
import math
from collections import OrderedDict
import threading

from ctrl.optCtrl import OptCtrl
from data.psData import PSData
from util.funcReader import FuncReader

import copy

class GroupCtrlV4(OptCtrl):
	def __init__(self,  name,  host, parent = None, congestionPoint = None, dev=None):
		OptCtrl.__init__(self,  name,  host)
		self.devtype = "GroupController"

		self.parent = parent

		# This boolean can be used in the future to check whether the connection to the parent is still active
		self.parentConnected = False

		self.maxIters = 200
		self.planHorizon = 192
		self.planInterval = 96

		# Algorithms speedup through simultaneous commits:
		# Use these functions with care! MultipleCommits usually leads to better results
		# self.multipleCommits = True				# Allow multiple commits to speedup the optimization
		self.multipleCommitsDivisor = 2			# Divisor to reduce the number of selected commits for each iteration

		# Use with care. Pruning is usually only really useful on HEMS level, or when a lot of houses have little to no flexibility
		# self.pruneInflexibleChildren = False		# Remove children with no to little improvement for following iterations
		# self.initialPlan = False

		self.enabled = True			# Is the controller connected?

		# Objectives
		self.desired = None
		self.prices = None
		self.congestionPoint = congestionPoint

		self.localWeight = { 'ELECTRICITY':0, 'EL1': 0, 'EL2': 0, 'EL3': 0, 'HEAT': 0, 'NATGAS': 0 }
		self.localDesired = None

		#accounting:
		self.nextPlan = -1
		self.alignNextPlan = host.startTime  # To align plannings with day starts from a config
		
		self.isFleetController = False # We need to set this explicitly, however, rootnodes become fleet controllers automatically in the startup!
		self.minProblem = 5000 # if this controller is a fleet controller, this is used to determine whether the parents problem should be used instead.
										# If the problem is too small, the higher level controller will be asked

		# DEBUG PARAM
		self.localDiscomfort = False

		# Locks
		self.lockSyncPlanning = threading.Lock()

		# Link to a smart meter (device) for details
		self.dev = dev

	def preTick(self, time):
		if (self.parent == None or self.parentConnected == False) and time >= self.nextPlan: #  or self.parentConnected == False


			if self.nextPlan == -1: # First time
				# Run a first planning in the same thread
				self.initiatePlanning()
			else:
				# Start the planning in a separate thread
				self.runInThread('initiatePlanning')
				
	def timeTick(self, time):
		pass
		
	def logStats(self, time):				
		#logging:
		t = time - time%self.timeBase
		try:
			for c in self.commodities:
				self.logValue("W-power.plan.real.c." + c, self.plan[c][t].real)
				self.logValue("W-power.plan.imag.c." + c, self.plan[c][t].imag)
				self.logValue("W-power.target.real.c." + c, self.desired[c].getValue(t).real)
				self.logValue("W-power.target.imag.c." + c, self.desired[c].getValue(t).imag)
				self.logValue("n-price.signal.real.c." + c, self.prices[c].getValue(t).real)
				if self.useEventControl:
					self.logValue("W-power.realized.imag.c." + c, self.realized[c][t].imag)
					self.logValue("W-power.realized.real.c." + c, self.realized[c][t].real)
		except:
			pass


		for c in self.commodities:
			try:
				# Objective of the plan
				obj = self.desired[c].getValue(time)
				self.logValue("n-obj-planning." + c, abs(self.plan[c][t]-obj))
				self.logValue("n-obj-planning-squared." + c, pow(abs(self.plan[c][t]-obj),2) )
				if self.useEventControl:
					self.logValue("n-obj-realized." + c, abs(self.realized[c][t]-obj))
					self.logValue("n-obj-realized-squared." + c, pow(abs(self.realized[c][t]-obj), 2) )

				if self.dev != None:
					# Compare planning to real usage
					if c in self.dev:
						try:
							self.dev[c].measure(time)
							val = self.dev[c].consumption.real
							obj = obj.real
							self.logValue("n-obj-measured." + c, abs(val-obj))
							self.logValue("n-obj-measured-squared." + c, pow(abs(val-obj), 2) )

							self.logValue("n-deviation-planning." + c, abs(self.plan[c][t]-val))
							self.logValue("n-deviation-planning-squared." + c, pow(abs(self.plan[c][t]-val), 2) )
							if self.useEventControl:
								self.logValue("n-deviation-realized." + c, abs(self.realized[c][t]-val))
								self.logValue("n-deviation-realized-squared." + c, pow(abs(self.realized[c][t]-val), 2) )

							self.logValue("n-costs.c."+ c, val*self.prices[c].getValue(time).real)
						except:
							pass
			except:
				pass


	#Start and end-functions for system/sim startup and shutdown
	def startup(self):
		assert(self.enabled == True) 	# Disconnected group controllers are not officially supported, only some code is in place.
										# However, disconnection / reconnection and synchronization upon these events must still be implemented!

		# Establish Controller <-> groupController connection
		if self.parent is not None:
			if not isinstance(self.parent, str):
				self.parent.appendChild(self)
			else:
				self.zCall(self.parent, 'appendChild', self.name)
			self.parentConnected = True

		else: # No parent, thus rootnode = fleet controller:
			self.isFleetController = True
			self.parentConnected = False

		if(self.desired == None):
			self.desired = {}
			for c in self.commodities:
				self.desired[c] = FuncReader(timeOffset = self.host.timeOffset)
				# self.desired[c].functionType = "sin"
				# self.desired[c].period = 12*3600
				# self.desired[c].amplitude = 5000
				# self.desired[c].dutyCycle = 0.5
				# self.desired[c].powerOffset = 0

		if (self.prices == None):
			self.prices = {}
			for c in self.commodities:
				self.prices[c] = FuncReader(timeOffset = self.host.timeOffset)
		# 		self.prices[c].functionType = "sin"
		# 		self.prices[c].period = 12*3600
		# 		self.prices[c].amplitude = -5000
		# 		self.prices[c].dutyCycle = 0.5
		# 		self.prices[c].powerOffset = 2500
		# self.profileWeight = 0 # Beta in the work by Thijs van der Klauw, should be between 0-1. 1 = normal profile steering, 0 = prices only

		if self.localDesired is None:
			self.localDesired = {}
			for c in self.commodities:
				self.localDesired[c] = FuncReader(timeOffset = self.host.timeOffset)
				# self.localDesired[c].functionType = "sin"
				# self.localDesired[c].period = 12*3600
				# self.localDesired[c].amplitude = 5000
				# self.localDesired[c].dutyCycle = 0.5
				# self.localDesired[c].offset = 0

		if self.alignNextPlan is None:
			self.alignNextPlan = 0
		else:
			self.alignNextPlan = self.alignNextPlan % (self.planInterval * self.timeBase)

		self.nextPlan = -1

		# persistence
		if self.persistence != None:
			watchlist = self.watchlist # + ["nextPlan"] # FIXME Enforcing a new plan to be sure, this line can probably be removed
			self.persistence.setWatchlist(watchlist)

	def shutdown(self):
		pass

	def initiatePlanning(self, lock=False):
		if not lock:
			self.lockSyncPlanning.acquire()

			if self.zCall(self.host, 'time') < self.nextPlan:
				# Planning already performed
				self.lockSyncPlanning.release()
				return

		s = PSData()
		s.copyFrom(self)
		s.time = self.host.time()-(self.host.time()%self.timeBase)
		s.timeBase = self.timeBase

		# Stimuli:
		desired = {}
		for c in self.commodities:
			desired[c] = self.desired[c].readValues(s.time, s.time+s.planHorizon*s.timeBase)
		prices = {}
		for c in self.commodities:
			prices[c] = self.prices[c].readValues(s.time, s.time+s.planHorizon*s.timeBase)

		s.desired = copy.deepcopy(desired)
		s.prices = copy.deepcopy(prices)

		# Synchronize data used for planning
		self.startSynchronizedPlanning(s)

		# Perform the planning
		self.doInitialPlanning(s)
		self.doPlanning(s)

		self.planningWinners = []
		self.setPlanningWinner(s.time, s.timeBase, self.name)

		# Incorporate updates that happened in the meanwhile
		self.endSynchronizedPlanning(s)

		if not lock:
			# We need to release the lock ourselves (running in a separate thread)
			self.lockSyncPlanning.release()

	def doPlanning(self, signal, reset = True):
		# We need to reset if we are planning, reset = False during initial planning to establish a feasible starting point!
		if reset:
			self.resetIteration(signal.source, [])

		# Store the initialplan
		ip = copy.deepcopy(self.candidatePlanning[self.name])
		bip = 0

		s = PSData()
		s.copy(signal)

		# Now test whether the current (in most cases the initial one) falls within the limits:
		withinLimits = True

		self.localDiscomfort = False # DEBUG, reconsider

		# result = self.iterativePlanning(s)
		# bip += result['boundsImprovement']

		# Note, only local limits need to be checked!
		# FIXME congestionpoints should have the option to provide a vector of bounds instead. T211
		# 1. First check for feasibility
		if self.congestionPoint is not None:
			for c in self.commodities:
				# s.desired[c] = list( np.array(s.desired[c]) + np.array(list(self.candidatePlanning[self.name][c])))
				if not self.checkBoundViolations(c, self.candidatePlanning[self.name][c]):
					withinLimits = False
					# Change the objective for this commodity now to steer the group towards a feasible solution:
					for i in range(0, len(s.desired[c])):
						s.desired[c][i] = max(self.congestionPoint.getLowerLimit(c).real, min(s.desired[c][i].real, self.congestionPoint.getUpperLimit(c).real))

			# 1.1. If we are not within limits, we need to do so first
			if not withinLimits:
				# Initial planning to resolve the problem with the new signal
				if self.parent is None or self.name=="HouseController-House-4":
					self.logMsg("Initial planning not within limits, executing an iterative planning phase to steer towards a feasible solution.")
				result = self.iterativePlanning(s)
				bip += result['boundsImprovement']

				# 1.2. Now check whether we are in bounds again:
				withinLimits = True
				for c in self.commodities:
					if not self.checkBoundViolations(c, result['profile'][c]):
						withinLimits = False


		# 3. New planning with curtailment if we are still violating limits (only when discomfort is allowed)
		if not withinLimits and (signal.allowDiscomfort or self.strictComfort == False):
		#if not withinLimits and self.strictComfort == False:
		# if self.congestionPoint is not None and not withinLimits and signal.allowDiscomfort or self.strictComfort == False:
			if self.parent is None or self.name=="HouseController-House-4":
				self.logWarning("Congestionpoint bounds violated, executing load shedding and/or production curtailment to resolve the issue.")
			# We are still violating the limits, so there is no feasible solution with maintaining comfort
			# So we can perform load shedding
			# This is the part where the PhD thesis of Thijs and Gerwin break and normally would return the best (infeasible) solution
			# However, if we allow discomfort, we can now attempt an iteration with load shedding / curtailment.
			s = PSData()
			s.copy(signal)
			s.allowDiscomfort = True
			self.localDiscomfort = True
			for c in self.commodities:
				# s.desired[c] = list( np.array(s.desired[c]) + np.array(list(self.candidatePlanning[self.name][c])))
				if not self.checkBoundViolations(c, result['profile'][c]):
					# Change the objective for this commodity now to steer the group towards a feasible solution:
					for i in range(0, len(s.desired[c])):
						s.desired[c][i] = max(self.congestionPoint.getLowerLimit(c).real, min(s.desired[c][i].real, self.congestionPoint.getUpperLimit(c).real))
			result = self.iterativePlanning(s)
			bip += result['boundsImprovement']

		elif withinLimits:
			if self.parent is None or self.name=="HouseController-House-4":
				self.logMsg("Executing a normal iterative planning phase.")
			s = PSData()
			s.copy(signal)
			result = self.iterativePlanning(s)
			bip += result['boundsImprovement']


		withinLimits = True
		for c in self.commodities:
			if not self.checkBoundViolations(c, result['profile'][c]):
				withinLimits = False


		# Bookkeeping of the planning
		self.lastPlannedTime = (signal.planHorizon * signal.timeBase) + signal.time

		t = signal.time
		self.nextPlan = (t - t%(self.planInterval * self.timeBase)) + (self.planInterval * self.timeBase) + self.alignNextPlan

		# Initial planning!
		if not reset:
			result['improvement'] = 1

		else:
			result['improvement'] = self.calculateImprovement(s.desired, ip, result['profile'])

			# # This is still not ideal
			# if not s.allowDiscomfort and not signal.allowDiscomfort and not self.localDiscomfort:
			# 	result['boundsImprovement'] = 0.0
			#
			# if not withinLimits:
			# 	result['improvement'] = -1 # We do not obtain an improvement at all if we violate the limits

		return result


#### PROFILE STEERING ALGORITHM
	# Initial planning to obtain the total power profile == energy consumption production over the horizon
	def doInitialPlanning(self,  signal, parents = []):
		result = {}
		time = signal.time

		#make sure all dicts are there:
		for c in signal.commodities:
			if c not in self.plan:
				self.plan[c] = {}

		self.candidatePlanning[self.name] = self.genZeroes(signal.planHorizon)
		for p in parents:
			self.candidatePlanning[p] = self.genZeroes(signal.planHorizon)

		self.planningWinners = []
		parents.append(self.name)

		s = PSData(signal)
		#firstly, we need to obtain the expected consumption profile somehow
		#NOTE: Realized is only applicable on the initial planning that is triggered. It is realized, hence it is (sort of) inflexible
		results = self.zCall(self.children, 'doInitialPlanning', s, list(parents))
		for k,r in results.items():
			for c in self.commodityIntersection(r['profile'].keys()):
				self.candidatePlanning[self.name][c] = copy.deepcopy(list(np.array(self.candidatePlanning[self.name][c]) + np.array(r['profile'][c])))

		self.planning = copy.deepcopy(self.candidatePlanning[self.name])

		# Bookkeeping
		for p in parents:
			self.candidatePlanning[p] = copy.deepcopy(self.planning)

		for c in self.commodities:
			for i in range(0,  len(self.planning[c])):
				self.plan[c][int(time + i*self.timeBase)] = self.planning[c][i]

		#Set the vars right
		self.planningWinners = []
		t = self.host.time()
		self.nextPlan = (t - t%(self.planInterval * self.timeBase)) + (self.planInterval * self.timeBase) + self.alignNextPlan

		result['boundsImprovement'] = 0.0 #self.calculateBoundImprovement(copy.deepcopy(self.candidatePlanning[self.name]), profileResult, signal.upperLimits, signal.lowerLimits, norm=2)
		result['improvement'] = 0.0
		result['profile'] = dict(self.candidatePlanning[self.name])

		return result


	#Profile steering algorithm
	def iterativePlanning(self,  signal):
		result = {}
		time = signal.time
		timeBase = signal.timeBase

		stopping = False

		# Adjust the desired profile and local profile into the desired profile (signal) and limits
		if self.parent != None and self.parentConnected:
			for c in self.commodities:

				# FIXME: Not yet sure why this works this way only..
				# probably because we need to fix the signal a level higher
				if not self.localDiscomfort: # signal.allowDiscomfort:
					signal.desired[c] = list( np.array(signal.desired[c]) + np.array(list(self.candidatePlanning[self.name][c])))

				# Add limits:
				if c in signal.upperLimits:
					assert(len(signal.upperLimits[c]) == signal.planHorizon )
					signal.upperLimits[c] = list( np.array(signal.upperLimits[c]) + np.array(list(self.candidatePlanning[self.name][c]))	)
				if c in signal.lowerLimits:
					assert(len(signal.lowerLimits[c]) == signal.planHorizon )
					signal.lowerLimits[c] = list( np.array(signal.lowerLimits[c]) + np.array(list(self.candidatePlanning[self.name][c]))	)

		iterationPlanning = copy.deepcopy(self.candidatePlanning[self.name])

		# Participating children list (may get pruned in the process)
		participatingChildren = list(self.children)

		# Determine the initial number of simultaneous commits to consider
		if self.multipleCommits:
			simultaneousCommits = len(self.children)
		else:
			simultaneousCommits = 1

		# simultaneousCommits = len(self.children)

		for i in range(0,  self.maxIters):
			if self.parent == None or self.parentConnected == False:
				self.logMsg("Planning iteration: "+str(i))
				self.resetPlanning([])

			assert(simultaneousCommits > 0)

			s = PSData()
			s.copy(signal)
			s.source = self.name
			s.upperLimits = copy.deepcopy(signal.upperLimits)
			s.lowerLimits = copy.deepcopy(signal.lowerLimits)

			ub = {}
			lb = {}

			for c in self.commodities:
				# Add in the local objective
				s.desired[c] = list(np.array(signal.desired[c])*(1-self.localWeight[c]) + np.array(self.localDesired[c].readValues(s.time, s.time+s.planHorizon*s.timeBase))*(self.localWeight[c]))
				s.desired[c] = list(np.array(s.desired[c]) - np.array(iterationPlanning[c]))

				# Incorporate limits:
				# Determine the own limits first and then see if there are stricter bounds from above:
				if self.congestionPoint is not None:
					if self.congestionPoint.hasUpperLimit(c):
						s.upperLimits[c] = list( np.array( ( [ self.congestionPoint.getUpperLimit(c) ] * s.planHorizon ) ) )
						if c in signal.upperLimits and len(signal.upperLimits[c]) == signal.planHorizon:
							for j in range(0, signal.planHorizon):
								s.upperLimits[c][j] = complex(min(s.upperLimits[c][j].real, signal.upperLimits[c][j].real),
															  min(s.upperLimits[c][j].imag, signal.upperLimits[c][j].imag) )

					if self.congestionPoint.hasLowerLimit(c):
						s.lowerLimits[c] = list( np.array( ( [ self.congestionPoint.getLowerLimit(c) ] * s.planHorizon ) ) )
						if c in signal.lowerLimits and len(signal.lowerLimits[c]) == signal.planHorizon:
							for j in range(0, signal.planHorizon):
								s.lowerLimits[c][j] = complex(max(s.lowerLimits[c][j].real, signal.lowerLimits[c][j].real),
															  max(s.lowerLimits[c][j].imag, signal.lowerLimits[c][j].imag))

				if self.congestionPoint is not None:
					if self.congestionPoint.hasUpperLimit(c):
						ub[c] = copy.deepcopy(s.upperLimits[c])
						lb[c] = copy.deepcopy(s.lowerLimits[c])

				if simultaneousCommits > 0:
					for j in range(0, len(s.desired[c])):
						s.desired[c][j] = (s.desired[c][j] / simultaneousCommits)

					if c in s.upperLimits and len(s.upperLimits[c]) == s.planHorizon:
						for j in range(0, len(s.upperLimits[c])):
							s.upperLimits[c][j] = (s.upperLimits[c][j].real / simultaneousCommits) - (iterationPlanning[c][j] / simultaneousCommits)

					if c in s.lowerLimits and len(s.lowerLimits[c]) == s.planHorizon:
						for j in range(0, len(s.lowerLimits[c])):
							s.lowerLimits[c][j] = (s.lowerLimits[c][j].real / simultaneousCommits) - (iterationPlanning[c][j] / simultaneousCommits)

			# FIXME!!!
			improvements = {}
			boundsImp = {}

			results = self.zCall(participatingChildren, 'doPlanning', s)
			for child, val in results.items():
				improvements[child] = val['improvement']

			# do some sorting
			sortedImprovements = OrderedDict(sorted(improvements.items(), key=lambda k: k[1], reverse=True))

			# select winners
			winners = []
			bestImprovement = 0.0

			for child, improvement in sortedImprovements.items():
				# First select winners
				if len(winners) < simultaneousCommits and winners.count(child) == 0: # or signal.allowDiscomfort:
					if improvement > 0.01:
						winners.append(child)
						# if self.parent == None:
						# 	print("normal", self.name, child.name, improvement, i)

						if self.planningWinners.count(child) == 0:
							self.planningWinners.append(child)

						if improvement > bestImprovement:
							bestImprovement = improvement

						# Perform bookkeeping and updating profiles
						childData = self.zCall(child, 'setIterationWinner', self.name, None)
						for c in self.commodityIntersection(childData['profile'].keys()):
							iterationPlanning[c] = list(np.array(iterationPlanning[c]) + np.array(childData['profile'][c]))

						if self.parent == None or self.parentConnected == False:
							self.zCall(child, 'setPlanningWinner', time,  timeBase, self.name, [])

			improvementThreshold = (self.minImprovement * len(participatingChildren) ) / math.sqrt(float(simultaneousCommits))

			# Stopping condition or update the number of simultaneous commits
			inBounds = True
			if s.allowDiscomfort:
				for c in self.commodities:
					if not self.checkBoundViolations(c, iterationPlanning[c]):
						inBounds = False
						break

			if inBounds and bestImprovement < improvementThreshold:
				if simultaneousCommits <= 1:
					break
				else:
					simultaneousCommits = 1


			simultaneousCommits = max(1, int(simultaneousCommits / self.multipleCommitsDivisor))

		if self.parent != None and self.parentConnected:
			result['improvement'] = self.calculateImprovement(signal.desired,  self.candidatePlanning[self.name],  iterationPlanning)
		else:
			result['improvement'] = 0.0

		if s.allowDiscomfort or self.localDiscomfort:
			result['boundsImprovement'] = self.calculateBoundImprovement(copy.deepcopy(self.candidatePlanning[self.name]), iterationPlanning, ub, lb, norm=2)
		else:
			result['boundsImprovement'] = 0.0

		# Final bookkeeping
		self.candidatePlanning[self.name] = copy.deepcopy(iterationPlanning)

		result['profile'] = dict(self.candidatePlanning[self.name])
		return result



	# Trigger a new planning
	def doReplanning(self):
		if self.parent == None or self.parentConnected == False:  # or self.parentConnected == False:
			self.initiatePlanning(True) #We already acquired the lock
		else:
			self.zCall(self.parent, 'doReplanning')



#### EVENT BASED PROFILE STEERING
	def sendIncentive(self):
		s = PSData()
		s.copyFrom(self)

		self.lockPlanning.acquire()
		intervals = int((self.lastPlannedTime - (self.host.time() - (self.host.time() % self.timeBase))) / self.timeBase )
		startTime = int(self.lastPlannedTime - (self.host.time() % self.timeBase))
		s.planHorizon = intervals

		startIdx = self.planHorizon - intervals

		#build the desired profile
		desiredPlan = {}
		prices = {}

		for c in self.commodities:
			desiredPlan[c] = []
			prices[c] = self.prices[c].retrieveValues(startTime, startTime+intervals*self.timeBase)

			if self.congestionPoint is not None:
				if self.congestionPoint.hasUpperLimit(c):
					s.upperLimits[c] = []
				if self.congestionPoint.hasLowerLimit(c):
					s.lowerLimits[c] = []

			for i in range(0,  intervals):
				try:
					desiredPlan[c].append(complex(0, 0))
					time = (self.host.time() - (self.host.time()%self.timeBase)) + i*self.timeBase
					desiredPlan[c][i] = (self.plan[c][time] - self.realized[c][time])

					try:
						# This part should be fine
						# Add limits:
						if self.congestionPoint is not None:
							if self.congestionPoint.hasUpperLimit(c):
								s.upperLimits[c].append(complex(self.congestionPoint.getUpperLimit(c).real - self.realized[c][time].real,
																self.congestionPoint.getUpperLimit(c).imag - self.realized[c][time].imag))
							if self.congestionPoint.hasLowerLimit(c):
								s.lowerLimits[c].append(complex(self.congestionPoint.getLowerLimit(c).real - self.realized[c][time].real,
																self.congestionPoint.getLowerLimit(c).imag - self.realized[c][time].imag))

							if desiredPlan[c][i].real > s.upperLimits[c][i].real or desiredPlan[c][i].real < s.lowerLimits[c][i].real:
								desiredPlan[c][i] = (s.lowerLimits[c][i].real + s.upperLimits[c][i].real) / 2.0
					except:
						pass
				except:
					# Interval probably doesn't exist (anymore)
					desiredPlan[c][i] = complex(0, 0)

			assert(len(prices[c]) == len(desiredPlan[c]))

		self.lockPlanning.release()
		s.desired = desiredPlan
		s.prices = prices
		s.time = int(self.host.time() - (self.host.time()%self.timeBase) )
		s.originalTimestamp = self.host.time()

		return s


	def doEventCancelation(self, childData):
		#in case a device quits its job early:
		assert(False) # NOTE: UNTESTED!!!
		self.lockPlanning.acquire()
		for c in self.commodities:
			for i in range(0,  childData['realized'][c]):
				time = (self.host.time() - (self.host.time()%self.timeBase)) + i*self.timeBase
				self.realized[c][time] -= childData['realized'][c][i]
		self.lockPlanning.release()


	def requestIncentive(self, timestamp):
		# FIXME: For async PS we need to check whether a planning is being created too!
		# As we cannot have two planning threads run in parallel
		# Therefore we also need to set some flag and trigger for it.

		# Check whether we are the root of this tree and need to send the incentive:
		if (self.parent == None or self.parentConnected == False):
			if self.host.time() >= self.nextPlan and self.lockSyncPlanning.acquire(blocking=False):
				self.doReplanning()
				self.lockSyncPlanning.release()

			return self.sendIncentive()

		# Check if we are a fleet controller and should send the incentive on behalf of the root controller:
		# This is only done if the local problem is still large enough
		#if False:
		elif self.isFleetController:
		# FIXME This case is disabled for now to ensure that the system works in multiple threads
			self.lockPlanning.acquire()
			# Check the difference between realized and agreed planning.
			# If they are too close (small diff) then we should pass the request to a higher level to see if error persist there
			intervals = int((self.lastPlannedTime - (self.host.time() - (self.host.time() % self.timeBase))) / self.timeBase )
			diff = 0
			for c in self.commodities:
				for i in range(0,  intervals):
					time = (self.host.time() - (self.host.time()%self.timeBase)) + i*self.timeBase
					diff += self.weights[c] * abs(self.realized[c][time] - self.plan[c][time])
			self.lockPlanning.release()

			if (diff/intervals) > self.minProblem: # The local problem is large enough, so send our incentive
				return self.sendIncentive()

		# Otherwise, we have not ran into a return statement, so we should ask the higher level controller to return the incentive
		signal = self.zCall(self.parent, 'requestIncentive', timestamp)
		while signal.originalTimestamp < self.planningTimestamp:
			# Perhaps use a delay here?
			signal = self.zCall(self.parent, 'requestIncentive', timestamp)

		self.lockPlanning.acquire()

		s = PSData()
		s.copy(signal)

		if self.congestionPoint is not None:
			for c in signal.commodities:
				# Prepare vectors
				if self.congestionPoint.hasUpperLimit(c):
					s.upperLimits[c] = []
				if self.congestionPoint.hasLowerLimit(c):
					s.lowerLimits[c] = []

				# Fill vectors

				for i in range(0, s.planHorizon):
					time = (self.host.time() - (self.host.time()%self.timeBase)) + i*self.timeBase
					# Check the strictness of bounds and correct them if applicable
					if self.congestionPoint.hasUpperLimit(c):
						s.upperLimits[c].append(self.congestionPoint.getUpperLimit(c))
						try:
							if c in signal.upperLimits:
								s.upperLimits[c][i] = (complex(min(signal.upperLimits[c][i].real, (self.congestionPoint.getUpperLimit(c).real - self.realized[c][time].real) ),
																min(signal.upperLimits[c][i].imag, (self.congestionPoint.getUpperLimit(c).imag - self.realized[c][time].imag) ) ) )
							else:
								s.upperLimits[c][i] = (complex(self.congestionPoint.getUpperLimit(c).real - self.realized[c][time].real,
																self.congestionPoint.getUpperLimit(c).imag - self.realized[c][time].imag))
						except:
							pass

					if self.congestionPoint.hasLowerLimit(c):
						s.lowerLimits[c].append(self.congestionPoint.getLowerLimit(c))
						try:
							if c in signal.lowerLimits:
								s.lowerLimits[c][i] = (complex(max(signal.lowerLimits[c][i].real, (self.congestionPoint.getLowerLimit(c).real - self.realized[c][time].real) ),
																	max(signal.lowerLimits[c][i].imag, (self.congestionPoint.getLowerLimit(c).imag - self.realized[c][time].imag) ) ) )
							else:
								s.lowerLimits[c][i] = (complex(self.congestionPoint.getLowerLimit(c).real - self.realized[c][time].real,
																	self.congestionPoint.getLowerLimit(c).imag - self.realized[c][time].imag))
						except:
							pass

					if s.desired[c][i].real > s.upperLimits[c][i].real:
						s.desired[c][i] = s.upperLimits[c][i]
					elif s.desired[c][i].real < s.lowerLimits[c][i].real:
						s.desired[c][i] = s.lowerLimits[c][i]

		self.lockPlanning.release()

		return s


	def requestCancelation(self, childData):
		assert(False) #UNTESTED
		if self.parent == None or self.parentConnected == False:
			self.doEventCancelation(childData)
		else:
			self.zCall(self.parent, 'requestCancelation', childData)
					
	#Push an update of a prediction that is considered to be a realized profile (e.g.static loads adjusted based on current measurements)	
	def updateRealized(self, profile):
		self.lockPlanning.acquire()

		for c in self.commodityIntersection(profile.keys()):
			for i in range(0, len(profile[c])):
				time = (self.host.time() - (self.host.time()%self.timeBase)) + i*self.timeBase
				try:
					if i == 0:
						# Weight for time elapsed:
						w = (self.timeBase - (self.host.time()%self.timeBase)) / self.timeBase
						profile[c][i] *= w

					self.realized[c][time] += profile[c][i]
					
					if self.forwardLogging:
						self.logValue("W-power.realized.real.c."+c,  self.realized[c][time].real, time)
						self.logValue("W-power.realized.imag.c." + c, self.realized[c][time].imag, time)
				except:
					pass

		self.lockPlanning.release()

		if self.parent != None and self.parentConnected == True:
			self.zCall(self.parent, 'updateRealized', profile)

	# Check whether a profile does meet the bounds set by a congestionpoint
	def checkBoundViolations(self, commodity, profile):
		if self.congestionPoint is not None:
			if self.congestionPoint.hasUpperLimit(commodity):
				for cons in profile:
					if cons.real - 0.00001 > self.congestionPoint.getUpperLimit(commodity).real:
						return False

			if self.congestionPoint.hasLowerLimit(commodity):
				for cons in profile:
					if cons.real + 0.00001 < self.congestionPoint.getLowerLimit(commodity).real:
						return False

		return True