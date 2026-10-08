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


import copy
import threading
from ctrl.loadCtrl import LoadCtrl
from sklearn import linear_model



# FIXME: Inherit from CurtCtrl in the future
# However, for now we omit the option to perform curtailment

class LivePvCtrl(LoadCtrl):
	#Make some init function that requires the host to be provided
	def __init__(self,  name,  dev, ctrl, sun, host):
		LoadCtrl.__init__(self,  name,  dev,  ctrl,  host)

		self.sun = sun
		self.lastModelTraining = -1

		# Temporary overriding
		# self.predictionAdaption = False

		# Model parameters
		self.model = []
		self.maxProduction = [] # Holds the maximum observed production (as negative value!) for each bin
		self.binSize = 1800 # timespan of one bin in the regression model
		self.bins = None # Variable will be set automatically on startup

		self.regressionTimeBase = 60	# in seconds
		self.historySize = 21*24*3600 	# in seconds

		# NOTE: All time indexes here are in UTC!
		# For DEMKit, this works fine as everything works in UTC
		# It is just that we humans need to take care of it when debugging ;-)
		if self.persistence != None:
			watchlist = self.watchlist + ["lastModelTraining", "model", "bins", "binSize", "regressionTimeBase", "historySize"]
			self.persistence.setWatchlist(watchlist)

		self.lockModel = threading.Lock()

	def startup(self):
		self.bins = int(86400/self.binSize) # 1 day = 86400 seconds

		LoadCtrl.startup(self)
		
		if self.lastModelTraining < self.host.time() - 24*3600:
			if self.lastModelTraining == -1:
				self.trainModel()
			else:
				self.runInThread('trainModel')

	def timeTick(self, time):
		LoadCtrl.timeTick(self, time)

		# Retrain the model if it is too "old" (1 day now)
		if self.lastModelTraining < self.host.time() - 24*3600:
			self.runInThread('trainModel')



#### PREDICTION CODE
	def doPrediction(self,  startTime,  endTime, adapt=False):
		# Get the sun prediction
		sunPrediction = copy.deepcopy( self.zCall(self.sun, 'doPrediction', startTime , endTime, self.timeBase) )
		result = self.predictProduction(sunPrediction, startTime,  endTime)

		return result


### Training the model based on the historical data
	def trainModel(self):
		self.lastModelTraining = self.host.time()

		self.updateDeviceProperties()
		time = self.host.time()
		time -= time%(24*3600) # Align data to start of a day

		# Step 1: get historical data of the PV panel:
		pvData = list(self.zCall(self.dev, 'readValues', time - self.historySize, time, None, self.regressionTimeBase ) )

		# Step 2: Get historical weather data from the sun object
		ghi = list(self.zCall(self.sun, 'readValues', time - self.historySize, time, "irradiationGHI", self.regressionTimeBase ) )
		dni = list(self.zCall(self.sun, 'readValues', time - self.historySize, time, "irradiationDNI", self.regressionTimeBase ) )

		pvData = list(pvData[0:len(ghi)])

		# Do some magic here, PV training model
		# Split the data in bins of an hour (or configurable)
		# Might want to lower the timebase when getting data for more points.

		# See: https://stackoverflow.com/questions/11479064/multiple-linear-regression-in-python

		# Create the lists
		maxProduction = [0] * self.bins
		predBins = []
		prodBins = []
		for i in range(0, self.bins):
			predBins.append([])
			prodBins.append([])

		assert(len(pvData) == len(ghi) == len(dni))

		for i in range(0,len(ghi)):
			# Check if we have data in all vectors
			b = int( ( (i*self.regressionTimeBase) % 86400 ) / self.binSize ) # selecting the right bin b


			if ghi[i] is None:
				ghi[i] = 0
			if dni[i] is None:
				dni[i] = 0
			if pvData[i] is None:
				pvData[i] = 0

			# Append data to the right vector
			prodBins[b].append(pvData[i].real)
			predBins[b].append([ghi[i], dni[i]])

			# Select the maximum observed production for a given bin
			if pvData[i].real < maxProduction[b]:
				maxProduction[b] = pvData[i].real

		self.lockModel.acquire()

		# Now apply a linear regression:
		self.model = []
		for b in range(0, self.bins):
			learning = linear_model.LinearRegression()
			learning.fit(predBins[b], prodBins[b])

			# Save the data
			self.model.append(list(learning.coef_))

		# Copy the production list:
		self.maxProduction = list(maxProduction)

		self.lockModel.release()


	def predictProduction(self, sunData, startTime, endTime):
		result = []

		time = startTime
		idx = 0

		self.lockModel.acquire()

		while time < endTime:
			b = int( ( time % 86400 ) / self.binSize ) # selecting the right bin b
			result.append(min(0, max(sunData[idx]['GHI']*self.model[b][0] + sunData[idx]['DNI']*self.model[b][1], self.maxProduction[b]) ) )

			if self.forwardLogging:
				self.logValue("W-power.prediction", result[-1], time)

			time += self.timeBase
			idx += 1

		self.lockModel.release()

		return result
