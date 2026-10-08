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

class CostShapley(CostSimulator):
	def __init__(self,  name,  host):
		CostSimulator.__init__(self,  name, host)
		self.devtype = "shapley"
		self.allocatedLosses = dict({})
		self.allocatedLoads = dict({})

	# Network aware cost allocation for phase `l'; does not allocate the neutral conductor losses
	def costAlloc(self, node, l, prevnode=None, prevedge=None):
		actualLosses = prevedge.getLossesPhase(l) if prevedge!=None else 0
		allocload = dict({});
		alloclosses = dict({});

		if self.meterToHouse:
			# A meter becomes a customer that is billed; just register them such that they participate in cost sharing with the meter load
			for meter in (node.metersL1 + node.metersL2 + node.metersL3):
				allocload[meter.name] = meter.consumption
				alloclosses[meter.name] = 0
				# Fall through! now start using these new customers in the cost allocation below
		elif len(node.edges) == 1 and prevnode!=None:
			# When meters do not become customers: leafs become customer and loads+losses to the connecting edge are allocated to this customer
			allocload   = { node.name : prevnode.getLNVoltage(l) * prevedge.current[l] }
			alloclosses = { node.name : actualLosses }
			return (allocload, alloclosses)

		for edge in node.edges:
			nd = edge.otherNode(node)
			if (prevnode == None or prevnode.name != nd.name):
				(eallocload, ealloclosses) = self.costAlloc(nd, l, node, edge)
				allocload   =  dict(allocload,	 **eallocload)
				alloclosses =  dict(alloclosses, **ealloclosses)

		# Calculate the total load _reported_ by underlying nodes
		totalLoad = sum(allocload.values())
		losses = prevedge.getLosses() if prevedge!=None else 0
		actualLoad = prevnode.getLNVoltage(l).conjugate() * prevedge.current[l] if prevnode!=None else totalLoad # TODO: verify conjugate!! Gerwin: Yes Marco, this is correct

		for key,loss in alloclosses.items():
			# Calculate the fraction of the load incurred by a customer; see paper for the mathematical details, e.g., why using the real part is correct.
			fraction = (allocload[key] / totalLoad).real if totalLoad!=0 else 0
			alloclosses[key] = loss + actualLosses.real * fraction
			allocload[key] = allocload[key] + actualLosses * fraction
		
		return (allocload, alloclosses)

	# Network unaware cost allocation (by load ratio)
	def costAllocSimple(self, node):
		loads = {}
		# Find all customers
		if self.meterToHouse:
			customers = self.allMeters(node)
			for c in customers:
				loads[c.name] = c.consumption
			
		else:
			customers = self.allCustomers(node)
			for c in customers:
				load = 0
				for phase in range(1,4): # L1, L2 and L3
					load += c.getLNVoltage(phase).conjugate() * c.edges[0].current[phase] # TODO: verify conjugate!! Gerwin: Yes Marco, this is correct
				loads[c.name] = load

		losses = self.totalLosses(node)

		alloclosses = {}
		totalLoad = sum(loads.values())
		for name,load in loads.items():
			fraction = (load / totalLoad).real if totalLoad !=0 else 0
			alloclosses[name] = fraction * losses
		return alloclosses
		
	def simulate(self, time):
		# Calculate the network aware cost allocation for all phases and merge the costs
		allocloadPhase = []
		alloclossesPhase = []
		for phase in range(1,4):
			(allocloadPhaseL, alloclossesPhaseL) = self.costAlloc(self.rootNode, phase)
			alloclossesPhase.append(alloclossesPhaseL)
			allocloadPhase.append(allocloadPhaseL)

		# Merge phase dictionaries
		allocload = dict({})
		alloclosses = dict({})
		for key in allocloadPhase[1]:
			allocload[key] = allocloadPhase[0][key] + allocloadPhase[1][key] + allocloadPhase[2][key]
			alloclosses[key] = alloclossesPhase[0][key] + alloclossesPhase[1][key] + alloclossesPhase[2][key]
			

		# Store the results for later use
		self.allocatedLoads  = allocload
		self.allocatedLosses = alloclosses
		self.allocatedLossesSimple = self.costAllocSimple(self.rootNode)

		# Check if all the losses for L1,L2 and L3 are properly allocated to customers
		totalallocatedLosses = sum(alloclosses.values())
		totalallocatedLossesSimple = sum(self.allocatedLossesSimple.values())
		totalactualLosses = self.totalLosses(self.rootNode)
		assert (abs(totalallocatedLosses - totalactualLosses) < 0.01) # Assert that all losses are allocated (0.01W margin...)
		assert (abs(totalallocatedLossesSimple - totalactualLosses) < 0.01) # Assert that all losses are allocated (0.01W margin...)

		self.logStats(time)

	def timeTick(self, time): 
		pass

	def startup(self):
		if self.rootNode == None:
			print("No rootNode set. Please make sure you define "+self.name+".rootNode")
			assert(False)

                        
	def logStats(self, time):
		# Store in database
		for key in sorted(self.allocatedLosses.keys()):
			tags = {'customer': key}
			values = {"n-allocloss": self.allocatedLosses[key], "n-simpleallocloss" : self.allocatedLossesSimple[key]}
			self.host.logValue(self.type,  tags,  values)

