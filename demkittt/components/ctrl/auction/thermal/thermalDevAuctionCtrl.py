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

from ctrl.auction.devAuctionCtrl import DevAuctionCtrl

import math

class ThermalDevAuctionCtrl(DevAuctionCtrl):
	def __init__(self, name, dev, parent, host):
		DevAuctionCtrl.__init__(self,  name, dev, parent, host)

	def setControlResult(self):
		result = {}

		# Get the desired consumption for the main commodity
		power = self.updatedFunction.demandForPrice(self.currentPrice)

		# Now populate the result:
		# We need to explicitly set the energy consumption for each commodity
		for c in self.dev.commodities:
			result[c] = []

			if c == self.commodities[0]:
				# This is the main commodity, directly set the result
				tup = (self.host.time(), power)
			else:
				# Translate the target into the other commodity using the CoP:
				# However, we first need to determine how much heat will be produced:

				heatPower = min(self.dev.producingPowers[-1], max(self.dev.producingPowers[0], power * self.dev.cop[self.commodities[0]] * math.copysign(1, self.heatRequest) ) )

				if c == 'HEAT':
					tup = (self.host.time(), heatPower)
					# Note that we need to consider limits of the device here as well
				else:
					tup = (self.host.time(), math.copysign( (heatPower / self.dev.cop[c]), self.dev.cop[c]) )

			result[c].append(tup)

		# Call the function to set the planning:
		self.zCall(self.dev, 'setPlan', result)
