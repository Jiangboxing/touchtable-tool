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



from dev.bufDev import BufDev

import math
from enum import Enum

class BatteryState(Enum):
	CHARGING = 2
	IDLE_AFTER_CHARGING = 1
	STARTING = 0
	IDLE_AFTER_DISCHARGING = -1
	DISCHARGING = -2

# Buffer device
class RealBufDev(BufDev):	#This buffer device (a battery as modelled by Bart Homan) is a BufferDevice, which is a Device, which is an Entity for the model
	def __init__(self,  name,  host, meter = None, ctrl = None):
		BufDev.__init__(self,  name,  host)

		# Capacity and powers are inherited from the BufDev

		# The following realistic battery parameters are obtained through analysis by Bart Homan and presented in the ISGT 2018 paper
		# FIXME: Add proper reference when the paper is actually published
		# Current limits for the battery
		self.chargingCurrents = [-4.0, 0.4]

		# Realistic buffer params for the small real buffer
		self.capacity = 43.2 				# Wh
		self.initialSoC = 43.2*0.4			# Wh
		self.chargingPowers = [-27.6, 2.76] # Wh

		self.discrete = False

		self.alpha = 0.00003030  #in V/A
		self.beta = 0.268 * self.timeBase # No units
		self.gamma = 2.684 # in seconds
		self.delta = 24381.46177 # in V/A

		# Battery state variables
		self.voltage = 6.0
		self.current = 0.0

		# Voltage characteristics:
		self.minVoltage = 5.5
		self.nomVoltage = 6.0 # Nominal voltage
		self.maxVoltage = 6.9

		# Initialize the state
		self.state = BatteryState.STARTING

		# Battery state specific variables, they are set when required:
		self.startDischargingVoltage = 6.0
		self.startDischargingSoC = self.initialSoC
		self.startIdleVoltage = 6.0
		self.startIdleTime = None


	def startup(self):
		BufDev.startup(self)

		assert(self.timeBase == 60) # Otherwise, this model breaks down!
		assert(self.discrete == False) # Model doesn't (yet) support this
		assert(len(self.commodities) == 1) # For now we assume we can only use one commodity

		self.chargingPowers.sort() #In case we accidentally didn't order them

		# Battery state specific variables, make sure we have some clever choices at start
		self.startDischargingVoltage = self.nomVoltage
		self.startDischargingSoC = self.initialSoC
		self.startIdleVoltage = self.nomVoltage
		self.startIdleTime = self.host.time()

	def preTick(self, time):
		# Obtain the total consumption over all commodities
		consumption = 0.0
		for c in self.commodities:
			consumption += self.consumption[c].real

		# Determine the current based on the consumption
		if consumption < 0.0001 and consumption > -0.0001:
			self.current = 0.0
		else:
			self.current = min(self.chargingCurrents[-1], max(self.chargingCurrents[0], (consumption / self.voltage) ) )

		# Allowance of charging when battery is full (i.e. voltage = maxVoltage) is now covered by the allowed chargingpowers at the end.

		# DETERMINE NEW STATE
		if self.current > 0: #Now we are charging
			self.state = BatteryState.CHARGING
			# Optionally, we could introduce a voltage recovery hack if we have the discharing -> charging transition

		elif self.current < 0: #Now we are discharging
			if self.state != BatteryState.DISCHARGING:
				self.startDischargingVoltage = self.voltage #...then we need to remember the voltage...
				self.startDischargingSoC = self.soc #...as well as the SoC
			self.state = BatteryState.DISCHARGING

		elif self.state == BatteryState.CHARGING:  #Current is 0 but we were charging before
			self.state = BatteryState.IDLE_AFTER_CHARGING

		elif self.state == BatteryState.DISCHARGING: #Current is 0 but we were discharging before
			self.state = BatteryState.IDLE_AFTER_DISCHARGING
			self.startIdleVoltage = self.voltage #Check which voltage we actually need to use -> the voltage directly after we stopped discharging
			self.startIdleTime = time #Make sure this is the actual timestamp (also checking if we're using it of the correct interval)


		# DETERMINE NEW VOLTAGE
		if self.state == BatteryState.CHARGING:
			self.voltage = self.voltage + (self.current / self.delta) * self.timeBase

		elif self.state == BatteryState.IDLE_AFTER_CHARGING:
			pass # Voltage remains unchanged

		elif self.state == BatteryState.DISCHARGING:
			self.voltage = self.voltage + self.alpha*self.timeBase * self.current / (self.startDischargingSoC / self.capacity)

		elif self.state == BatteryState.IDLE_AFTER_DISCHARGING: #Here only voltage will rise, no change in SoC will be visible, only after applying the first current again
			timeDelta = (time - self.startIdleTime)
			exponent = 1
			try:
				exponent = math.exp( -timeDelta / ( (self.beta * timeDelta) + self.gamma * self.timeBase) )
			except:
				exponent = 1.0 #option to have division by zero for the lithium ion battery
			self.voltage = self.startIdleVoltage + ( (self.startDischargingVoltage - self.startIdleVoltage) * (1 - exponent ) )

		elif self.state == BatteryState.STARTING:
			pass

		else:
			assert(False) # Illegal state

		# Check voltage bounds
		self.voltage = max(self.minVoltage, min(self.voltage, self.maxVoltage))

		# Determine the new SoC
		self.soc += self.voltage * self.current * (self.timeBase / 3600.0) #As E_max or capacity is in Wh, we need Delta t in hours

		# now make sure that we are still in the SoC constraints:
		self.soc = min(self.capacity, max(self.soc, 0.0))

		# Rest voltage when we are close to zero SoC
		if self.soc <= self.capacity*0.005: #If the battery is empty...
			self.voltage = self.minVoltage

		# Determine the allowed powers for the next interval
		# Overwrite charging powers
		self.chargingPowers = []
		self.chargingPowers.append(self.chargingCurrents[0] * self.voltage)
		self.chargingPowers.append(self.chargingCurrents[-1] * self.voltage)

		assert(self.chargingPowers[1] >= self.chargingPowers[0])

		# Check if we need to notify of marks
		BufDev.checkFillMarks(self)


	def timeTick(self,  time):
		BufDev.timeTick(self, time)

		self.chargingPowers.append(max((self.chargingCurrents[0] * self.voltage), -1*self.soc*self.timeBase) )
		self.chargingPowers.append(min((self.chargingCurrents[-1] * self.voltage), (self.capacity-self.soc)*self.timeBase) )

		# Check if the consumption set according to the controller makes sense.
		for c in self.commodities:
			if self.consumption[c].real < self.chargingPowers[0]:
				self.consumption[c] = self.chargingPowers[0]
			elif self.consumption[c].real > self.chargingPowers[1]:
				self.consumption[c] = self.chargingPowers[1]

			# Check if the voltage allows us to consume:
			if self.voltage <= self.minVoltage and self.consumption[c].real < 0.0:
				self.consumption[c] = complex(0.0, 0.0)
			elif self.voltage >= self.maxVoltage and self.consumption[c].real > 0.0:
				self.consumption[c] = complex(0.0, 0.0)

	def logStats(self, time):
		# logging
		BufDev.logStats(self, time)

		#Additions of the advanced model
		self.logValue("V-voltage", self.voltage)
		self.logValue("I-current", self.current)


#### INTERFACING
	def getProperties(self):
		r = BufDev.getProperties(self) 	# Get the properties of the overall Device class, which already includes global properties
		return r