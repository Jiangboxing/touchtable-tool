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


from environment.envEntity import EnvEntity
from util.csvReader import CsvReader

import util.helpers
import pytz

import numpy as np #D.

import math
from datetime import datetime


class WindEnv(EnvEntity):
	def __init__(self,  name,  host):
		EnvEntity.__init__(self,  name, host)

		self.devtype = "Wind"

		self.timezone = 'Europe/Amsterdam' # This is not a pytz object for Astral!

		# Time settings
		self.stdTime = 0 # KNMI data is given for UT (Universal Time), so the longitude is 0.
		self.useInterpolation = True

		#D. wind turbine parameters
		self.windSpeed = 0.0
		self.windSpeedScaleFactor = 0.975
		self.windSpeedHubHeight = 0.0

		self.windSpeedFile = None
		self.windSpeedTimeBase = 3600
		self.windSpeedColumn = -1
		self.windSpeedReader = None


		self.currentState = {}
		self.timeBase = 3600 # Default of most weather information sources
		self.timeOffset = -3600
		if host != None:
			self.timeOffset = host.timeOffset -3600 # KNMI data is in UTC, so we need to subtract one hour in the dataset

		self.reader = None

		#D. Question: what this used for?
		# Mapping of variables to names in InfluxDB. Should become the standard for new classes to access data from InfluxDB easily
		# self.varMapping = {
		# 	"elevation": "deg-elevation",
		# 	"azimuth": "deg-azimuth",
		# 	"zenith": "deg-zenith",
		# 	"irradiationGHI": "Wm2-irradiation.GHI",
		# 	"irradiationDHI": "Wm2-irradiation.DHI",
		# 	"irradiationDNI": "Wm2-irradiation.DNI"
		# }

	def preTick(self, time):
		self.lockState.acquire()

		#D. parameter for wind turbine
		result = dict(self.getWindSpeed(time))
		self.windSpeed = result['windSpeed']

		# Update the current state
		self.currentState = dict(result)
		self.lockState.release()


	def getWindSpeed(self, time):
		#D. getWindSpeed can be changed to getWindProps if more parameters need to be obtained/read from file
		result = {}
		if self.useInterpolation:
			result = dict(self.windSpeedInterpolation(time))
		else:
			result = dict(self.windSpeedSimple(time))
		return result

	# These windSpeed(simple/Interpolation) functions calculate the radiation values for a specific time
	def windSpeedSimple(self, time):
		# Noninterpolated variant
		# Hourly averages do not give appropriate results, so we pick a static time based on the timebase to calculate all values
		# Since the middle of a time interval gives the best representation, this value is used
		result = {}
		modeltime = int(time - (time % self.timeBase) + (self.timeBase / 2))

		d = datetime.fromtimestamp(time, tz=pytz.utc)

		# D. other parameters can be obtained with results list in the future
		result['windSpeed'] = self.windSpeedReader.readValue(modeltime)

		return result

	def windSpeedInterpolation(self, time):
		result = {}

		t1 = (time - (time%self.timeBase)) - int(self.timeBase/2)
		t2 = (time - (time%self.timeBase)) + int(self.timeBase/2)
		if (time % self.timeBase) >= int(self.timeBase/2):
			t1 += self.timeBase
			t2 += self.timeBase

		assert(t1 <= time <= t2)

		result['windSpeed'] = util.helpers.interpolatePoint(self.windSpeedReader.readValue(t1),self.windSpeedReader.readValue(t2), t1, t2, time)

		return result

	def startup(self):
		self.lockState.acquire()

		#D. #initialize the reader
		if self.windSpeedReader == None:
			self.windSpeedReader = CsvReader(self.windSpeedFile, self.windSpeedTimeBase, self.windSpeedColumn, self.timeOffset)

		self.lockState.release()

		# Initialize the values
		self.preTick(self.host.time())

		EnvEntity.startup(self)

	def timeTick(self,  time):	
		pass
	
	def postTick(self, time):
		pass
	
	def logStats(self, time):
		self.lockState.acquire()

		self.logValue("m/s-windSpeed", self.windSpeed)
		self.logValue('m/s-windSpeedHubHeight', self.windSpeedHubHeight)

		self.lockState.release()

	def shutdown(self):
		pass	

	def getProperties(self):
		# Get the properties of this device
		r = {}
		r = EnvEntity.getProperties(self)

		return r

##### LOCAL HELPER FUNCTIONS
	def windTurbineYield(self, dataSourceHeight, hubHeight, cutInSpeed, cutOutSpeed, roughnesslength, powerCurveWindSpeeds, powerCurveValues, time=None):

		#D. two way to calculate wind turbine generation, here 2nd method is used.
		# 1st method: use power coefficient: P = 1/8 * airDensity * d2 * PI * V3 * Cp
		# 2st method: know wind speed at hub height and power curve, just corresponds the power value

		# Obtain the current values
		if time is None:
			windProps = self.currentState #D.
		else:
			windProps = self.getWindSpeed(time) #D.

		#D. modify wind speed from 10m to hub height
		assert(hubHeight > 0)
		if hubHeight == dataSourceHeight:
			self.windSpeedHubHeight = windProps['windSpeed'] * self.windSpeedScaleFactor
		else:
			self.windSpeedHubHeight = windProps['windSpeed'] * self.windSpeedScaleFactor * math.log10(hubHeight/roughnesslength)/math.log10(10/roughnesslength)

		#D. limits for wind turbines: cut-in & cut-out speed
		if self.windSpeedHubHeight < cutInSpeed or self.windSpeedHubHeight > cutOutSpeed:
			return 0.0

		#D. Source: windpowerlib library
		windTurbineYield = np.interp(self.windSpeedHubHeight, powerCurveWindSpeeds,powerCurveValues, left=0,right=0)

		return max(0.0, windTurbineYield)


	def readValue(self, time, filename=None, timeBase=None, field=None):
		if field != None:
			filename = field

		r = self.reader.readValue(time, filename, timeBase)
		return r

	def readValues(self, startTime, endTime, filename="elevation", timeBase=None, field=None):
		if field != None:
			filename = field

		result = self.reader.readValues(startTime, endTime, self.varMapping[filename], timeBase)

		return result

	def doPrediction(self, startTime, endTime, timeBase = None):
		if timeBase is None:
			timeBase = self.timeBase
		result = []

		# We can simply use the original function, just loop through all desired time intervals :)
		# For now we do not consider
		time = startTime
		while time < endTime:
			result.append(self.getWindSpeed(time)) #D.
			time += timeBase

		return result