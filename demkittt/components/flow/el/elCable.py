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

from flow.edge import Edge

class ElCable(Edge):
	def __init__(self,  name,  flowSim, nodeFrom, nodeTo, host):
		Edge.__init__(self,  name, flowSim, nodeFrom, nodeTo, host)

		self.devtype = "ElectricityCable"
		self.hasNeutral = True

		#bookkeeping
		self.current = [complex(0.0, 0.0)] *4
		self.flowDirection = [1] * 4
		#order: C-N-O-N (C=Conductor (diagonal of matrix), N=Next conductor, O=Opposite conductor):
		self.impedance = [complex(0.0, 0.0)] *4
		#   _-=-_
		#  / (C) \
		# ((N) (N)) <-- this is a LV cable with 4 conductors. Use your imagination ;-)
		#  \ (O) /
		#   ^-=-^

		# Same definitions can be used for three phase MV cables because In=0.
		# Reference: "Netten voor distributie van electriciteit" by Phase to Phase, 2012, section 8.2.8
		# https://phasetophase.nl/boek/index.html

		# Precalculated values for speedup (see startup())
		self.scaledImpedance = []

		self.length = None    	#in meters
		self.ampacity = None	#amperes
		self.fuse = 0       	#additional limit

		self.enabled = True #Option to disable the cable.
		self.burned = False
		self.powered = [True, True, True, True] #Option to indicate the cable is powered, in case of a fault towards the transformer

	def voltageDrop(self, phase):
		assert(not ((not self.hasNeutral) and (phase == 0))) # neutral conductor not available
		result = complex(0.0, 0.0)
			
		# Use symmetric idea, should also work for three phase MV.
		for i in range(0, 4):
			result += self.current[((i+phase)%4)] * self.scaledImpedance[i]

		return result

	def getLossesPhase(self, phase):
		# Use phase = 0 for neutral conductor
		assert(not ((not self.hasNeutral) and (phase == 0)))  # neutral conductor not available

		return abs((self.voltageDrop(phase) * self.current[phase].conjugate()).real)

	def getLosses(self):
		result = 0.0

		for conductor in self.conductors():
			result += self.getLossesPhase(conductor)

		return result

	def determinePhysicalState(self):
		result = False
		for phase in self.conductors():
			if abs(self.current[phase]) > self.ampacity and self.powered[phase]:
				result = True
				self.burned = True
				self.powered[phase] = False
				if not self.powered[phase]:
					self.logWarning("Phase "+str(phase)+" burned!")
				if phase == 0 and not self.powered[phase]:
					self.powered = [False, False, False, False]
		return result

	def updatePhysicalState(self, prevNode, nextNode):
		for phase in self.conductors():
			if abs(nextNode.voltage[phase]) - abs(prevNode.voltage[phase]) < 0:
				self.flowDirection[phase] = 1
			else:
				self.flowDirection[phase] = -1

		# Check if we are powered
		for phase in self.conductors():
			# if self.powered[phase]:
			if not self.burned:
				self.powered[phase] = prevNode.powered[phase]
				if not self.powered[phase]:
					self.logWarning("Phase "+str(phase)+" not powered!")
			if phase == 0 and not self.powered[phase]:
				self.powered = [False, False, False, False]
				break



	def conductors(self):
		# Convention used here is that the first index is always the neutral conductor,
		# also for nodes without a neutral conductor.
		startIndex = 1
		if self.hasNeutral:
			startIndex = 0

		return range(startIndex, len(self.current))

	def getCableLoad(self):
		assert(self.ampacity > 0)
		load = 0.0
		for conductor in self.conductors():
			if abs(self.current[conductor]) > load:
				load = abs(self.current[conductor])
		return 100*(load / self.ampacity)

	def estimateReliability(self):
		pass

	def checkViolations(self):
		violations = 0
		limit = self.ampacity
		if 0 < self.fuse < self.ampacity:
			limit = self.fuse

		for conductor in self.conductors():
			if abs(self.current[conductor]) > limit:
				violations += 1

		if violations > 0:
			self.logWarning("capacity of "+str(violations)+" conductor(s) violated")
		self.logValue("n-violations.capacity", violations)

	def startup(self):
		# Prepare scaled impedance:
		for i in range(0, 4):
			imp = self.impedance[i] * (self.length/1000.0)
			self.scaledImpedance.append(imp)

	def timeTick(self,  time):
		pass

	def shutdown(self):
		pass

	def reset(self, restoreGrid = True):
		self.current = [complex(0.0, 0.0)] * 4

		if restoreGrid:
			self.powered = [True, True, True, True]
			self.burned = False

	def logStats(self, time):
		self.logValue("A-current.c.L1", abs(self.current[1]) * self.flowDirection[1])
		self.logValue("A-current.c.L2", abs(self.current[2]) * self.flowDirection[2])
		self.logValue("A-current.c.L3", abs(self.current[3]) * self.flowDirection[3])

		if self.hasNeutral:
			self.logValue("A-current.c.N", abs(self.current[0])  * self.flowDirection[0])

		self.logValue("p-load", self.getCableLoad())
		self.logValue("W-power.losses", self.getLosses())
		self.checkViolations()

