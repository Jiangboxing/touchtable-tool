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

import math

# Buffer device
class BufDev(Device):	
	def __init__(self,  name,  host, meter = None, ctrl = None, congestionPoint = None):
		Device.__init__(self,  name,  host)
		self.devtype = "Buffer"
		
		#params
		self.capacity = 12000 #in Wh
		self.initialSoC = 6000 #in Wh
		self.soc = self.initialSoC #state of charge

		self.prevConsumption = 0.0
		
		#define 2 entries for a continuous range
		self.chargingPowers = [-3700, 3700]
		#self.chargingPowers = [-3680.0, -3450.0, -3220.0, -2990.0, -2760.0, -2530.0, -2300.0, -2070.0, -1840.0, -1610.0, -1380.0, 0.0, 1380.0, 1610.0, 1840.0, 2070.0, 2300.0, 2530.0, 2760.0, 2990.0, 3220.0, 3450.0, 3680.0]

		# Game / teaching strategy for charging from the local grid.
		# solar_only: only charge from local surplus production.
		# smart: store surplus solar, discharge down to 20% when one high-power load is active.
		# manual_charge/manual_discharge: user-triggered charge/discharge actions.
		self.gridChargingStrategy = "solar_only"
		self.gridReserveTargetSoc = 0.80
		self.smartDischargeFloorSoc = 0.20
		self.gridChargePowerLimit = 1000
		self.gridChargeLoadThreshold = 1000
		self.smartHighLoadThreshold = 1500
		self.manualChargePowerLimit = 1000
		self.manualDischargePowerLimit = 1850
		self.gridChargingSource = "idle"
		self.gridChargingBlocked = False

		self.chargingEfficiency = None #[1, 1] 	# Efficiency currently only works in discrete mode
										 		# It indicates how much energy flows in/out of the storage in reality.
												# For Powers > 0 -> Efficiency  < 1 due to conversion losses, i.e. energy gets lost and therefore not stord
												# For Powers < 0 -> Efficiecncy > 1, reverse reasoning
												# example: [1/0.9, 1/0.9, 1, 0.9, 0.9] for powers [-2000, -1000, 0, 1000, 2000]
												# Note that as usual: Powers are given w.r.t. what is seen from the connection point.

		self.discrete = False
		self.useInefficiency = None 		# variable will be setup on startup

		self.lossOverTime = 0
		
		#Marks to trigger replanning
		self.lowMark = 1000
		self.highMark = 11000 
		self.flagLowMark = False
		self.flagHighMark = False
		
		#state
		self.selfConsumption = 0.0
		
		self.balancing = False

		# Fixed param, required to make the buffer and the bufferconverter compatible with similar control methods
		self.cop = 1.0
		
		self.parent = None
		self.meter = None
		if meter != None:
			self.balancing = True 	# Enable real time control
			self.meter = meter
			if ctrl != None:
				self.parent = ctrl

		# Set the congestion point
		# NOTE: Adding a congestionpoint without control implies you want to obey this limit at all cost
		self.congestionPoint = congestionPoint

	def startup(self):
		self.lockState.acquire()
		self.soc = min(self.initialSoC, self.capacity)
		self.chargingPowers.sort()

		if self.highMark > self.capacity:
			self.highMark = 0.9 * self.capacity
			self.logWarning("Predefined highmark not appropriate. I fixed this for you!")
		if self.lowMark >= self.highMark or self.lowMark < 0:
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

		if self.chargingEfficiency is not None:
			self.useInefficiency = True
		else:
			self.useInefficiency = False
			self.chargingEfficiency = [1] * len(self.chargingPowers)

		# Determine internalpowers
		self.internalPowers = []
		for i in range(0, len(self.chargingPowers)):
			self.internalPowers.append(self.chargingPowers[i] * self.chargingEfficiency[i])

		if self.chargingEfficiency is not None:
			assert(len(self.chargingEfficiency) == len(self.chargingPowers))

			prev = self.internalPowers[0] - 1
			for val in self.internalPowers:
				assert(val.real > prev.real)	# For the algorithm to work, we still need to ensure that the resulting powers the optimization uses increase
				prev = val

		self.lockState.release()

		Device.startup(self)

	def preTick(self, time):
		self.lockState.acquire()
		consumption = 0
		for c in self.commodities:
			# find associated efficiency
			if not self.useInefficiency:
				consumption += self.consumption[c].real
			else:
				consumption += self.chargeForConsumption(self.consumption[c].real)


		
		#First update the SoC
		self.soc += consumption * (self.host.timeBase / 3600.0)
		self.soc -= self.selfConsumption * (self.host.timeBase / 3600.0)
		
		#now make sure that we are still in the SoC constraints:
		self.soc = min(self.capacity, max(self.soc, 0))
		
		#avoid weird rounding stuff:
		if self.soc >= self.capacity*0.99999:
			self.soc = self.capacity

		self.lockState.release()

		self.checkFillMarks()

	
	def timeTick(self,  time):			
		self.prunePlan()

		planning = {}
		for c in self.commodities:
			planning[c] = complex(0.0, 0.0)

		self.lockState.acquire()
		#Add the self-consumption properly
		self.selfConsumption = self.lossOverTime

		totalConsumption = 0
		#
		# # Normal operation with a controller
		# if not self.balancing:
		# 	for c in self.commodities:
		# 		if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
		# 			self.consumption[c] = self.plan[c][0][1].real
		# 		else:
		# 			self.consumption[c] = complex(0.0, 0.0)
		#
		# else:
		# 	# Perform online control algorithms
		# 	self.onlineControl()

		if self.parent is None:
			for c in self.commodities:
				if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
					self.consumption[c] = self.plan[c][0][1].real
				else:
					if self.meter is not None:
						self.onlineControl()
					else:
						self.consumption[c] = complex(0.0, 0.0)

		else:
			# Perform online control algorithms
			self.onlineControl()

		# Perform consistency checks.
		for c in self.commodities:
			totalConsumption += self.consumption[c].real

		# buffer underrun / overflow check and make the device fix this!
		if ((self.soc * (3600.0 / self.host.timeBase) + totalConsumption + self.selfConsumption) * (self.host.timeBase / 3600.0)) > self.capacity:
			#We have a buffer overflow:
			reduceBy = (((self.soc * (3600.0 / self.host.timeBase) + totalConsumption + self.selfConsumption) * (self.host.timeBase / 3600.0)) - self.capacity) / (self.host.timeBase / 3600.0) / len(self.commodities)
			for c in self.commodities:
				self.consumption[c] = max(self.chargingPowers[0]/self.chargingEfficiency[0], min(self.consumption[c].real-self.consumptionForCharge(reduceBy), self.chargingPowers[-1]/self.chargingEfficiency[-1]))

		elif ((self.soc * (3600.0 / self.host.timeBase) + totalConsumption + self.selfConsumption) * (self.host.timeBase / 3600.0)) < 0.0:
			#We have a buffer underflow:
			increaseBy = ((abs(self.soc * (3600.0 / self.host.timeBase) + totalConsumption + self.selfConsumption) * (self.host.timeBase / 3600.0))) / (self.host.timeBase / 3600.0) / len(self.commodities)
			for c in self.commodities:
				self.consumption[c] = max(self.chargingPowers[0]/self.chargingEfficiency[0], min(self.consumption[c].real+self.consumptionForCharge(increaseBy), self.chargingPowers[-1]/self.chargingEfficiency[-1]))


		if not self.balancing:
			for c in self.commodities:
				#add optional reactive power
				if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
					if self.consumption[c].real < self.chargingPowers[-1]:
						try:
							qmax = math.sqrt((self.chargingPowers[-1]*self.chargingPowers[-1]) - (self.consumption[c].real*self.consumption[c].real))
							self.consumption[c] += complex(0.0, max(-1*qmax, min(self.plan[c][0][1].imag, qmax)))
						except:
							pass # Nearly 0, math error. Reactive power control makes no sense in this exception

		self.lockState.release()
	
	def logStats(self, time):
		self.lockState.acquire()
		try:
			for c in self.commodities:
				self.logValue("W-power.real.c." + c, self.consumption[c].real)
				self.logValue("W-power.imag.c." + c, self.consumption[c].imag)
				if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
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

	def checkFillMarks(self):
		#request for a replanning on marks and (re)set the flags accordingly
		if self.controller is not None:
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

#### INTERFACING
	def getProperties(self):
		r = Device.getProperties(self) 	# Get the properties of the overall Device class, which already includes global properties

		self.lockState.acquire()
		# Populate the result dict
		r['soc'] = self.soc
		r['cop'] = self.cop
		r['capacity'] = self.capacity
		r['chargingPowers'] = self.chargingPowers
		r['selfConsumption'] = self.selfConsumption
		r['internalPowers'] = self.internalPowers
		r['chargingEfficiency'] = self.chargingEfficiency
		r['discrete'] = self.discrete
		r['useInefficiency'] = self.useInefficiency
		r['gridChargingStrategy'] = self.gridChargingStrategy
		r['gridReserveTargetSoc'] = self.gridReserveTargetSoc
		r['smartDischargeFloorSoc'] = self.smartDischargeFloorSoc
		r['gridChargePowerLimit'] = self.gridChargePowerLimit
		r['gridChargeLoadThreshold'] = self.gridChargeLoadThreshold
		r['smartHighLoadThreshold'] = self.smartHighLoadThreshold
		r['manualChargePowerLimit'] = self.manualChargePowerLimit
		r['manualDischargePowerLimit'] = self.manualDischargePowerLimit
		r['gridChargingSource'] = self.gridChargingSource
		r['gridChargingBlocked'] = self.gridChargingBlocked
		self.lockState.release()

		return r
				

#### Online control system
	def maxChargingPowerForStrategy(self, netLoadWithoutBattery):
		if self.gridChargingStrategy not in ["solar_only", "smart", "manual_charge", "manual_discharge"]:
			self.gridChargingStrategy = "solar_only"

		solarSurplusLimit = max(0.0, -1.0 * netLoadWithoutBattery)
		if self.gridChargingStrategy == "solar_only":
			return solarSurplusLimit
		if self.gridChargingStrategy == "manual_discharge":
			return 0.0
		if self.gridChargingStrategy == "smart":
			return solarSurplusLimit

		if self.capacity <= 0:
			return solarSurplusLimit

		socFraction = self.soc / self.capacity
		targetSoc = self.gridReserveTargetSoc
		chargeLimit = self.gridChargePowerLimit
		loadThreshold = self.gridChargeLoadThreshold

		if self.gridChargingStrategy == "manual_charge":
			return max(solarSurplusLimit, min(self.manualChargePowerLimit, self.chargingPowers[-1]))

		gridChargeLimit = 0.0
		if socFraction < targetSoc and netLoadWithoutBattery < loadThreshold:
			gridChargeLimit = min(chargeLimit, loadThreshold - max(0.0, netLoadWithoutBattery))

		return max(solarSurplusLimit, gridChargeLimit)

	def activeChargingTargetSoc(self):
		if self.gridChargingStrategy == "smart":
			return self.gridReserveTargetSoc
		return 1.0

	def applyManualStrategy(self, localLoadWithoutBattery):
		if self.capacity <= 0:
			return 0.0

		timeBaseHours = self.host.timeBase / 3600.0

		if self.gridChargingStrategy == "manual_charge":
			capacityLimitedCharge = max(0.0, (self.capacity - self.soc) / timeBaseHours)
			chargePower = min(self.manualChargePowerLimit, self.chargingPowers[-1], capacityLimitedCharge)
			if chargePower <= 0.0:
				self.gridChargingSource = "idle"
				return 0.0

			solarSurplus = max(0.0, -1.0 * localLoadWithoutBattery)
			self.gridChargingSource = "solar" if chargePower <= solarSurplus + 1.0 else "grid"
			return chargePower

		availableDischarge = max(0.0, self.soc / timeBaseHours)
		dischargePower = min(max(0.0, localLoadWithoutBattery), self.manualDischargePowerLimit, abs(self.chargingPowers[0]), availableDischarge)
		self.gridChargingSource = "discharging" if dischargePower > 0.0 else "idle"
		return -1.0 * dischargePower

	def applySmartStrategy(self, currentPower, localLoadWithoutBattery):
		if self.capacity <= 0:
			return 0.0

		socFraction = self.soc / self.capacity
		timeBaseHours = self.host.timeBase / 3600.0
		isHighLoad = localLoadWithoutBattery >= self.smartHighLoadThreshold

		if isHighLoad:
			if socFraction <= self.smartDischargeFloorSoc:
				self.gridChargingSource = "idle"
				return 0.0

			availableDischarge = max(0.0, (self.soc - (self.smartDischargeFloorSoc * self.capacity)) / timeBaseHours)
			dischargePower = min(localLoadWithoutBattery, abs(self.chargingPowers[0]), availableDischarge)
			self.gridChargingSource = "discharging" if dischargePower > 0.0 else "idle"
			return -1.0 * dischargePower

		if socFraction >= self.gridReserveTargetSoc:
			self.gridChargingSource = "idle"
			return 0.0

		maxChargingPower = self.maxChargingPowerForStrategy(localLoadWithoutBattery)
		capacityLimitedCharge = max(0.0, (self.capacity - self.soc) / timeBaseHours)
		chargePower = min(maxChargingPower, self.chargingPowers[-1], capacityLimitedCharge)
		if chargePower <= 0.0:
			self.gridChargingSource = "idle"
			return 0.0

		solarSurplus = max(0.0, -1.0 * localLoadWithoutBattery)
		self.gridChargingSource = "solar" if chargePower <= solarSurplus + 1.0 else "grid"
		return chargePower

	def onlineControl(self):
		planning = {}
		for c in self.commodities:
			planning[c] = complex(0.0, 0.0)
		# Initialize local vats
		target = {}
		load = {}
		nonBufferLoad = {}

		for c in self.commodities:
			target[c] = complex(0.0, 0.0)
			load[c] = complex(0.0, 0.0)
			nonBufferLoad[c] = complex(0.0, 0.0)

		# Obtain the current power consumption of all meters
		if type(self.meter) is list:
			for m in self.meter:
				m.measure(self.host.time())
				cons = self.zGet(m, 'consumption')
				nonBufferCons = self.zGet(m, 'nonBufferConsumption')
				for c in self.commodities:
					try:
						load[c] += cons[c]
					except:
						pass
					try:
						nonBufferLoad[c] += nonBufferCons[c]
					except:
						pass
		else:
			self.meter.measure(self.host.time())
			for c in self.commodities:
				cons = self.zGet(self.meter, 'consumption')
				nonBufferCons = self.zGet(self.meter, 'nonBufferConsumption')
				try:
					load[c] += cons[c]
				except:
					pass
				try:
					nonBufferLoad[c] += nonBufferCons[c]
				except:
					nonBufferLoad[c] = load[c] - self.consumption[c]

		if self.smartOperation and self.parent is not None:
			for c in self.commodities:
				target[c] = self.zCall(self.parent, 'getPlan', self.host.time(), c)
				if self.congestionPoint is not None:
					target[c] = complex(max(self.congestionPoint.getLowerLimit(c).real, min(target[c].real, self.congestionPoint.getUpperLimit(c).real)),
										max(self.congestionPoint.getLowerLimit(c).imag, min(target[c].imag, self.congestionPoint.getUpperLimit(c).imag)))

		# No control, but a congestionpoint
		elif self.congestionPoint is not None:
			for c in self.commodities:
				# Obey the congestion point limits if required
				if load[c].real - self.consumption[c].real < self.congestionPoint.getLowerLimit(c).real:
					target[c] = self.congestionPoint.getLowerLimit(c).real
				elif load[c].real - self.consumption[c].real > self.congestionPoint.getUpperLimit(c).real:
					target[c] = self.congestionPoint.getUpperLimit(c).real

				# Otherwise, try to bring the SoC to the middle (50%)
				elif self.soc >= 0.51*self.capacity:
					target[c] = max(self.congestionPoint.getLowerLimit(c).real, ((0.5*self.capacity - self.soc)*(3600/self.timeBase) + load[c] - self.consumption[c]).real)
				elif  self.soc <= 0.49*self.capacity:
					target[c] = min(self.congestionPoint.getUpperLimit(c).real, ((0.5*self.capacity - self.soc)*(3600/self.timeBase) + load[c] - self.consumption[c]).real)
				else:
					# In the other case, we will do nothing and stay at the 50% SoC
					target[c] = load[c]  - self.consumption[c]
					target[c] = max(self.congestionPoint.getLowerLimit(c).real, min(target[c].real, self.congestionPoint.getUpperLimit(c).real))

		# Now set the power, obeying the limits of the device
		consumption = {}
		self.gridChargingBlocked = False
		self.gridChargingSource = "idle"
		for c in self.commodities:
			localLoadWithoutBattery = nonBufferLoad[c].real
			consumption[c] = self.consumption[c] + (target[c] - load[c])

			# Make sure all limits/bounds of the devices are met
			cons = max(((-self.soc)/(self.host.timeBase/3600.0)),  min(consumption[c].real,  ((self.capacity-self.soc)/(self.host.timeBase/3600.0)) ) )
			self.consumption[c] = max(self.chargingPowers[0], min(cons.real, self.chargingPowers[-1]))
			maxChargingPower = self.maxChargingPowerForStrategy(localLoadWithoutBattery)

			if self.gridChargingStrategy == "smart":
				self.consumption[c] = self.applySmartStrategy(self.consumption[c], localLoadWithoutBattery)
			elif self.gridChargingStrategy in ["manual_charge", "manual_discharge"]:
				self.consumption[c] = self.applyManualStrategy(localLoadWithoutBattery)
			elif self.gridChargingStrategy == "solar_only" and self.consumption[c] < 0.0:
				self.consumption[c] = 0.0
			elif self.consumption[c] < 0.0 and localLoadWithoutBattery <= 0.0:
				self.consumption[c] = 0.0
			elif self.consumption[c] < 0.0:
				self.consumption[c] = max(self.consumption[c], -1.0 * localLoadWithoutBattery)

			if self.consumption[c] > 0.0:
				if self.consumption[c] > maxChargingPower:
					self.gridChargingBlocked = maxChargingPower <= 0.0
					self.consumption[c] = max(0.0, maxChargingPower)

				if self.consumption[c] > 0.0:
					solarSurplus = max(0.0, -1.0 * localLoadWithoutBattery)
					if self.consumption[c] <= solarSurplus + 1.0:
						self.gridChargingSource = "solar"
					else:
						self.gridChargingSource = "grid"
			elif self.consumption[c] < 0.0:
				self.gridChargingSource = "discharging"

			# Check reactive limits, using a try to prevent issues when reactive power support is not implemented/enabled
			try:
				if self.consumption[c].real < self.chargingPowers[-1]:
					qmax = math.sqrt((self.chargingPowers[-1]*self.chargingPowers[-1]) - (self.consumption[c].real*self.consumption[c].real))
					self.consumption[c] += complex(0.0, max(-1*qmax, min(consumption[c].imag, qmax)))
			except:
				pass


	def chargeForConsumption(self, cons):
		if not self.useInefficiency:
			return cons

		result = 0

		try:
			idx = self.chargingPowers.index(cons.real)
			result = cons.real*self.chargingEfficiency[idx]
		except:
			# Not an exact value in the list
			idx = 0
			while idx < len(self.chargingPowers) and self.chargingPowers[idx] < cons.real:
				idx += 1

			eff = 1
			if idx >= len(self.chargingPowers)-1:
				eff = self.chargingEfficiency[-1]
			else:
				d = (cons.real - self.chargingPowers[idx].real) / (self.chargingPowers[idx+1].real - self.chargingPowers[idx].real)
				eff = (d * self.chargingEfficiency[idx]) + ((1-d) * self.chargingEfficiency[idx+1])
			result = cons * eff

		return result

	def consumptionForCharge(self, charge):
		if not self.useInefficiency:
			return charge

		result = 0

		try:
			idx = self.internalPowers.index(charge.real)
			result = charge.real/self.chargingEfficiency[idx]
		except:
			# Not an exact value in the list
			x = self.chargingPowers[0]
			idx = 0
			while idx < len(self.internalPowers) and self.internalPowers[idx] < charge.real:
				idx += 1

			eff = 1
			if idx >= len(self.internalPowers)-1:
				eff = self.chargingEfficiency[-1]
			else:
				d = (charge.real - self.internalPowers[idx].real) / (self.internalPowers[idx+1].real - self.internalPowers[idx].real)
				eff = (d * self.chargingEfficiency[idx]) + ((1-d) * self.chargingEfficiency[idx+1])
			result = charge / eff

		return result
