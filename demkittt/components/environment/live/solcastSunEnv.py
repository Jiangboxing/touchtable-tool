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


from environment.sunEnv import SunEnv
import pytz
import requests
from util.influxdbReader import InfluxDBReader

from datetime import datetime
import dateutil.parser

class SolcastSunEnv(SunEnv):
	def __init__(self,  name,  host, reader=None):
		SunEnv.__init__(self,  name, host)

		self.timeBase = 60

		self.apiKey = ""

		# by default take the system location
		self.latitude = host.latitude
		self.longitude = host.longitude

		self.lastUpdate = -1
		self.updateInterval = 900  # To get all the updates
		self.dataCache = None # Storage, also for predictions

		self.supportsForecast = True

		self.reader = reader

		# Mapping of variables to names in InfluxDB. Should become the standard for new classes to access data from InfluxDB easily
		self.varMapping = {
			"elevation": "deg-elevation",
			"azimuth": "deg-azimuth",
			"zenith": "deg-zenith",
			"irradiationGHI": "Wm2-irradiation.GHI",
			"irradiationDHI": "Wm2-irradiation.DHI",
			"irradiationDNI": "Wm2-irradiation.DNI"
		}

		# May this service become paid, then this may be an alternative:
		# https://pvlib-python.readthedocs.io/en/latest/forecasts.html

	def preTick(self, time):
		result = dict(self.getIrradiation(time))

		# Now unpack the dict:
		self.elevation = result['elevation']
		self.azimuth = result['azimuth']
		self.zenith = result['zenith']

		self.irradiationGHI = result['GHI']
		self.irradiationDHI = result['DHI']
		self.irradiationDNI = result['DNI']

		# Update the current state
		self.currentState = dict(result)

	def getIrradiation(self, time):
		return dict(self.radiationSolcast(time))


	# These radiation functions calculate the radiation values for a specific time
	# FIXME make async
	def radiationSolcast(self, time):
		result = {}

		# FIXME Static data from calculations, should be moved out here
		d = datetime.fromtimestamp(time, tz=pytz.utc)
		result['elevation'] = self.location.solar_elevation(d)
		result['azimuth'] = self.location.solar_azimuth(d)
		result['zenith'] = self.location.solar_zenith(d)

		result['GHI'] = self.irradiationGHI
		result['DHI'] = self.irradiationDHI
		result['DNI'] = self.irradiationDNI

		# Retrieve data from Solcast
		if (self.host.time() - self.lastUpdate) > self.updateInterval:
			self.retrieveData()

		data = self.dataCache

		for entry in data['forecasts']:
			t1 = int(dateutil.parser.parse(entry['period_end']).timestamp())-(30*60)
			t2 = int(dateutil.parser.parse(entry['period_end']).timestamp())

			if t1 <= time and t2 >= time:
				result['GHI'] = entry['ghi']
				result['DNI'] = entry['dni']
				result['DHI'] = entry['dhi']
				result['time'] = t1
				return dict(result)

		return dict(result)


	def startup(self):
		self.initializeReaders()

		# Setup the astral location
		self.location.latitude = self.latitude
		self.location.longitude = self.longitude
		self.location.timezone = self.timezone
		self.location.elevation = self.height

		# Initialize the values
		self.preTick(self.host.time())

		if self.host != None:
			self.host.addEnv(self)

	def retrieveData(self):
		# We should not be a bad citizen to the service
		try:
			url = "https://api.solcast.com.au/radiation/forecasts?longitude=" + \
			      str(self.longitude) + "&latitude=" + str(self.latitude) + "&api_key="+ self.apiKey +"&format=json"
			r = requests.get(url)

			if r.status_code != 200:
				self.logWarning(
					"Could not connect to Solcast. Errorcode: " + str(r.status_code) + "\t\t" + r.text)
				return self.dataCache

			self.dataCache = r.json()

			# If all succeeded:
			self.lastUpdate = self.host.time()
		except:
			self.logWarning("Solcast service error")

		return self.dataCache

	def doPrediction(self, startTime, endTime, timeBase = None):
		if timeBase is None:
			timeBase = self.timeBase
		result = []

		# We can simply use the original function, just loop through all desired time intervals :)
		# For now we do not consider
		time = startTime
		while time < endTime:
			result.append(self.radiationSolcast(time))
			time += timeBase

		return result
	
	def initializeReaders(self):
		if self.reader is None:
			self.reader = InfluxDBReader(self.type, timeBase=self.timeBase, host=self.host,
												   tags={"name": self.name}, value=self.varMapping["elevation"])

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




