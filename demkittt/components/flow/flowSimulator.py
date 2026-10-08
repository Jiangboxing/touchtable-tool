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


from flow.flowEntity import FlowEntity

class FlowSimulator(FlowEntity):
	def __init__(self,  name,  host):
		FlowEntity.__init__(self, name, host)
		
		self.devtype = "flowsim"
		
		self.rootNode = None
		self.nodes = []
		self.edges = []

		self.host.addFlow(self)

	def simulate(self, time):
		pass
		
	def startup(self):
		self.reset()
		
	def shutdown(self):
		pass	
	
	def reset(self, restoreGrid = True):
		self.resetNodes(restoreGrid)
		self.resetEdges(restoreGrid)
	
	def resetNodes(self, restoreGrid = True):
		for node in self.nodes:
			node.reset(restoreGrid)
		
	def resetEdges(self, restoreGrid = True):
		for edge in self.edges:
			edge.reset(restoreGrid)
		
	def logStats(self, time):
		#all nodes:
		for node in self.nodes:
			node.logStats(time)
		
		#all edges:
		for edge in self.edges:
			edge.logStats(time)
			
	def callOnTree(self, func, *args):
		assert(self.rootNode != None)
		
		#prepare data collection
		d = {}
		d['edges'] = []
		d['nodes'] = []
		
		#call function on the rootnode
		if hasattr(self.rootNode, func):
			r = getattr(self.rootNode, func)(*args)
			d['nodes'].append(r)
		
		# Start the recursive calls
		self.callOnSection(self.rootNode, None, d, func, *args)
		
		#and return results
		return d

	
	def callOnSection(self, thisNode, prevNode, d, func, *args):
		for edge in thisNode.edges:
			nextNode = edge.otherNode(thisNode)             
			if nextNode != prevNode and edge.enabled == True:
				# Check if this edge has the function we are looking for
				if hasattr(edge, func):
					r = getattr(edge, func)(*args)
					d['edges'].append(r)

				# Check if this node has the function we are looking for
				if hasattr(nextNode, func):
					r = getattr(nextNode, func)(*args)
					d['nodes'].append(r)
		
				# Recursive call
				self.callOnSection(nextNode, thisNode, d, func, *args)