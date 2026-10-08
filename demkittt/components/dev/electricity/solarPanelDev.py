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


from dev.curtDev import CurtDev

class SolarPanelDev(CurtDev):
	def __init__(self,  name,  host, sun):
		CurtDev.__init__(self,  name,  host)

		self.devtype = "Curtailable"
		self.sun = sun

		# params
		self.size = 1.6*12					# Solar panel array in m2
		self.efficiency = 20				# Conversion efficiency in %

		# orientation
		self.inclination = 35 				# Elevation in degrees from horiontal plane on earth surface
		self.azimuth = 180					# Orientation in degrees, 0 = north, 90 = east, 180 = south

		# new style parameters based on the Wp specification of a panel, its size and number of panels
		self.wattPeak = None				# WP given in Watt per panel at 1000W/m2 irradiation
		self.panels = None					# Number of panels
		self.panelSize = 1.65				# Panel size in m2
		self.inverterEfficiency = 0.811 	# Panel efficiency != system efficiency after DC/AC conversion
											# Source: https://www.mdpi.com/201184

	def startup(self):
		CurtDev.startup(self)

		# Initialize default values, we intend to support both the classic (efficiency based) method and wattpeak method
		# Note that the behaviour is due to change for DEMKit v4.x
		if self.wattPeak is not None:
			self.efficiency = ( (self.wattPeak / self.panelSize) / 1000.0) * self.inverterEfficiency * 100

		if self.panels is not None:
			self.size = self.panels * self.panelSize

	def preTick(self, time):
		self.lockState.acquire()
		if self.wattPeak is not None:
			self.efficiency = ( (self.wattPeak / self.panelSize) / 1000.0) * self.inverterEfficiency * 100

		if self.panels is not None:
			self.size = self.panels * self.panelSize

		for c in self.commodities:
			self.consumption[c] = self.calculateProduction()

		self.originalConsumption = dict(self.consumption)
		self.lockState.release()


#### INTERFACING
	def getProperties(self):
		r = CurtDev.getProperties(self) 	# Get the properties of the overall Device class, which already includes global properties

		self.lockState.acquire()
		# Populate the result dict
		r['size'] = self.size
		r['efficiency'] = self.efficiency
		r['inclination'] = self.inclination
		r['azimuth'] = self.azimuth
		r['onOffDevice'] = self.onOffDevice
		r['originalConsumption'] = self.originalConsumption
		if self.wattPeak is not None:
			r['wattPeak'] = self.wattPeak
		if self.panels is not None:
			r['panels']= self.panels
		self.lockState.release()

		return r

# HELPERS
	def calculateProduction(self, time = None):
		# Do something with the irradiation here
		if time is None:
			production = self.sun.powerOnPlane(self.inclination, self.azimuth)
		else:
			production = self.sun.powerOnPlane(self.inclination, self.azimuth, time)

		return -1 * production * (self.efficiency/100.0) * self.size

	def readValue(self, time, filename=None, timeBase=None):
		return self.calculateProduction(time)

	def readValues(self, startTime, endTime, filename=None, timeBase=None):
		if timeBase is None:
			timeBase = self.timeBase

		# Function used for predictions
		result = []
		time = startTime
		while time < endTime:
			result.append(self.calculateProduction(time))
			time += timeBase

		return result
