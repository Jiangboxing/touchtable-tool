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
from ctrl.groupCtrl import GroupCtrl
from data.psData import PSData

import copy

# ADMM Group controller
# Reading material for reference:
# Distributed Convex Optimization for Electric Vehicle Aggregators
# Rivera, Goebel, Jacobsen
# IEEE: https://ieeexplore.ieee.org/document/7372473

# Special thanks to Victor Reijnders for the first version of this implementation

# The ADMM algorithm, with gamma = 0 creates a system that is similar to profile steering on the local level
# Therefore, with this implementation, we share the device controllers as implemented with Profile Steering
# Furthermore, the current implementation inherits on the Profile Steering code
# As a result, ADMM and event-driven Profile Steering may be combined as well, similarly auctions may be used (when implemented) easily too

# FIXME
# Work in progress, we first extend
# Multiple levels of control not yet supported (pass-through nodes)
# Local limits should work, but intermediate stricter limits are not an option yet
# Cleanup needs to be considered later on
# In comparison to the implementation by Victor, we perform incentive transformations at the group controller (similar to Profile Steering)
# This leads to less operatiosn (less computation power) and allows us to use the same PS device controllers :)
# In the future, we may alter the PSData container for a generic data container using some smart inheritance. The way it was originally intended anyways.
# Also, it only works for a single commodity currently. I expect it will work for multiple commodities as well, similarly to PS!

# Note that some parts are commented as they are not necessary for ADMM right now (e.g. unused/tested features).
# However, they might be included in the future

# FIXME do a proper inheritance
# ADMM additions / altered functions indicated with comment: ADMM++ / ADMM--

# ADMM++
class AdmmGroupCtrl(GroupCtrl):
	def __init__(self,  name,  host, parent = None, congestionPoint = None, dev=None):
		GroupCtrl.__init__(self,  name,  host, parent, congestionPoint, dev)
		self.devtype = "GroupController"

		# ADMM++
		self.rho = 0.5
		self.mu = 10 # used for the penalty parameter rho
		self.tauIncr = 2 # used for the penalty parameter rho
		self.tauDecr = 2 # used for the penalty parameter rho
		self.epsPrimal = 100 # stopping criterium for the primal residual
		self.epsDual = 100 # stopping criterium for the dual residual
		self.delta = 1 # scaling parameter for aggregator's objective

		# self.rho = 0.5
		# self.mu = 10 # used for the penalty parameter rho
		# self.tauIncr = 2 # used for the penalty parameter rho
		# self.tauDecr = 2 # used for the penalty parameter rho
		# self.epsPrimal = 100 # stopping criterium for the primal residual
		# self.epsDual = 100 # stopping criterium for the dual residual
		# self.delta = 1 # scaling parameter for aggregator's objective

		# ADMM--
		# Use these functions with care! MultipleCommits usually leads to better results
		self.multipleCommits = False			# Allow multiple commits to speedup the optimization
		self.multipleCommitsDivisor = 1			# Divisor to reduce the number of selected commits for each iteration

		# Use with care. Pruning is usually only really useful on HEMS level, or when a lot of houses have little to no flexibility
		self.pruneInflexibleChildren = False		# Remove children with no to little improvement for following iterations
		self.initialPlan = False # FIXME UNDECIDED YET


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

		# ADMM ++
		s.averageProfile = self.genZeroes(s.planHorizon)
		s.scaledLagrangian = self.genZeroes(s.planHorizon)

		#debug
		# print(s.averageProfile)
		# print(s.scaledLagrangian)

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

	# ADMM++
	def doPlanning(self, signal):
		# Prepare the data and limits
		self.resetIteration(signal.source, [])
		s = PSData()
		s.copy(signal)

		# debug
		# print("Altered signal?")
		# print(s.averageProfile)
		# print(s.scaledLagrangian)

		# Now test whether the current (in most cases the initial one) falls within the limits:
		withinLimits = True

		# Note, only local limits need to be checked!
		# FIXME congestionpoints should have the option to provide a vector of bounds instead. T211

		# FIXME Congestion points disabled for ADMM at the moment
		# It requires some tought on how to handle the updates on the average profile and scaled lagrangian

		# if self.congestionPoint is not None and s.allowDiscomfort == False: # No need to go through this process if the higher level already has a problem
		# 	for c in self.commodities:
		# 		if not self.checkBoundViolations(c, self.candidatePlanning[self.name][c]):
		# 			withinLimits = False
		# 			# Change the objective for this commodity now to steer the group towards a feasible solution:
		# 			for i in range(0, len(s.desired[c])):
		# 				s.desired[c][i] = max(self.congestionPoint.getLowerLimit(c).real, min(s.desired[c][i].real, self.congestionPoint.getUpperLimit(c).real))
		#
		# 	if not withinLimits:
		# 		# We have detected violations
		# 		# Initial planning to resolve the problem with the new signal
		# 		result = self.iterativePlanning(s)
		#
		# 		# Now check whether we are in bounds again:
		# 		withinLimits = True
		# 		for c in self.commodities:
		# 			if not self.checkBoundViolations(c, self.candidatePlanning[self.name][c]):
		# 				withinLimits = False
		#
		# if not withinLimits and self.strictComfort == False:
		# 	self.logWarning("Congestionpoint bounds violated, executing load shedding and/or production curtailment")
		# 	# We are still violating the limits, so there is no feasible solution with maintaining comfort
		# 	# So we can perform load shedding
		# 	# This is the part where the PhD thesis of Thijs and Gerwin break and normally would return the best (infeasible) solution
		# 	# However, if we allow discomfort, we can now attempt an iteration with load shedding / curtailment.
		# 	s.allowDiscomfort = True
		# 	result = self.iterativePlanning(s)

		if True: #elif withinLimits:
			# We are in the bounds, so we can perform a normal planning as indicated in the thesis
			# s = PSData()		# When considering limits, these still need to be commented probably
			# s.copy(signal)	# Since the average profile and scaled lagrangian are likely to be altered through object references
			# Not sure why these need to be recopied in PS anyways
			result = self.iterativePlanning(s)

		# Bookkeeping of the planning
		self.lastPlannedTime = (signal.planHorizon * signal.timeBase) + signal.time

		t = signal.time
		self.nextPlan = (t - t%(self.planInterval * self.timeBase)) + (self.planInterval * self.timeBase) + self.alignNextPlan

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

		#Bookkeeping
		self.planning = copy.deepcopy(self.candidatePlanning[self.name])

		for p in parents:
			self.candidatePlanning[p] = copy.deepcopy(self.planning)

		for c in self.commodities:
			for i in range(0,  len(self.planning[c])):
				self.plan[c][int(time + i*self.timeBase)] = self.planning[c][i]

		#Set the vars right
		self.planningWinners = []
		t = self.host.time()
		self.nextPlan = (t - t%(self.planInterval * self.timeBase)) + (self.planInterval * self.timeBase) + self.alignNextPlan

		result['improvement'] = 0.0
		result['profile'] = dict(self.candidatePlanning[self.name])

		return result


	#Profile steering algorithm
	# ADMM++
	# Note that currently unsupported/untested features of ADMM have been commented to re-enable them in the future easily
	def iterativePlanning(self,  signal):
		result = {}
		time = signal.time
		timeBase = signal.timeBase

		# Adjust the desired profile and local profile into the desired profile (signal) and limits
		if self.parent is not None and self.parentConnected:
			for c in self.commodities:
				signal.desired[c] = list( np.array(signal.desired[c]) + np.array(list(self.candidatePlanning[self.name][c])))

				# Add limits:
				# if c in signal.upperLimits:
				# 	assert(len(signal.upperLimits[c]) == signal.planHorizon )
				# 	signal.upperLimits[c] = list( np.array(signal.upperLimits[c]) + np.array(list(self.candidatePlanning[self.name][c]))	)
				# if c in signal.lowerLimits:
				# 	assert(len(signal.lowerLimits[c]) == signal.planHorizon )
				# 	signal.lowerLimits[c] = list( np.array(signal.lowerLimits[c]) + np.array(list(self.candidatePlanning[self.name][c]))	)

		iterationPlanning = copy.deepcopy(self.candidatePlanning[self.name])

		# Participating children list (may get pruned in the process)
		participatingChildren = list(self.children)

		# ADMM algorithm initialization
		residual = 2*self.epsPrimal
		dualResidual = 2*self.epsDual

		# Bookkeeping from previous iteration
		previousRho = self.rho
		rho = self.rho

		# We need to track all profiles of the children at this level (can this be hidden? privacy?)
		previousAverageProfile = signal.averageProfile.copy()
		previousScaledLagrangian = signal.scaledLagrangian.copy()
		previousGroupPlanning = self.genZeroes(signal.planHorizon)

		previousChildPlanning={}
		for i in participatingChildren:
			previousChildPlanning[i] = self.genZeroes(signal.planHorizon)

		# In contrast to Profile Steering, all children are involved in every iteration, so this is rather static:
		winners = []
		for child in participatingChildren:
			winners.append(child)
			self.planningWinners.append(child)

		# FIXME:
		# Gerwin does not like this to have a separate prediction (treat all devices/nodes equal)
		# Let's see if we can do without
		# Might also open the option to remove delta param

		s = PSData()
		s.copy(signal)
		s.source = self.name
		s.upperLimits = copy.deepcopy(signal.upperLimits)
		s.lowerLimits = copy.deepcopy(signal.lowerLimits)
		s.rho = rho

		iter = 0
		while iter < self.maxIters and (residual > self.epsPrimal or dualResidual > self.epsDual) and participatingChildren:
		# for i in range(0,  self.maxIters):
			if self.parent == None or self.parentConnected == False:
				self.logMsg("Planning iteration: "+str(iter))
				self.resetPlanning([])

			# ADMM++
			# Sending incentive to the children

			# We cannot support multiple commodities yet:
			assert(len(self.commodities) == 1)

			for c in self.commodities:
				# Preparing the steering signal:
				s.desired[c] = list(np.subtract(np.array([0]*len(s.averageProfile[c])),np.add(np.array(s.averageProfile[c]),np.array(s.scaledLagrangian[c]))))

			# 	# Incorporate limits:
			# 	# Determine the own limits first and then see if there are stricter bounds from above:
			# 	if self.congestionPoint is not None:
			# 		if self.congestionPoint.hasUpperLimit(c):
			# 			s.upperLimits[c] = list( np.array( ( [ self.congestionPoint.getUpperLimit(c) ] * s.planHorizon ) ) )
			# 			if c in signal.upperLimits and len(signal.upperLimits[c]) == signal.planHorizon:
			# 				for j in range(0, signal.planHorizon):
			# 					s.upperLimits[c][j] = complex(min(s.upperLimits[c][j].real, signal.upperLimits[c][j].real),
			# 												  min(s.upperLimits[c][j].imag, signal.upperLimits[c][j].imag) )
			#
			# 		if self.congestionPoint.hasLowerLimit(c):
			# 			s.lowerLimits[c] = list( np.array( ( [ self.congestionPoint.getLowerLimit(c) ] * s.planHorizon ) ) )
			# 			if c in signal.lowerLimits and len(signal.lowerLimits[c]) == signal.planHorizon:
			# 				for j in range(0, signal.planHorizon):
			# 					s.lowerLimits[c][j] = complex(max(s.lowerLimits[c][j].real, signal.lowerLimits[c][j].real),
			# 												  max(s.lowerLimits[c][j].imag, signal.lowerLimits[c][j].imag))
			#
			# 	for j in range(0, len(s.desired[c])):
			# 		s.desired[c][j] = (s.desired[c][j] / simultaneousCommits)
			#
			# 	if c in s.upperLimits and len(s.upperLimits[c]) == s.planHorizon:
			# 		for j in range(0, len(s.upperLimits[c])):
			# 			s.upperLimits[c][j] = (s.upperLimits[c][j].real / simultaneousCommits) - (iterationPlanning[c][j] / simultaneousCommits)
			#
			# 	if c in s.lowerLimits and len(s.lowerLimits[c]) == s.planHorizon:
			# 		for j in range(0, len(s.lowerLimits[c])):
			# 			s.lowerLimits[c][j] = (s.lowerLimits[c][j].real / simultaneousCommits) - (iterationPlanning[c][j] / simultaneousCommits)

			childPlanning = {}
			iterationPlanning = {}
			for c in self.commodities:
				iterationPlanning[c] = [0] * s.planHorizon

			results = self.zCall(participatingChildren, 'doPlanning', s)
			for child, val in results.items():
				childPlanning[child] = {}
				for c in self.commodities:
					childPlanning[child][c] = val['profile'][c]
					iterationPlanning[c] = list(np.array(iterationPlanning[c]) + np.array(val['profile'][c]))

			# Bookkeeping on aggregator level
			groupPlanning = {}
			for c in self.commodities:
				# groupPlanning[c] = rho/(rho+2*self.delta)*np.subtract(np.array(previousGroupPlanning[c]),np.add(np.array(s.averageProfile[c]),np.array(s.scaledLagrangian[c])))
				groupPlanning[c] = (rho/2)*np.subtract(np.array(previousGroupPlanning[c]),np.add(np.array(s.averageProfile[c]),np.array(s.scaledLagrangian[c])))
				s.averageProfile[c] = list(np.mean(np.insert(np.array([childPlanning[i][c] for i in childPlanning.keys()]),0, groupPlanning[c], axis=0), axis=0))  # \bar{x}^{k+1}
				s.scaledLagrangian[c] = list(np.add(np.array(s.averageProfile[c]),np.array(previousScaledLagrangian[c])))  #u^{k+1}

				# Not sure how residuals should work for multiple commodities tho
				residual = np.linalg.norm(s.averageProfile[c], ord=2) # ||r^k||_2
				dualFeasibility = []
				for i in participatingChildren:
					tempDualFeasibility = list(np.add( np.subtract(np.array(childPlanning[i][c]), np.array(previousChildPlanning[i][c])), np.subtract(np.array(previousAverageProfile[c]), np.array(s.averageProfile[c])))) #s_i^k
					dualFeasibility += [-rho*(len(participatingChildren)+1)*j for j in tempDualFeasibility]
				dualResidual = np.linalg.norm(dualFeasibility, ord=2) # ||s^k||_2

			# Updating Rho
			if residual > self.mu * dualResidual:
				rho = self.tauIncr * previousRho
				# print("inc")
			elif dualResidual > self.mu * residual:
				rho = previousRho / self.tauDecr
				# print("dec")
			else:
				rho = previousRho
				# print("equ")

			self.planningWinners = list(winners)
			self.zCall(participatingChildren, 'setIterationWinner', self.name, None)
			self.zCall(participatingChildren, 'setPlanningWinner', time,  timeBase, self.name, [])

			# Further bookkeeping
			previousRho = rho
			previousChildPlanning = childPlanning.copy()
			previousAverageProfile = copy.deepcopy(s.averageProfile)
			previousScaledLagrangian = copy.deepcopy(s.scaledLagrangian)
			previousGroupPlanning = copy.deepcopy(groupPlanning)

			iter += 1

		# Final bookkeeping, similar to Profile Steering. Should also set the internal bookkeeping as to be fully compatible with all other additions
		self.candidatePlanning[self.name] = copy.deepcopy(iterationPlanning)
		result['profile'] = dict(self.candidatePlanning[self.name])
		return result
