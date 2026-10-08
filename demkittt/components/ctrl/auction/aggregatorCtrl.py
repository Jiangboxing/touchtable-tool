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
from core.entity import Entity

import copy

class AggregatorCtrl(Entity):
	def __init__(self, name, parent, host, congestionPoint=None):
		Entity.__init__(self,  name,  host)

		if self.host != None:
			self.host.addController(self)

		# Params
		self.children = []

		# Establish Controller <-> groupController connection
		self.parent = parent

		self.timeBase = 900

		self.useEventControl = False

		self.updateThreshold = 0.25 #amount of change in demand functions required to trigger an update
		self.discreteBids = False

		self.currentPrice = 0
		self.currentFunction = DemandFunction() #Note: currentFunction is the function that the parent knows / uses to clear the market
		self.updatedFunction = DemandFunction() #Note: updatedFunction is the function that used to trigger an update

		self.commodities = ['ELECTRICITY'] #Note, Auction only supports one commodity

		self.congestionPoint = congestionPoint

		self.type = "controllers"
		self.devtype = "AggregatorController"

	def setClearingPrice(self, price):
		if self.congestionPoint is not None:
			if self.congestionPoint.hasUpperLimit(self.commodities[0]):
				if self.currentFunction.demandForPrice(price) > self.congestionPoint.getUpperLimit(self.commodities[0]):
					price = self.currentFunction.priceForDemand(self.congestionPoint.getUpperLimit(self.commodities[0]))
			if self.congestionPoint.hasLowerLimit(self.commodities[0]):
				if self.currentFunction.demandForPrice(price) < self.congestionPoint.getLowerLimit(self.commodities[0]):
					price = self.currentFunction.priceForDemand(self.congestionPoint.getLowerLimit(self.commodities[0]))

		# Round if we have discrete bids:
		if self.discreteBids:
			price = int(round(price))

		self.currentPrice = price

		self.zCall(self.children, 'setClearingPrice', price)

	def requestDemandFunction(self):
		# Function to request demand functions from the children
		self.currentFunction.clear()

		results = self.zCall(self.children, 'requestDemandFunction')
		for r in results.values():
			self.currentFunction.addFunction(r)

		# Create function to send upwards in the tree
		self.updatedFunction = copy.deepcopy(self.currentFunction)

		if self.congestionPoint is not None:
			# If we have a congestion point, we need to alter the function we send upwards
			# However, advanced versions of the auction use the difference in current and updated functions to decide whether or not to propagate changes
			# Hence we make a copy which we can alter
			limitedFunction = copy.deepcopy(self.currentFunction)

			if self.congestionPoint.hasUpperLimit(self.commodities[0]):
				if limitedFunction.demandForPrice(limitedFunction.minPrice) > self.congestionPoint.getUpperLimit(self.commodities[0]):
					upperPowerLimit = self.congestionPoint.getUpperLimit(self.commodities[0])
					limitedFunction.priceForDemand(upperPowerLimit)
					limitedFunction.addLine(upperPowerLimit, upperPowerLimit, limitedFunction.minPrice, limitedFunction.priceForDemand(upperPowerLimit))
			if self.congestionPoint.hasLowerLimit(self.commodities[0]):
				if limitedFunction.demandForPrice(limitedFunction.maxPrice) < self.congestionPoint.getLowerLimit(self.commodities[0]):
					lowerPowerLimit = self.congestionPoint.getLowerLimit(self.commodities[0])
					limitedFunction.priceForDemand(lowerPowerLimit)
					limitedFunction.addLine(lowerPowerLimit, lowerPowerLimit, limitedFunction.priceForDemand(lowerPowerLimit), limitedFunction.maxPrice)

			return limitedFunction
		else:
			return self.updatedFunction

	def updateDemandFunction(self, oldFunction, newFunction):
		# called by children upon a demand function update
		# update the update function:
		self.updatedFunction.subtractFunction(oldFunction)
		self.updatedFunction.addFunction(newFunction)

		# Now determine that the change and see if we pass the threshold:
		if self.currentFunction.difference(self.updatedFunction) > self.updateThreshold:
			#Propagate the changes:
			self.zCall(self.parent, 'updateDemandFunction', self.currentFunction, self.updatedFunction)

	def preTick(self, time):
		pass

	def timeTick(self,  time):
		pass

	def postTick(self, time):
		pass

	def logStats(self, time):
		self.logValue("n-price.clearing",  self.currentPrice)
		self.logValue("W-power.clearing",  self.currentFunction.demandForPrice(self.currentPrice))

	def startup(self):
		# Establish Controller <-> groupController connection
		if self.parent is not None:
			if not isinstance(self.parent, str):
				self.parent.appendChild(self)
			else:
				self.zCall(self.parent, 'appendChild', self.name)

		# Auctioneer has to send the request for a function update
		assert(len(self.commodities) == 1) #Only support for single commodity control with Auctions!
		Entity.startup(self)

	def shutdown(self):
		pass

	def logValue(self, measurement,  value):
#         tags = {'ctrltype':self.devtype,  'name':self.name}
#         values = {measurement:value}
#         self.host.logValue(self.type,  tags,  values)
		data = self.type+",ctrltype="+self.devtype+",name="+self.name+" "+measurement+"="+str(value)
		self.host.logValuePrepared(data)

	def appendChild(self, child):
		self.children.append(child)