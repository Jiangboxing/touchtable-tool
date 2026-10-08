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
import random

from ctrl.groupCtrl import GroupCtrl
from data.psData import PSData

class CostGroupCtrl(GroupCtrl):
	def __init__(self,  name,  host, parent = None, congestionPoint = None):
		GroupCtrl.__init__(self,  name,  host, parent, congestionPoint)

		#costs
		self.costSharing = True

	def doPlanning(self, signal):
		self.resetIteration(signal.source, [])
		s = PSData()
		s.copy(signal)

		if (self.parent != None):
			for c in self.commodities:
				s.desired[c] = list( np.array(signal.desired[c]) + np.array(list(self.candidatePlanning[self.name][c]))	)

				# Add limits:
				if c in signal.upperLimits:
					s.upperLimits[c] = list( np.array(signal.upperLimits[c]) + np.array(list(self.candidatePlanning[self.name][c]))	)
				if c in signal.lowerLimits:
					s.lowerLimits[c] = list( np.array(signal.lowerLimits[c]) + np.array(list(self.candidatePlanning[self.name][c]))	)

		return self.costSharingPlanning(s)


#### COST SHARING ALGORITHM
	def costSharingPlanning(self, signal):
		assert(self.useEventControl == False) # FIXME: [GERWIN] Unsupported for now as it needs to set the iterationConfimed too! May break with the whole idea. See T184
		assert(len(self.commodities) == 1) # FIXME: [GERWIN] I did add support for commodities, but I am not sure if this will work as expected. See T184

		time = signal.time
		timeBase = signal.timeBase

		# Start with an empty planning, plan loads on top
		iterationPlanning = {}
		for c in self.commodities:
			emptyplan = np.array([0] * self.planHorizon)
			iterationPlanning[c] = emptyplan

		self.childrenSub = {}
		for i in range(0, self.maxIters):
			print('Iteration CSC: ' + str(i))
			random.shuffle(self.children)
			for child in self.children:
				# The child profile is subtracted from the total profile, unless it is the initial planning, which is ignored.
				# It would be better/faster not to make an initial planning.

				# Need an additional loop to populate childrensub for commodities
				if not child.name in self.childrenSub:
					self.childrenSub[child.name] = {}

				for c in self.commodities:
					csub = self.childrenSub[child.name].get(c, emptyplan)
					iterationPlanning[c] = np.array(iterationPlanning[c]) - np.array(csub)

				# Create a data object for profile steering
				s = PSData()
				s.copy(signal)
				s.source = self.name

				# The desired profile is -0.5 times the total load.  Note, in profile steering this is -1.
				for c in self.commodities:
					s.desired[c] = -0.5 * np.array(iterationPlanning[c]);

				profileChild = child.doPlanning(s)
				self.childrenSub[child.name] = profileChild['profile'];

				# The next few lines are book keeping only needed in the profile steering implementation.
				# In this algorithm every plan is immediately final.
				if self.planningWinners.count(child) == 0:
					self.planningWinners.append(child)

				child.setIterationWinner(self.name, None)

				if (self.parent == None):
					child.setPlanningWinner(time, timeBase, self.name)

				for c in self.commodities:
					iterationPlanning[c] = list(np.array(iterationPlanning[c]) + np.array(profileChild['profile'][c]))

		# Algorithm above, bookkeeping below... :-)
		for child in self.children:
			for c in self.commodities:
				self.candidatePlanning[self.name][c] = list(np.array(iterationPlanning[c]) + np.array(child.getPlan(time, c)))

		#Bookkeeping
		self.candidatePlanning[self.name] = dict(iterationPlanning)
		self.candidateConfirmed[self.name] = dict(iterationPlanning)

		if (self.parent == None):
			self.planning = dict(iterationPlanning)
			self.confirmed = dict(iterationPlanning)

			for c in self.commodities:
				for i in range(0, len(self.planning[c])):
					self.plan[c][int(time + i * self.timeBase)] = self.planning[c][i]
					self.realized[c][int(time + i * self.timeBase)] = self.confirmed[c][i]

					if self.forwardLogging and self.host.logControllers:
						self.logValue("W-power.plan.real.c." + c, self.plan[c][int(time + i * self.timeBase)].real,int(time + i * timeBase))
						self.logValue("W-power.realized.real.c." + c,self.realized[c][int(time + i * self.timeBase)].real, int(time + i * timeBase))
						self.logValue("W-power.plan.imag.c." + c, self.plan[c][int(time + i * self.timeBase)].imag,int(time + i * timeBase))
						self.logValue("W-power.realized.imag.c." + c,self.realized[c][int(time + i * self.timeBase)].imag, int(time + i * timeBase))

		result = {}
		result['improvement'] = 0xDEADBEEF;  # Has no meaning for this algorithm
		result['profile'] = dict(iterationPlanning)
		result['realized'] = dict(iterationPlanning)  # XXX

		return result

