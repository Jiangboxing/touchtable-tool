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


from ctrl.optCtrl import OptCtrl
from data.psData import PSData
from util.funcReader import FuncReader

import copy
import numpy as np

# Device controller base
class DevCtrl(OptCtrl):
	#Make some init function that requires the host to be provided
	def __init__(self, name, dev, parent, host):
		OptCtrl.__init__(self,  name,  host)

		self.dev = dev
		if parent != None:
			self.parent = parent

		# This boolean can be used in the future to check whether the connection to the parent is still active
		if parent != None:
			self.parentConnected = True
		else:
			self.parentConnected = False

		self.perfectPredictions = False

		#Variables storing local device data
		self.devData = None
		self.devDataUpdate = -1
		self.devDataPlanning = None

		self.staticDevice = True # True if the device is always available

		self.localWeight = { 'ELECTRICITY':0, 'EL1': 0, 'EL2': 0, 'EL3': 0, 'HEAT': 0, 'NATGAS': 0 }
		self.localDesired = None

	def startup(self):
		# Establish device <-> controller connection
		if not isinstance(self.dev, str):
			self.dev.controller = self
		else:
			self.zSet(self.dev, 'controller', self.name)

		# Establish controller <-> parent connection
		if self.parent is not None:
			if not isinstance(self.parent, str):
				self.parent.appendChild(self)
			else:
				self.zCall(self.parent, 'appendChild', self.name)

		# persistence
		if self.persistence != None:
			watchlist = self.watchlist + ["devData", "devDataUpdate", "devDataPlanning"]
			self.persistence.setWatchlist(watchlist)


		if self.localDesired is None:
			self.localDesired = {}
			for c in self.commodities:
				self.localDesired[c] = FuncReader(timeOffset = self.host.timeOffset, timeBase = self.timeBase)
				# self.localDesired[c].functionType = "sin"
				# self.localDesired[c].period = 12*3600
				# self.localDesired[c].amplitude = 5000
				# self.localDesired[c].dutyCycle = 0.5
				# self.localDesired[c].offset = 0

		OptCtrl.startup(self)

	def logStats(self, time):
		t = time - time%self.timeBase
		self.lockPlanning.acquire()
		try:
			for c in self.commodities:
				self.logValue("W-power.plan.real.c." + c, self.plan[c][t].real)
				self.logValue("W-power.plan.imag.c." + c, self.plan[c][t].imag)
				if self.useEventControl:
					self.logValue("W-power.realized.real.c." + c, self.realized[c][t].real)
					self.logValue("W-power.realized.imag.c." + c, self.realized[c][t].imag)
		except:
			pass

		self.lockPlanning.release()


#### PROFILE STEERING ALGORITHM
	#Planning announcements
	def startSynchronizedPlanning(self, signal):
		self.devDataPlanning = copy.deepcopy( self.updateDeviceProperties() )

		OptCtrl.startSynchronizedPlanning(self, signal)

	def endSynchronizedPlanning(self, signal):
		self.lockPlanning.acquire()
		if self.useEventControl:
			# Get the update device state
			self.devDataPlanning = copy.deepcopy( self.updateDeviceProperties() )

			d = {}
			for c in self.commodities:
				d[c] = [complex(0.0, 0.0)] * signal.planHorizon

			signal.desired = d

			self.lockPlanning.release()
			r = self.doPlanning(signal, False)

			self.lockPlanning.acquire()

			for c in self.commodities:
				self.realized[c] = {}
				for i in range(0,  len(r['profile'][c])):
					t = int(signal.time - (signal.time%self.timeBase) + i*self.timeBase)
					self.realized[c][t] = r['profile'][c][i]

			self.planningTimestamp = self.host.time()

			if self.staticDevice:
				self.setPlan(r['profile'], signal.time, signal.timeBase)

		# perform forward logging if desired to expose the planning to a user :)
		if self.forwardLogging and self.host.logControllers:

			for c in signal.commodities:
				for i in range(0,  signal.planHorizon):
					self.logValue("W-power.plan.real.c."+c,  self.plan[c][int(signal.time + i*signal.timeBase)].real, int(signal.time + i*signal.timeBase))
					self.logValue("W-power.plan.imag.c." + c, self.plan[c][int(signal.time + i*signal.timeBase)].imag, int(signal.time + i * signal.timeBase))

					if self.useEventControl:
						self.logValue("W-power.realized.imag.c." + c,self.realized[c][int(signal.time + i * signal.timeBase)].imag,int(signal.time + i * signal.timeBase))
						self.logValue("W-power.realized.real.c." + c,self.realized[c][int(signal.time + i * signal.timeBase)].real,int(signal.time + i * signal.timeBase))

		self.lockPlanning.release()

		return dict(self.realized)

	#planning functions
	def doInitialPlanning(self,  signal, parents = []):
		time = signal.time
		timeBase = signal.timeBase

		self.candidatePlanning[self.name] = self.genZeroes(signal.planHorizon)

		result = copy.deepcopy(self.doPlanning(signal,  False))
		self.candidatePlanning[self.name] = copy.deepcopy(result['profile'])
				
		self.setPlanningWinner(time, timeBase, self.name, parents)

		return result
			
	def doPlanning(self,  signal,  requireImprovement = True):
		print("this function must be overridden")	
		assert(False)





#### EVENT BASED PROFILE STEERING
	def requestIncentive(self):
		if self.useEventControl:

			time = self.host.time()
			s = self.zCall(self.parent, 'requestIncentive', time)

			while s.originalTimestamp < self.planningTimestamp:
				time = self.host.time()
				s = self.zCall(self.parent, 'requestIncentive', time)

			self.doEventPlanning(s)
		
	def requestCancelation(self):
		print("this function must be overridden")	
		assert(False)
		
	def doEventPlanning(self, signal):
		print("this function must be overridden")	
		assert(False)

	def executeValleyFillingJob(self):
		self.parent.executeValleyFillingJob()
		
	def triggerEvent(self, event):
		#all types of events:
		if event == "stateUpdate":
			self.requestIncentive()
		elif event == "predictionUpdate":
			self.updatePrediction()
		elif event == "cancelation":
			self.requestCancelation()
		elif event == "vfJobTrigger":
			self.executeValleyFillingJob()
		else:
			#default option
			self.requestIncentive()


	def doPrediction(self,  startTime,  endTime):
		print("this function must be overridden")	
		assert(False)
		
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
		self.zCall(self.dev, 'setPlan', result)

	def updateDeviceProperties(self):
		if self.devDataUpdate < self.host.time():
			self.devData = self.zCall(self.dev, 'getProperties')

		return self.devData



#### HELPER FUNCTIONS
	# Prepare an incoming signal based on local data
	def preparePlanningData(self, signal, realized = None):
		s = PSData()
		s.copy(signal)

		# Fill the realized dict if required
		if realized is None:
			realized = {}
			for c in self.commodities:
				realized[c] = [complex(0.0, 0.0)] * len(signal.desired[c])

		for c in self.commodityIntersection(signal.commodities):
			if len(realized[c]) < len(signal.desired[c]):
				for i in range(0, (len(signal.desired[c]) - len(realized[c]))):
					realized[c].append(complex(0.0, 0.0))

		# Add the current profile
		for c in self.commodityIntersection(signal.commodities):
			s.desired[c] = list(np.array(signal.desired[c])*(1-self.localWeight[c]) + np.array(self.localDesired[c].readValues(s.time, s.time+s.planHorizon*s.timeBase))*(self.localWeight[c]))
			s.desired[c] = list(np.array(signal.desired[c]) + np.array(list(realized[c][(len(realized[c])-len(s.desired[c])):])))

			# backup: (to be removed)
			# s.desired[c] = list(np.array(signal.desired[c]) + np.array(list(realized[c][(len(realized[c])-len(signal.desired[c])):])))

		# Add the profile steering limits
		for c in self.commodityIntersection(signal.commodities):
			if c in signal.upperLimits:
				s.upperLimits[c] = list( np.array(signal.upperLimits[c]) + np.array(list(realized[c][(len(realized[c])-len(signal.desired[c])):])))
			if c in signal.lowerLimits:
				s.lowerLimits[c] = list( np.array(signal.lowerLimits[c]) + np.array(list(realized[c][(len(realized[c])-len(signal.desired[c])):])))

		# Check prices:
		for c in self.commodityIntersection(signal.commodities):
			if len(s.prices[c]) < len(s.desired[c]):
				s.prices[c] = [0] * len(s.desired[c])

		# Return the transformed steering signal
		return s


##### GENERAL HELPER FUNCTIONS
	# Weave a dict multiple commodities into one vector of a single commodity
	def weaveDict(self, d, commodities):
		result = []

		try:
			for i in range(0, len(d[commodities[0]])):
				for c in commodities:
					result.append(d[c][i])
		except:
			return []

		return result

	def weaveMultiply(self, v, commodities):
		result = []

		try:
			for i in range(0, len(v)):
				for c in commodities:
					result.append(v[i] / float(len(commodities)))
		except:
			return []

		return result

	def unweaveVec(self, v, commodities):
		result = {}
		for c in commodities:
			result[c] = []

		for i in range(0, len(v)):
			c = commodities[i%(len(commodities))]
			result[c].append(v[i])

		return result
