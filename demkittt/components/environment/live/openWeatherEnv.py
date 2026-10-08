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


from environment.weatherEnv import WeatherEnv

import requests
import threading

from util.influxdbReader import InfluxDBReader

class OpenWeatherEnv(WeatherEnv):
	def __init__(self,  name,  host):
		WeatherEnv.__init__(self,  name, host)

		self.timeBase = 60

		# Openweathermap API key needs to be provided
		self.apiKey = ""

		# by default take the system location
		self.latitude = host.latitude
		self.longitude = host.longitude

		self.lastUpdate = -1
		self.updateInterval = 900 # They won't update any faster

		self.lastPrediction = -1
		self.predictionCache = None

		self.supportsForecast = True
		# Sample url= http://api.openweathermap.org/data/2.5/weather?lat=52.2215372&lon=6.8936619&units=metric&APPID=825c585b3d9169bce8e3e0f3fee352ce

		self.reader = None

		# Mapping of variables to names in InfluxDB. Should become the standard for new classes to access data from InfluxDB easily
		self.varMapping = {
			"temperature": "C-temperature",
			"humidity": "p-humidity",
			"pressure": "hPa-pressure",
			"windspeed": "mps-wind.speed",
			"winddirection": "deg-wind.direction"
		}

	def startup(self):
		self.initializeReaders()

		# Initialize the values
		self.preTick(self.host.time())

		if self.host != None:
			self.host.addEnv(self)

	def preTick(self, time):
		self.runInThread('retrieveData') #self.retrieveData()


#### HELPER FUNCTIONS
	# FIXME, make async
	def retrieveData(self):
		# We should not be a bad citizen to the service
		self.lockState.acquire()
		if (self.host.time() - self.lastUpdate)  > self.updateInterval:
			try:
				url = "http://api.openweathermap.org/data/2.5/weather?lat="+str(self.latitude)+"&lon="+str(self.longitude)+"&units=metric&APPID="+self.apiKey
				r = requests.get(url)
				if r.status_code != 200:
					self.logWarning("Could not connect to OpenWeatherMap. Errorcode: "+str(r.status_code)+ "\t\t" + r.text)
					return

				data = r.json()
				self.temperature = data['main']['temp']
				self.humidity = data['main']['humidity']
				self.pressure = data['main']['pressure']
				self.windspeed = data['wind']['speed']
				if 'deg' in data['wind']:
					self.winddirection = data['wind']['deg']

				# If all succeeded:
				self.lastUpdate = self.host.time()
			except:
				self.logWarning("OpenWeatherMap service error")
		self.lockState.release()

	# FIXME make async
	def retrieveForecast(self):
		self.lockState.acquire()
		if self.lastPrediction < self.host.time():
			try:
				url = "http://api.openweathermap.org/data/2.5/forecast?lat="+str(self.latitude)+"&lon="+str(self.longitude)+"&units=metric&APPID="+self.apiKey
				r = requests.get(url)
				if r.status_code != 200:
					self.logWarning("Could not connect to OpenWeatherMap. Errorcode: "+str(r.status_code)+ "\t\t" + r.text)
					return

				self.predictionCache = r.json()

				# If all succeeded:
				self.lastUpdate = self.host.time()
			except:
				self.logWarning("OpenWeatherMap service error")

		self.lockState.release()
		return dict(self.predictionCache)

	def doPrediction(self, startTime, endTime, timeBase=None):
		if timeBase is None:
			timeBase = self.timeBase

		result = []
		data = self.retrieveForecast()

		time = startTime
		while time < endTime:
			# Retrieve the correct value:
			for element in data['list']:
				if element['dt'] <= time and element['dt']+10800 > time: # 10800 seconds = 3 hours, the interval length of openweathermap
					d = {}
					d['temperature'] = element['main']['temp']
					d['humidity'] = element['main']['humidity']
					d['pressure'] = element['main']['pressure']
					d['windspeed'] = element['wind']['speed']
					if 'deg' in element['wind']:
						d['winddirection'] = element['wind']['deg']
					else:
						d['winddirection'] = 0
					d['time'] = element['dt']

					result.append(dict(d))
					break

			time += timeBase
		return result

	def doTemperaturePrediction(self, startTime, endTime = None, timeBase = 60, perfect = False):
		# FIXME IMPLEMENT

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

	def initializeReaders(self):
		# FIXME REMOVE HARDCODED DETAILS USED IN TESTING
		self.reader = InfluxDBReader(self.type, address="130.89.15.70", port=6086, database="demkitlive",
											   timeBase=self.timeBase, tags={"name": self.name}, value=self.varMapping["temperature"])

	def readValue(self, time, filename=None, timeBase=None, field=None):
		if field != None:
			filename = field

		r = self.reader.readValue(time, filename, timeBase)
		return r

	def readValues(self, startTime, endTime, filename="temperature", timeBase=None, field=None):
		if field != None:
			filename = field

		result = self.reader.readValues(startTime, endTime, self.varMapping[filename], timeBase)
		return result