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


from dev.loadDev import LoadDev

import math

# Bufferconverter device, the buffer level is based on the secondary side (e.g. heat)!

##### NOTICE #####
# Note that there is a better thermal model for heating the the thermal folder!

class BufConvDev(LoadDev):	
	def __init__(self,  name,  host):
		LoadDev.__init__(self,  name,  host)
		self.devtype = "BufferConverter"
		
		#params
		self.capacity = 250000 #in kWh
		self.initialSoC = 125000 #in kWh
		self.soc = self.initialSoC #state of charge
		self.cop = 4.0 #coefficient of performance
		
		self.prevConsumption = 0.0
		
		#define 2 entries for a continuous range
		self.chargingPowers = [0.0, 30000.0]
# 		self.chargingPowers = [0.0, 1380.0, 1610.0, 1840.0, 2070.0, 2300.0, 2530.0, 2760.0, 2990.0, 3220.0, 3450.0, 3680.0]
		self.discrete = False
		
		self.lossOverTime = 0
		
		#Marks to trigger replanning
		self.lowMark = 1000
		self.highMark = 11000 
		self.flagLowMark = False
		self.flagHighMark = False
		
		#loss profile, overrides lossOverTime
		self.filename = None
		
		#state
		self.selfConsumption = 0.0

	def startup(self):
		self.lockState.acquire()

		self.soc = self.initialSoC
		self.chargingPowers.sort()

		if self.highMark > self.capacity:
			self.highMark = 0.9 * self.capacity
			self.logWarning("Predefined highmark not appropriate. I fixed this for you!")
		if self.lowMark > self.highMark or self.lowMark < 0:
			self.lowMark = 0.1 * self.capacity
			self.logWarning("Predefined lowmark not appropriate. I fixed this for you!")

		#initialize flags
		if self.soc > self.highMark:
			self.flagHighMark = True
		elif self.soc < self.lowMark:
			self.flagLowMark = True

		for c in self.commodities:
			self.consumption[c] = complex(0.0, 0.0)

		# persistence
		if self.persistence != None:
			watchlist = ["soc", "selfConsumption", "consumption", "flagLowMark", "flagHighMark", "plan"]
			self.persistence.setWatchlist(watchlist)

		self.lockState.release()

		LoadDev.startup(self)

	def preTick(self, time):
		self.lockState.acquire()
		consumption = 0
		for c in self.commodities:
			consumption += self.consumption[c].real
		
		#First update the SoC
		self.soc += consumption * (self.host.timeBase / 3600.0) * self.cop
		self.soc -= self.selfConsumption * (self.host.timeBase / 3600.0)
		
		#now make sure that we are still in the SoC constraints:
		self.soc = min(self.capacity, max(self.soc, 0))
		
		#avoid weird rounding stuff:
		if self.soc >= self.capacity*0.99999:
			self.soc = self.capacity

		self.lockState.release()

		#request for a replanning on marks and (re)set the flags accordingly
		if self.smartOperation and self.controller is not None:

			#test for marks and set flags accordingly
			if self.soc <= self.lowMark and self.flagLowMark == False:
				self.zCast(self.controller, 'triggerEvent', "stateUpdate")
				self.flagLowMark = True
			if self.soc >= self.highMark and self.flagHighMark == False:
				self.zCast(self.controller, 'triggerEvent', "stateUpdate")
				self.flagHighMark = True
				
			#Reset the flags	
			if self.flagHighMark == True and self.soc < self.highMark:
				self.flagHighMark = False
			if 	self.flagLowMark == True and self.soc > self.lowMark:
				self.flagLowMark = False

	
	def timeTick(self,  time):			
		self.prunePlan()

		self.lockState.acquire()
		#set the next consumptions, not considering real constraints on the buffer
		#Add the self-consumption properly
		if self.filename is not None :
			#File specified, use that as self consumption
			self.selfConsumption = self.readValue(time)
		else:
			self.selfConsumption = self.lossOverTime

		totalConsumption = 0	
		for c in self.commodities:	
			if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
				self.consumption[c] = complex(self.plan[c][0][1].real, 0.0)
			else:
				self.consumption[c] = complex(self.selfConsumption/self.cop, 0.0)
			totalConsumption += self.consumption[c].real

		# buffer underrun / overflow check and make the device fix this!
		if ((self.soc + totalConsumption*self.cop + self.selfConsumption) * (self.host.timeBase / 3600.0)) > self.capacity:
			#We have a buffer overflow:
			reduceBy = (((self.soc + totalConsumption*self.cop + self.selfConsumption) * (self.host.timeBase / 3600.0)) - self.capacity) / (self.host.timeBase / 3600.0) / len(self.commodities)
			
			for c in self.commodities:
				self.consumption[c] = max(self.chargingPowers[0], min(self.consumption[c].real-reduceBy, self.chargingPowers[-1]))
				self.logWarning("Buffer overflow")

		elif ((self.soc + totalConsumption*self.cop + self.selfConsumption) * (self.host.timeBase / 3600.0)) < 0.0:
			#We have a buffer underflow:
			increaseBy = 0.0
			if self.strictComfort:
				increaseBy = ((abs(self.soc + totalConsumption*self.cop + self.selfConsumption) * (self.host.timeBase / 3600.0))) / (self.host.timeBase / 3600.0) / len(self.commodities)
			
			for c in self.commodities:
				self.consumption[c] = max(self.chargingPowers[0], min(self.consumption[c].real+increaseBy, self.chargingPowers[-1]))
				self.logWarning("Buffer underflow")
		
		for c in self.commodities:	
			#add optional reactive power	
			if c in self.plan and len(self.plan[c]) > 0:
				qmax = math.sqrt((self.chargingPowers[-1]*self.chargingPowers[-1]) - (self.consumption[c].real*self.consumption[c].real))
				self.consumption[c] += complex(0, max(-1*qmax, min(self.plan[c][0][1].imag, qmax)))

		self.lockState.release()
	
	def logStats(self, time):			
		#logging
		self.lockState.acquire()
		try:
			for c in self.commodities:
				self.logValue("W-power.real.c." + c, self.consumption[c].real)
				self.logValue("W-power.imag.c." + c, self.consumption[c].imag)
				if c in self.plan and len(self.plan[c]) > 0:
					self.logValue("W-power.plan.real.c."+c, self.plan[c][0][1].real)
					self.logValue("W-power.plan.imag.c."+c, self.plan[c][0][1].imag)
		except:
			pass

		self.logValue("Wh-energy.soc", self.soc)
		self.logValue("W-power.real.secondary", self.selfConsumption)
		self.logValue("b-available", 1)

		self.lockState.release()
			
	def shutdown(self):
		pass	

#### INTERFACING
	def getProperties(self):
		r = LoadDev.getProperties(self) 	# Get the properties of the overall Device class, which already includes global properties

		self.lockState.acquire()
		# Populate the result dict
		r['soc'] = self.soc
		r['cop'] = self.cop

		r['capacity'] = self.capacity
		r['chargingPowers'] = self.chargingPowers
		r['selfConsumption'] = self.selfConsumption
		r['discrete'] = self.discrete

		r['lossOverTime'] = self.lossOverTime

		self.lockState.release()

		return r