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

from ctrl.valleyFilling.vfBtsCtrl import VfBtsCtrl
from ctrl.auction.btsAuctionCtrl import BtsAuctionCtrl
from ctrl.auction.demandFunction import DemandFunction

class VfBtsAuctionCtrl(VfBtsCtrl, BtsAuctionCtrl):
	def __init__(self, name, dev, ctrl, host):
		BtsAuctionCtrl.__init__(self, name, None, None, None)
		VfBtsCtrl.__init__(self, name, dev, ctrl, host)

		self.useEventControl = False
		self.devtype = "VfBufferTimeshiftableController"

	def preTick(self, time):
		VfBtsCtrl.preTick(self, time)
		BtsAuctionCtrl.preTick(self, time)

	def timeTick(self, time):
		#VfBtsCtrl.timeTick(self, time)
		BtsAuctionCtrl.timeTick(self, time)

	def createDemandFunction(self):
		# Synchronize the device state:
		deviceState = self.updateDeviceProperties()

		result = DemandFunction()

		# Static load has no flex
		assert(self.devData['discrete'] == False) #FIXME: Discrete auction not supported currently! See T185

		remainingCharge = self.devData['capacity'] - self.devData['soc']

		if not self.devData['available'] or remainingCharge == 0:
			result.addLine(0,0,result.minComfort, result.maxComfort) #No car available, no other option!
		else:
			# First find out the charge bounds
			maximum = min( remainingCharge*(3600.0/self.host.timeBase), self.devData['chargingPowers'][-1])

			#minimum is a bit harder:
			minimum = self.devData['chargingPowers'][0]
			if (remainingCharge * 3600.0) / max(1, (self.devData['currentJob']['endTime'] - self.host.time() - self.host.timeBase)) >= self.devData['chargingPowers'][-1]:
				minimum = self.devData['chargingPowers'][-1] #deadline approaching, must charge!

			#now determine the preferred level based on SoC and deadline
			preferred = (remainingCharge * 3600.0) / max(1, (self.devData['currentJob']['endTime'] - self.host.time()))

			# The algorithm of Martijn is used, where the charging powers are defined as [0, min, max]
			if len(self.devData['chargingPowers']) == 3:
				comfort = min((preferred / self.devData['chargingPowers'][-1]) * (result.maxComfort-300), result.maxComfort-300 - 1)

				if preferred < self.devData['chargingPowers'][1]:
					preferred = self.devData['chargingPowers'][1]

				#Checks to make sure that the function will be concave
				minimum = min(maximum, minimum)
				if preferred > maximum:
					preferred = maximum
				if minimum > preferred:
					preferred = minimum

				result.addLine(maximum, preferred, result.minComfort + 300, 0)
				result.addLine(preferred, preferred, 0, comfort)
				result.addLine(preferred, minimum, comfort, comfort + 1)
				result.addLine(minimum, minimum, comfort + 1, result.maxComfort-300)

			else:
				# Checks to make sure that the function will be concave
				minimum = min(maximum, minimum)
				if preferred > maximum:
					preferred = maximum
				if minimum > preferred:
					preferred = minimum

				#now construct the bid:
				result.addLine(maximum, preferred, result.minComfort+300, 0)
				result.addLine(preferred, minimum, 0, result.maxComfort-300)

			#curtailment zone:
			if minimum >= self.devData['chargingPowers'][0]:
				result.addLine(minimum, self.devData['chargingPowers'][0], result.maxComfort+1, result.maxPrice)

		return result;

	def logStats(self, time):
		VfBtsCtrl.logStats(self, time)
		BtsAuctionCtrl.logStats(self, time)
