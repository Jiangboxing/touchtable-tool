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

import random

class WeatherEnv(EnvEntity):
	def __init__(self,  name,  host):
		EnvEntity.__init__(self,  name, host)

		self.devtype = "Weather"
		self.timeBase = 3600 # Default of most weather information sources

		# NOTE: ONLY SUPPORTS TEMPERATURE AT THIS MOMENT

		#  Readable values:
		self.temperature = 0.0 # in degrees Celsius
		self.humidity = 0.0 # in %
		self.pressure = 0.0 # in hPa
		
		self.windspeed = 0.0 # in meters per second
		self.windspeedScaleFactor = 0.975
		self.windspeedHubHeight = 0.0
		self.winddirection = 0.0 # degrees
		

		self.weatherFile = None
		self.weatherTimeBase = 3600		# Seconds per interval. Default 1 hour for KNMI weather data

		# Separate readers for each weather column
		self.temperatureReaderReader = None
		self.temperatureColumn = 0

		self.windspeedReader = None
		self.windspeedColumn = 1

		self.timeOffset = -3600
		if host != None:
			self.timeOffset = host.timeOffset -3600 #KNMI data offset is in UTC

	def startup(self):
		#initialize the readers
		self.temperatureReader = CsvReader(self.weatherFile, self.weatherTimeBase, self.temperatureColumn, self.timeOffset)
		self.windspeedReader = CsvReader(self.weatherFile, self.weatherTimeBase, self.windspeedColumn, self.timeOffset)

		# Initialize the values
		self.preTick(self.host.time())

		EnvEntity.startup(self)

	def preTick(self, time):
		self.lockState.acquire()
		self.temperature = self.temperatureReader.readValue(time)
		self.windspeed = self.windspeedReader.readValue(time)
		self.lockState.release()
		# Only temperature supported for now. Additional readers make it possible to get other data in if required

	def timeTick(self,  time):
		pass

	def postTick(self, time):
		pass

	def shutdown(self):
		pass

	def logStats(self, time):
		self.lockState.acquire()
		self.logValue("C-temperature", self.temperature)
		self.logValue("hPa-pressure", self.pressure)
		self.logValue("p-humidity", self.humidity)
		self.logValue("mps-wind.speed", self.windspeed)
		self.logValue("deg-wind.direction", self.winddirection)
		self.lockState.release()

	def getProperties(self):
		# Get the properties of this device
		r = {}
		r = EnvEntity.getProperties(self)

		return r

	def doTemperaturePrediction(self, startTime, endTime = None, timeBase = 60, perfect = False):
		if endTime is None:
			temperature = self.temperatureReader.readValue(startTime)
			if perfect is False:
				temperature = temperature -0.5 + random.random() # Just some randomization. Would be nice to retrieve a prediction dataset in the future, T194
			return temperature

		else:
			result = []
			time = startTime
			while time < endTime:
				# Recursive call to itself
				result.append(self.doTemperaturePrediction(time, None, timeBase, perfect))
				time += timeBase

			return result

	def doWindPrediction(self, startTime, endTime = None, timeBase = 60, perfect = False):
		if endTime is None:
			wind = self.windspeedReader.readValue(startTime)
			if perfect is False:
				wind = wind -0.5 + random.random() # Just some randomization. Would be nice to retrieve a prediction dataset in the future, T194
			return wind

		else:
			result = []
			time = startTime
			while time < endTime:
				# Recursive call to itself
				result.append(self.doWindPrediction(time, None, timeBase, perfect))
				time += timeBase

			return result