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

# Profile steering data structure

class PSData():
	def __init__(self, other = None):
		self.source = None
		self.msg = "steering" #or "profile" when going up?
		
		self.commodities = ['ELECTRICITY']
# 		self.commodities = ['EL1', 'EL2', 'EL3'] #, 'HEAT', 'COLD', 'GAS']
		
		self.desired = {'ELECTRICITY': []}
# 		self.desired = {'EL1': [],\
# 						'EL2': [],\
# 						'EL3': []}
# 						,\
# 						'HEAT': [],\
# 						'COLD': [],\
# 						'GAS': [] }
		
		self.profile = {'ELECTRICITY': []}
# 		self.profile = {'EL1': [],\
# 						'EL2': [],\
# 						'EL3': []}
# 						,\
# 						'HEAT': [],\
# 						'COLD': [],\
# 						'GAS': [] }
		
		self.weights = {'ELECTRICITY': 1}
# 		self.weights = {'EL1': (1/3),\
# 						'EL2': (1/3),\
# 						'EL3': (1/3)}
# 						,\
# 						'HEAT': 0.25,\
# 						'COLD': 0.25,\
# 						'GAS': 0.25}

		self.prices = {'ELECTRICITY': []}
# 		self.prices = {'EL1': [],\
# 						'EL2': [],\
# 						'EL3': []}
# 						,\
# 						'HEAT': [],\
# 						'COLD': [],\
# 						'GAS': [] }

		# FIXME: Confusing
		self.profileWeight = 1 # Beta in the work by Thijs van der Klauw, 1 meaning prices have NO weights

		self.allowDiscomfort = False 	# Flag to indicate that device controllers should consider load shedding

		#accounting
		self.time = 0
		self.timeBase = 900
		
		self.planHorizon = 192
		self.planInterval = 96

		self.improvement = 0

		self.upperLimits = {}
		self.lowerLimits = {}

		# The timestamp is the original time at which the first message was sent
		# Used to invalidate real-time control messages if a new planning is made inbetween
		self.originalTimestamp = -1

		# ADMM Additions,
		# FIXME a separate steeringData class should be created, inherited by both PSData and ADMMData classes (and possibly more in the future)
		self.rho = 0.5
		self.averageProfile = {'ELECTRICITY': []}
		self.scaledLagrangian = {'ELECTRICITY': []}


		#Copy from source if other is not None
		if other != None:
			self.copy(other)
		
	def copy(self, other):
		self.commodities = list(other.commodities)
		self.desired = dict(other.desired)
		self.weights = dict(other.weights)
		self.prices = dict(other.prices)
		self.profileWeight = other.profileWeight
		self.time = other.time
		self.timeBase = other.timeBase
		self.source = other.source
		self.msg = other.msg
		self.allowDiscomfort = other.allowDiscomfort
		self.planHorizon = other.planHorizon
		self.planInterval = other.planInterval
		self.upperLimits = dict(other.upperLimits)
		self.lowerLimits = dict(other.lowerLimits)
		self.originalTimestamp = other.originalTimestamp

		# ADMM
		try:
			self.rho = other.rho
			self.averageProfile = dict(other.averageProfile)
			self.scaledLagrangian = dict(other.scaledLagrangian)
		except:
			pass
		
	def copyFrom(self, obj):
		self.commodities = list(obj.commodities)
		self.weights = dict(obj.weights)
		self.profileWeight = obj.profileWeight
		self.time = obj.host.time()
		self.timeBase = obj.timeBase
		self.source = obj.name
		self.planHorizon = obj.planHorizon
		self.planInterval = obj.planInterval

		# ADMM
		try:
			self.rho = obj.rho
			self.averageProfile = dict(obj.averageProfile)
			self.scaledLagrangian = dict(obj.scaledLagrangian)
		except:
			pass

	def fillZeroesDesired(self, len):
		for key in self.commodities.keys():	
			self.desired[key] = [complex(0.0, 0.0)] * len

	def fillZeroesProfile(self, len):
		for key in self.commodities.keys():	
			self.profile[key] = [complex(0.0, 0.0)] * len
			
	def getRealListDesired(self, c):
		#commodity c
		if c in self.commodities and c in self.desired:
			r = []
			for val in self.desired[c]:
				r.append(val.real)
			return r
		else:
			return []
		
	def getRealListProfile(self, c):
		#commodity c
		if c in self.commodities and c in self.profile:
			r = []
			for val in self.desired[c]:
				r.append(val.real)
			return r
		else:
			return []
				