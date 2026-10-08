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


from dev.device import Device
from data.evTypes import evTypes

import math

class BtsDev(Device):	
	def __init__(self,  name,  host):
		Device.__init__(self,  name,  host)
		self.devtype = "BufferTimeshiftable"
		
		#params
		self.capacity = 12000
		self.chargingPowers = [0.0, 1380.0, 1610.0, 1840.0, 2070.0, 2300.0, 2530.0, 2760.0, 2990.0, 3220.0, 3450.0, 3680.0]
		self.discrete = False
		self.supportDcMode = False # Support DC Charging
		self.support3pMode = False # Support 3 phase charging

		#EVSE (Charging Pole) params are normally copied on startup, but placed in these vars:
		self.evseChargingPowers = None
		self.evseDiscrete = None
		self.evseSupportDcMode = None
		self.evseSupport3pMode = None
		self.evsePreferredPhase = [self.commodities[0]]

		#state
		self.soc = self.capacity
		self.currentJobIdx = 0
		self.currentJob = {}
		self.available = False
			
		#other
		self.jobs = []

		# TouchTable tests
		self.timeTillDeadline = 0

	def startup(self):
		self.lockState.acquire()

		self.soc = self.capacity

		self.jobs.sort()
		#find the current job
		i = -1
		for job in self.jobs:
			if job[1]['startTime'] >= self.host.time():
				break
			else:
				i += 1
		self.currentJobIdx = i

		for i in range(0, len(self.jobs)-1):
			if self.jobs[i][1]['endTime'] >= self.jobs[i+1][1]['startTime']:
				assert(False)

		self.chargingPowers.sort()

		# Copy the settings to the EVSE part of the model
		self.evseChargingPowers = list(self.chargingPowers)
		self.evseDiscrete = self.discrete
		self.evseSupportDcMode = self.supportDcMode
		self.evseSupport3pMode = self.support3pMode

		for c in self.commodities:
			self.consumption[c] = complex(0.0, 0.0)

		# persistence
		if self.persistence != None:
			watchlist = ["capacity", "chargingPowers", "discrete", "supportDcMode", "support3pMode",
						 "soc", "available", "jobs", "currentJob", "currentJobIdx", "plan", "consumption"]
			self.persistence.setWatchlist(watchlist)

		self.lockState.release()

		Device.startup(self)

	def preTick(self, time):
		self.lockState.acquire()
		#first update the SoC
		consumption = 0
		for c in self.commodities:
			consumption += self.consumption[c].real
			
		self.soc = max(0,  min(self.capacity,  self.soc+consumption/(3600.0/self.host.timeBase)))

		#now check if we need to update the state
		if not self.available:
			if self.currentJobIdx+1 < len(self.jobs):
				if self.jobs[self.currentJobIdx+1][1]['startTime'] <= self.host.time():
					#new job to be triggered:
					self.currentJobIdx += 1
					self.currentJob = self.jobs[self.currentJobIdx][1]
					self.setProperties(self.currentJob['evType'])
					self.soc = max(0,  self.capacity - self.currentJob['charge'])
					self.available = True

					self.timeTillDeadline = self.currentJob['endTime'] - self.currentJob['startTime']

					#new job has to start, lets request a planning for it!
					if self.smartOperation and self.controller is not None:
						self.lockState.release()
						if self.controller.parent.devtype == "vfGroupAuctionController" or self.controller.parent.devtype == "vfGroupController":
							self.controller.triggerEvent("vfJobTrigger")
						else:
							self.zCast(self.controller, 'triggerEvent', "stateUpdate")
						self.lockState.acquire()

		else:
			if self.soc >= 0.9999*self.capacity:
				self.soc = self.capacity

			#Update the time:
			self.timeTillDeadline -= self.host.timeBase
			self.currentJob['endTime'] = self.host.time() + self.timeTillDeadline

			if self.currentJob['endTime'] <= self.host.time():
				self.available = False

		self.lockState.release()

		
	def timeTick(self,  time):
		self.prunePlan()

		self.lockState.acquire()

		#finally update the consumption
		for c in self.commodities:
			if self.available:
				if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
					self.consumption[c] = complex(max((-self.soc)/(self.host.timeBase/3600.0),  min(self.plan[c][0][1].real,  (self.capacity-self.soc)/(self.host.timeBase/3600.0))), 0.0)
				else:
					self.consumption[c] = complex(max((-self.soc)/(self.host.timeBase/3600.0),  min(self.chargingPowers[-1],  (self.capacity-self.soc)/(self.host.timeBase/3600.0))), 0.0)
			else:
				self.consumption[c] = complex(0.0, 0.0)
			
			#add optional reactive power
			try:
				if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
					if self.consumption[c].real < self.chargingPowers[-1]:
						qmax = math.sqrt((self.chargingPowers[-1]*self.chargingPowers[-1]) - (self.consumption[c].real*self.consumption[c].real))
						self.consumption[c] += complex(0.0, max(-1*qmax, min(self.plan[c][0][1].imag, qmax)))
			except:
				pass
				# Does not work yet with negative powers (Vehicle 2 Grid)

		if self.persistence != None:
			self.persistence.save()

		self.lockState.release()
	
	def logStats(self, time):
		self.lockState.acquire()

		try:
			for c in self.commodities:
				self.logValue("W-power.real.c."+c,  self.consumption[c].real)
				self.logValue("W-power.imag.c."+c, self.consumption[c].imag)
				if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
					self.logValue("W-power.plan.real.c."+c, self.plan[c][0][1].real)
					self.logValue("W-power.plan.imag.c."+c, self.plan[c][0][1].imag)
		except:
			pass

		self.logValue("Wh-energy.soc",  self.soc)
		if self.available:
			self.logValue("b-available",  1)
		else:
			self.logValue("b-available",  0)
		self.logValue("n-state-job", self.currentJobIdx)

		self.lockState.release()

#### INTERFACING
	def getProperties(self):
		r = Device.getProperties(self) 	# Get the properties of the overall Device class, which already includes global properties

		self.lockState.acquire()

		# Populate the result dict
		r['available'] = self.available
		r['soc'] = self.soc
		r['capacity'] = self.capacity
		r['chargingPowers'] = self.chargingPowers
		r['discrete'] = self.discrete

		r['jobs'] = self.jobs
		r['currentJobIdx'] = self.currentJobIdx
		r['currentJob'] = self.currentJob

		self.lockState.release()
		return r


#### LOCAL HELPERS
	def addJob(self, startTime, endTime, charge, ev=None):
		self.lockState.acquire()
		errorFlag = False

		# Apply the offset upon loading jobs:
		startTime -= self.timeOffset
		endTime -= self.timeOffset

		j = {}
		assert(startTime < endTime)
		assert(charge > 0)
		
		j['startTime'] = startTime
		j['endTime'] = min(endTime,  startTime + 24*3600)
		j['charge'] = min(charge, self.capacity)
		j['evType'] = None

		# Select the ev type
		if ev in evTypes:
			j['evType'] = dict(evTypes[ev])
			assert(j['evType']['chargingPowers'][-1] > j['evType']['chargingPowers'][0])
		
		#some checks on validity of the input:
		#NOTE: Not checking if charging is feasible! The rest should handle this imho
		if len(self.jobs) > 0 and j['startTime'] <= self.jobs[-1][1]['endTime']:
			errorFlag = True
			self.logError("Inconsistent job specification!")
		
		job = (len(self.jobs),  dict(j))
		if not errorFlag:
			self.jobs.append(job)

		self.lockState.release()


	def setProperties(self, evType):
		if evType != None:
			# Set the parameters according to an EVType
			self.capacity = evType['capacity']
			self.discrete = self.evseDiscrete or evType['discrete'] 	# If either can accept continuous, then discrete is definitely possible
			self.supportDcMode = self.evseSupportDcMode and evType['supportDcMode']
			self.support3pMode = self.evseSupport3pMode and evType['support3pMode']

			# Now select the charging powers:
			if not self.discrete:
				self.chargingPowers = [max(self.evseChargingPowers[0], evType['chargingPowers'][0]), min(self.evseChargingPowers[-1], evType['chargingPowers'][-1])]
			else:
				# We use the EVSE capabilities, in range of the EV (i.e. EVSE is LEADING)
				minimum = max(self.evseChargingPowers[0], evType['chargingPowers'][0])
				maximum = min(self.evseChargingPowers[-1], evType['chargingPowers'][-1])
				self.chargingPowers = []

				if evType['discrete']:
					for power in evType['chargingPowers']:
						if power >= minimum and power <= maximum:
							self.chargingPowers.append(power)
				else:
					for power in self.evseChargingPowers:
						if power >= minimum and power <= maximum:
							self.chargingPowers.append(power)

			if len(self.chargingPowers) < 2 or self.chargingPowers[0] >= self.chargingPowers[-1]:
				# Error, invalid values..
				self.chargingPowers = self.evseChargingPowers
				self.logError("Charging powers incorrect between EVSE and EV")

		else:
			# No EV Type, reset to the defaults:
			self.chargingPowers = list(self.evseChargingPowers)
			self.discrete = self.evseDiscrete
			self.supportDcMode = self.evseSupportDcMode
			self.support3pMode = self.evseSupport3pMode

		self.chargingPowers.sort() # Just to be sure


# Notes to consider when "upgrading" this model and the timeshiftables for real situations, see T205
# - with the EVSE integration, it may be wise to create a specific EVdev class instead to keep the bts-class abstract
# - The controller also needs an update
# - This type of support, e.g. using different washing schemes, should also be integrated in the TS device
# - This asks for an improved structure / job system / device model type for a future version of DEMKit
