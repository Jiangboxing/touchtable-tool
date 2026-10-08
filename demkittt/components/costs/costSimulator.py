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


from costs.costEntity import CostEntity

class CostSimulator(CostEntity):
	def __init__(self,  name,  host):
		CostEntity.__init__(self, name, host)
		
		self.devtype = "costsim" 
		
		self.host = host

		#register this device at the host
		self.host.addCost(self)
		self.meterToHouse = False
		self.rootNode = None

	def timeTick(self,  time):	
		pass
	
	def simulate(self, time):
		pass
		
	def startup(self):
		self.reset()
		
	def shutdown(self):
		pass	

	def refreshCustomers(self):
		if self.meterToHouse:
			self.customers = self.allMeters(self.rootNode)
		else:
			self.customers = self.allLeafs(self.rootNode)

	def addNetwork(self, root):
		self.rootNode = root
		self.refreshCustomers()

	# Total losses for phases L1, L2 and L3
	def totalLosses(self, node, prevnode=None):
		if node == None or (len(node.edges) == 1 and prevnode!=None):
			return 0		 # When there are no edges below `node'
		childs = [e for e in node.edges if prevnode == None or e.otherNode(node).name != prevnode.name] # Child nodes below `node'
		directlosses = sum([e.getLosses()-e.getLossesPhase(0) for e in childs]) # Losses of phases L1,L2,L3 of cables below `node'

		# losses of cable to `node'  +  losses of cables below `node'
		return directlosses + sum([ self.totalLosses(e.otherNode(node), node) for e in childs] )

	# Find all leaf nodes in the network and return them in a list
	def allLeafs(self, node, prevnode=None):
		if node == None or (len(node.edges) == 1 and prevnode!=None):
			return [node]		      # When there are no edges below `node'
		childNodes = [e.otherNode(node) for e in node.edges if prevnode == None or e.otherNode(node).name != prevnode.name] # Child nodes below `node'
		return sum([ self.allLeafs(c, node) for c in childNodes ], [])

	# Find all meters in the network and return them in a list
	def allMeters(self, node, prevnode=None):
		if node == None:
			return
		meters = node.metersL1 + node.metersL2 + node.metersL3
		if (len(node.edges) == 1 and prevnode!=None):
			return meters		      # When there are no edges below `node'
		childNodes = [e.otherNode(node) for e in node.edges if prevnode == None or e.otherNode(node).name != prevnode.name] # Child nodes below `node'
		return meters + sum([ self.allMeters(c, node) for c in childNodes ], [])
	


