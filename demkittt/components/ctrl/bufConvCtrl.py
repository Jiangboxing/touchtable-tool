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


from ctrl.bufCtrl import BufCtrl

import copy
import util.helpers
from util.windowPredictor import WindowPredictor

##### NOTICE #####
# Note that there is a better thermal model for heating in the thermal folder!

#Buffer converter controller
class BufConvCtrl(BufCtrl):
	def __init__(self,  name,  dev,  ctrl,  host):
		BufCtrl.__init__(self,   name,  dev,  ctrl,  host)

		self.devtype = "BufferConverterController"
		self.predictor = None

		self.useReactiveControl = False #Heat pumps dont do this

	def startup(self):
		# Notice to be kept until it is tested or the whole model is removed
		self.logWarning("This controller has received a major prediction module update on May 30 2018.\n"+
						"But it is untested due to reduced need for this model.\n"+
						"Please check if predictions still work correctly or revert.")

		BufCtrl.startup(self)

		# Initialize the predictions
		self.predictor = WindowPredictor(self.timeBase)

		time = self.host.time(self.timeBase) - (4*7*24*3600)
		data = list(self.zCall(self.dev, 'readValues', time , time + (4*7*24*3600), None, self.timeBase) )
		self.predictor.addSamples(data, time, self.timeBase)

		# persistence
		if self.persistence != None:
			watchlist = self.watchlist + ["devData", "devDataUpdate", "predictor"]
			self.persistence.setWatchlist(watchlist)

	def timeTick(self, time):
		# Add a sample to the predictor
		if (time % self.timeBase == 0):
			self.updateDeviceProperties()
			self.predictor.addSample(self.devData['selfConsumption'], time)

		if self.useEventControl:
			if time >= self.nextPlan:
				self.requestIncentive()
			
	def doPlanning(self, signal, requireImprovement = True):
		self.lockPlanning.acquire()
		# Synchronize the device state:
		deviceState = self.updateDeviceProperties()

		# Perform a prediction on the energy demand drained from the buffer
		consumption = self.doPrediction(signal.time-(signal.time%signal.timeBase),
										signal.time-(signal.time%signal.timeBase)+signal.timeBase*signal.planHorizon)

		if len(consumption) != signal.planHorizon:
			consumption = util.helpers.interpolate(consumption, signal.planHorizon)

		#Scale the consumption according to the COP
		consumption = [x/self.devDataPlanning['cop'] for x in consumption]

		# Call the buffer planning implementation from the buffer controller
		result = self.bufPlanning(signal, copy.deepcopy(self.candidatePlanning[self.name]), consumption, requireImprovement, self.devDataPlanning, self.planningCapacity, self.planningPower)
		self.candidatePlanning[self.name] = copy.deepcopy(result['profile'])

		self.lockPlanning.release()
		return result

	def doEventPlanning(self, signal):
		self.lockPlanning.acquire()
		self.updateDeviceProperties()

		# Synchronize the device state:
		deviceState = self.updateDeviceProperties()

		# Perform a prediction on the energy demand drained from the buffer
		consumption = self.doPrediction(signal.time-(signal.time%signal.timeBase),
										signal.time-(signal.time%signal.timeBase)+signal.timeBase*signal.planHorizon)

		if len(consumption) != signal.planHorizon:
			consumption = util.helpers.interpolate(consumption, signal.planHorizon)

		#Scale the consumption according to the COP
		consumption = [x/self.devData['cop'] for x in consumption]

		self.lockPlanning.release()

		# Call the buffer planning implementation from the buffer controller
		return self.bufEventPlanning(signal, consumption)


	def doPrediction(self,  startTime,  endTime):
		if self.perfectPredictions:
			return list(self.zCall(self.dev, 'readValues', startTime , endTime, None, self.timeBase) )
		else:
			return list(self.predictor.predictValues(startTime, int((endTime-startTime) / self.timeBase) ) )