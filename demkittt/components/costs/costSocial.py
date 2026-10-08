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


from costs.costSimulator import CostSimulator

# ``Social'' cost allocation: everyone receives the same share... This also serves as example code. 
class CostSocial(CostSimulator):
	def __init__(self,  name,  host):
		CostSimulator.__init__(self,  name, host)
		self.devtype = "social"
	
	def timeTick(self, time): 
		pass

	def startup(self):
		if self.rootNode == None:
			print("No rootNode set. Please make sure you define "+self.name+".rootNode")
			assert(False)

	def simulate(self, time):
		# Allocate the losses evenly over the customers
	    losses = self.totalLosses(self.rootNode)
		share = losses / len(self.customers) # share for each customer, i.e., total losses / #customers
		self.allocatedLosses = { c.name : share for c in self.customers } # A customer is a meter or node, but since Python is a mess this works :-)

		self.logStats(time)
            
	def logStats(self, time):
		# Store in database
		for key in sorted(self.allocatedLosses.keys()):
			tags = {'customer': key}
			values = {"n-socialallocloss": self.allocatedLosses[key] }
			self.host.logValue(self.type,  tags,  values)