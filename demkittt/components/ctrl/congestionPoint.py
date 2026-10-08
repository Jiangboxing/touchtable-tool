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

class CongestionPoint():
	def __init__(self):
		self.commodities = []

		self.upperLimits = {}
		self.lowerLimits = {}

	def setUpperLimit(self, c, limit):
		self.upperLimits[c] = limit
		if c not in self.commodities:
			self.commodities.append(c)

	def setLowerLimit(self, c, limit):
		self.lowerLimits[c] = limit
		if c not in self.commodities:
			self.commodities.append(c)

	def hasUpperLimit(self, c):
		return c in self.upperLimits

	def hasLowerLimit(self, c):
		return c in self.lowerLimits

	def getUpperLimit(self, c):
		if c in self.upperLimits:
			return self.upperLimits[c]

	def getLowerLimit(self, c):
		if c in self.lowerLimits:
			return self.lowerLimits[c]

	# FIXME: We should implement something to check whether the constraints are met in real-time in the future.
	# FIXME 	For now we just use this class as a placeholder for input into the controller