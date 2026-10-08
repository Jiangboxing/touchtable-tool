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

class BufAuctionCtrl(DevAuctionCtrl):
	def __init__(self, name, dev, parent, host):
		DevAuctionCtrl.__init__(self,  name, dev, parent, host)

		self.devtype = "BufferController"

	def createDemandFunction(self):
		# Synchronize the device state:
		deviceState = self.updateDeviceProperties()

		result = DemandFunction()
		assert(self.devData['discrete'] == False) # Discrete device options not supported currently

		maximum = min( (self.devData['capacity'] - self.devData['soc'])*(3600.0/self.timeBase) , self.devData['chargingPowers'][-1])
		minimum = max( -self.devData['soc']*(3600.0/self.timeBase), self.devData['chargingPowers'][0])

		assert(maximum >= minimum)
		assert(maximum >= 0)
		assert(minimum <= 0)

		realSoC = self.devData['soc'] / self.devData['capacity'] #Fraction of the fill level

		result.addLine(maximum, 0.0, result.minComfort, (result.minComfort + 100 + (1-realSoC)*400))
		result.addLine(0.0, minimum, (result.maxComfort - realSoC*400 - 100), result.maxComfort)

		return result
