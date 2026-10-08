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

class BufConvAuctionCtrl(DevAuctionCtrl):
	def __init__(self, name, dev, parent, host):
		DevAuctionCtrl.__init__(self,  name, dev, parent, host)

		self.devtype = "BufferConverterController"

	def createDemandFunction(self):
		# Synchronize the device state:
		deviceState = self.updateDeviceProperties()

		result = DemandFunction()
		assert(self.devData['discrete'] == False) # Discrete options not supported currently

		#Not so clever bid: Just put the current measured consumption at 0 and possible min and max on both ends

		#determine the bounds and preferred
		#Note that we use the current consumption for the outflow!
		if self.commodities[0] in self.devData['consumption']:
			consumption = self.devData['consumption'][self.commodities[0]].real * self.devData['scaling'] #self.devData['readValue(self.host.time())
		else:
			consumption = 0.0

		maximum = min( ( (self.devData['capacity'] - self.devData['soc']) * (3600.0/self.host.timeBase) + consumption) / self.devData['cop'], self.devData['chargingPowers'][-1])
		minimum = 0.0
		if self.devData['soc']*(3600.0/self.host.timeBase) < consumption:
			minimum = (consumption/self.devData['cop']) - (self.devData['soc']*(3600.0/self.host.timeBase)/self.devData['cop'])
		if minimum >= maximum:
			#We cannot make the heatdemand
			minimum = maximum
		preferred = min(maximum, max(minimum, consumption/self.devData['cop']))

		#checks:
		assert(maximum >= minimum)
		assert(maximum >= preferred)
		assert(minimum <= preferred)

		result.addLine(maximum, preferred, result.minComfort, 0)
		result.addLine(preferred, minimum, 0, result.maxComfort)

		#curtailment and "burning"
		if minimum >= self.devData['chargingPowers'][0]:
			result.addLine(minimum, self.devData['chargingPowers'][0], result.maxComfort+1, result.maxPrice)
		if maximum <= self.devData['chargingPowers'][-1]:
			result.addLine(self.devData['chargingPowers'][-1], maximum, result.minPrice, result.minComfort-1)

		return result;
