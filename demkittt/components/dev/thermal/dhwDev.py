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

from util.csvReader import CsvReader
from util.windowPredictor import WindowPredictor
from dev.thermal.thermalDev import ThermalDevice

class DhwDev(ThermalDevice):
	def __init__(self,  name,  host):
		ThermalDevice.__init__(self,  name,  host)
		self.devtype = "Load"

		# State variables:
		self.temperature = 60.0 			# in Celsius. This variable will hold the demanded temperature

		# Model parameters:
		self.heatSupply = {}
		self.heatTemperature = {}

		# Ambient temperature file handling
		self.dhwFile = None
		self.dhwTimeBase = 60
		self.dhwColumn = -1
		self.dhwReader = None

		self.perfectPredictions = False
		self.predictor = None

		self.windows = []

	# Startup is called to initialize the model
	def startup(self):
		self.lockState.acquire()
		assert(len(self.commodities) == 1) # Only one commodity supported for this device (Preferably HEAT)

		# Initialize the heat supply variables for the initial state
		self.heatSupply[self.commodities[0]] = 0.0 # Note: HeatSupply will be set by the heat source and should therefore be considered read only
		self.heatTemperature[self.commodities[0]] = 0.0

		# Initialize the ambient reader based on the configuration input
		self.dhwReader = CsvReader(self.dhwFile, self.dhwTimeBase, self.dhwColumn, self.timeOffset)
		self.predictor = WindowPredictor(self.timeBase)

		# Make sure to initialize the initial state of the model:
		self.consumption[self.commodities[0]] = self.dhwReader.readValue(self.host.time())

		if not self.perfectPredictions:
			self.initializePredictors()

		if self.persistence != None:
			watchlist = ["temperature", "plan", "predictor", "consumption"]
			self.persistence.setWatchlist(watchlist)

		self.lockState.release()

		ThermalDevice.startup(self)

	# PreTick is called before the actual time simulation.
	# Use this to update the state based on the state selected in the previous interval
	def preTick(self, time):
		self.lockState.acquire()
		if self.host.timeBase <= self.timeBase:
			self.consumption[self.commodities[0]] = self.dhwReader.readValue(self.host.time())
		else:
			assert(self.host.timeBase % self.timeBase == 0)
			#resample the profile:
			total = 0.0
			for i in range(0, int(self.host.timeBase/self.timeBase)): #Forward looking
				total += self.dhwReader.readValue(self.host.time()+(i*self.timeBase))
			self.consumption[self.commodities[0]] = (total / (self.host.timeBase/self.timeBase) )

		self.predictor.addSample(self.consumption[self.commodities[0]], time)

		self.lockState.release()

	# TimeTick is called after all control actions
	def timeTick(self,  time):
		self.prunePlan() # there is no real plan (now?!) but it is good to throw away old data to avoid high memory usage\

	def logStats(self, time):
		self.lockState.acquire()
		for c in self.commodities:
			self.logValue("W-power.real.c." + c, self.consumption[c].real)
		self.lockState.release()

#### INTERFACING TO READ THE STATE BY A CONTROLLER
	# E.G. this is used by a thermostat device to read the current temperature and see if heating is requiree
	def getProperties(self):
		r = ThermalDevice.getProperties(self) 	# Get the properties of the overall Device class, which already includes global properties

		return r

	def initializePredictors(self):
		time = self.host.time() - (4*7*24*3600)
		while time < self.host.time():
			self.predictor.addSample(self.dhwReader.readValue(time), time)
			time += self.timeBase

	# FIXME: We should move predictions to controllers. See T215
	def doPrediction(self, startTime, endTime, timeBase = None):
		if timeBase == None:
			timeBase = self.timeBase

		result = []
		if not self.perfectPredictions:
			intervals = int((endTime - startTime) / timeBase)
			result = list(self.predictor.predictValues(startTime, intervals, timeBase))
		else:
			time = startTime
			while time < endTime:
				result.append(self.dhwReader.readValue(time))
				time += timeBase

		return result