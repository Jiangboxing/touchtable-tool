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

from ctrl.auction.demandFunction import DemandFunction
from ctrl.auction.devAuctionCtrl import DevAuctionCtrl

class BtsAuctionCtrl(DevAuctionCtrl):
	def __init__(self, name, dev, parent, host):
		DevAuctionCtrl.__init__(self,  name, dev, parent, host)

		self.devtype = "BufferTimeshiftableController"

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

			#Checks to make sure that the function will be concave
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
