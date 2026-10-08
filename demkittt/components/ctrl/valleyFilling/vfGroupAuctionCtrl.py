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


from ctrl.valleyFilling.vfGroupCtrl import VfGroupCtrl
from ctrl.auction.aggregatorCtrl import AggregatorCtrl
from ctrl.auction.demandFunction import DemandFunction

class VfGroupAuctionCtrl(VfGroupCtrl, AggregatorCtrl):
	def __init__(self, name, host, parent=None, congestionPoint=None):
		AggregatorCtrl.__init__(self, name, None, None)
		VfGroupCtrl.__init__(self, name, host, parent, congestionPoint)

		self.useEventControl = False
		self.discreteBids = True

		self.devtype = "vfGroupAuctionController"

		#params
		self.auctionTimeBase = 900
		self.nextAuction = 0			 #Timer for the next auction
		self.nextFunctionUpdate = 0	 	 #Timer for the next complete function update
		self.auctionInterval = 1		 #max discrete time intervals between auctions
		self.functionUpdateInterval = 1 #max discrete time intervals between full function updates

		self.commodities = ['ELECTRICITY']

	def preTick(self, time):
		VfGroupCtrl.preTick(self, time)

		if self.parent == None:
			if time >= self.nextFunctionUpdate:
				self.requestDemandFunction()
				self.nextAuction = time  # Make sure that a new auction is triggered after the prices are updated.
				self.nextFunctionUpdate = self.host.time() + self.functionUpdateInterval * self.auctionTimeBase

			if time >= self.nextAuction:
				self.clearMarket()

	# two types of events: Timeticks and events	(the latter not being implemented currently)
	def timeTick(self, time):
		VfGroupCtrl.timeTick(self, time)

	def logStats(self, time):
		VfGroupCtrl.logStats(self, time)
		AggregatorCtrl.logStats(self, time)

	# Start and end-functions for system/sim startup and shutdown
	def startup(self):
		VfGroupCtrl.startup(self)

		assert(len(self.commodities) == 1)# Support for single commodity with auctions only

	def shutdown(self):
		pass

	def clearMarket(self):
		# Create a new function with the virtual generator  based on the planned power:
		t = self.host.time() - (self.host.time() % self.timeBase)
		clearingFunction = DemandFunction(self.currentFunction.minPrice, self.currentFunction.maxPrice)

		c = self.commodities[0]

		if self.useEventControl:
			#Updated plans through eventbased, try to follow the realized profile instead:
			target = self.realized[c][t].real
		else:
			#No event based control, so we need to use the plan
			#target = self.plan[c][t].real
			target = self.fillLevel

		if target >= 0:
			self.maxGeneration = -1.0*target
			self.minGeneration = -1.0*target
		else:
			self.maxGeneration = -1.0*target
			self.minGeneration = -1.0*target
		clearingFunction.addLine(self.maxGeneration, self.minGeneration, self.currentFunction.minPrice, self.currentFunction.maxPrice)

		# add the current active bid function:
		clearingFunction.addFunction(self.currentFunction)

		#And now clear the market at 0:
		price = clearingFunction.priceForDemand(0.0)
		self.setClearingPrice(price)

		#Set a next clearing timer:
		self.nextAuction = self.host.time() + self.auctionInterval*self.auctionTimeBase

	def updateDemandFunction(self, oldFunction, newFunction):
		# FIXME: Again, should use super function instead
		# called by children upon a demand function update
		# update the update function:

		# For now, update the demand function anyways in the whole cluster\
		if self.parent == None:
			self.requestDemandFunction()
			self.nextFunctionUpdate = self.host.time() + self.functionUpdateInterval * self.auctionTimeBase
			self.clearMarket()  # We might as well clear the market now that we have new bids
		else:
			# called by children upon a demand function update
			# update the update function:
			self.updatedFunction.subtractFunction(oldFunction)
			self.updatedFunction.addFunction(newFunction)

			# Now determine that the change and see if we pass the threshold:
			if self.currentFunction.difference(self.updatedFunction) > self.updateThreshold:
				# Propagate the changes:
				self.zCall(self.parent, 'updateDemandFunction', self.currentFunction, self.updatedFunction)

