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


import numpy as np
import operator

from util.helpers import interpolate
from ctrl.groupCtrl import GroupCtrl

class VfGroupCtrl(GroupCtrl):
	def __init__(self, name, host, parent=None, congestionPoint=None):
		GroupCtrl.__init__(self, name, host, parent, congestionPoint)

		self.devtype = "vfGroupController"
		self.historicDays = 10

		self.fillLevel = 0
		self.chargeLevel = 0
		self.baseLoad = 0

		self.runningJobs = {}

		self.logBaseLoad = True
		self.useOptAlg = True

	def preTick(self, time):
		if self.logBaseLoad:
			self.baseLoad = self.doBaseLoadPrediction(self.host.time(), self.host.time() + self.timeBase)

		to_delete = []
		for job_key, job_value in self.runningJobs.items():
			if time > job_value['endTime']:
				to_delete.append(job_key)

		for key in to_delete:
			del self.runningJobs[key]

		if to_delete:
			for job_key, job_value in self.runningJobs.items():
				for c in self.children:
					if c.dev.name == job_key:
						self.runningJobs[job_key]['remainingCharge'] = c.dev.capacity - c.dev.soc

			self.doFillLevelPrediction()

		if self.devtype == "vfGroupController":
			if self.runningJobs:
				self.doChargeLevelPrediction()
			else:
				self.chargeLevel = 0

	def doFillLevelPrediction(self):
		# Baseload is the sum of the historic data of the static loads and a prediction of the pv production
		# When an event occurs, the algorithm must predict the baseload for the day ahead and predict the fill level
		if not self.runningJobs:
			self.fillLevel = 0

		else:
			if self.parent == None:
				self.logMsg("New fill level prediction")

			# If the useOptAlg Flag is set, the optimization algorithm by Thijs/Martijn is used to calculate the fillLevel
			# First we find the first deadline of all running jobs
			if self.useOptAlg:
				minEndTime = float("inf")
				for job_value in self.runningJobs.values():
					if job_value['endTime'] < minEndTime:
						minEndTime = job_value['endTime']

				# Then the baseloads are retrieved from now until the first deadline, for a number of historic days
				startTime = self.host.time()
				endTime = (minEndTime - ((minEndTime - startTime) % self.timeBase)) + self.timeBase
				baseLoads = self.getBaseLoads(startTime, endTime, self.historicDays)

				# Now the maximum filllevel is calculated using the algorithm by Thijs/Martijn.
				# For every historic day, all running jobs are executed and the maximum of the retrieved fill levels is returned
				fillLevel = 0
				for job_key, job_value in self.runningJobs.items():
					for c in self.children:
						if c.dev.name == job_key:
							fillLevel += self.getMaxFillLevel(baseLoads, c, self.runningJobs[job_key], startTime, endTime)

				self.fillLevel = fillLevel

			# If the useOptAlg Flag is not set, we use our own algorithm, which is a for loop that iterates to the correct filllevel
			else:
				# First we find the first deadline of all running jobs
				minEndTime = float("inf")
				for job_value in self.runningJobs.values():
					if job_value['endTime'] < minEndTime:
						minEndTime = job_value['endTime']

				# Then the baseloads are retrieved from now until the first deadline, for a number of historic days
				startTime = self.host.time()
				endTime = (minEndTime - ((minEndTime - startTime) % self.timeBase)) + self.timeBase
				baseLoads = self.getBaseLoads(startTime, endTime, self.historicDays)

				# Finally the maximum filllevel is calculated by running all jobs on the previous days
				self.fillLevel = self.getMaxFillLevel(baseLoads)

	def doChargeLevelPrediction(self):
		#Every interval, the algorithm must predict the baseload for the coming interval
		if self.logBaseLoad:
			self.chargeLevel = max(0, self.fillLevel - self.baseLoad)
		else:
			baseLoad = self.doBaseLoadPrediction(self.host.time(), self.host.time() + self.timeBase)
			self.chargeLevel = max(0, self.fillLevel - baseLoad)

	def executeValleyFillingJob(self):
		self.runningJobs = {}
		for child in self.children:
			if child.devtype == "VfBtsController":
				if child.dev.currentJob:
					job = child.dev.currentJob
					job['remainingCharge'] = job['charge']
					self.runningJobs[child.dev.name] = job

		to_delete = []
		for job_key, job_value in self.runningJobs.items():
			if self.host.time() > job_value['endTime']:
				to_delete.append(job_key)

		for key in to_delete:
			del self.runningJobs[key]

		if to_delete:
			for job_key, job_value in self.runningJobs.items():
				for c in self.children:
					if c.dev.name == job_key:
						self.runningJobs[job_key]['remainingCharge'] = c.dev.capacity - c.dev.soc

		self.doFillLevelPrediction()

	def logStats(self, time):
		t = time - time % self.timeBase
		for c in self.commodities:
			self.logValue("FillLevel.c." + c, self.fillLevel)
			self.logValue("ChargeLevel.c." + c, self.chargeLevel)
			self.logValue("BaseLoad.c." + c, self.baseLoad)

	def doBaseLoadPrediction(self, startTime, endTime):
		loadControllers = []
		pvControllers = []
		for child in self.children:
			if child.devtype == "vfLoadController":
				loadControllers.append(child)
			elif child.devtype == "vfPVController":
				pvControllers.append(child)

		if not loadControllers:
			pvPrediction = [0.0] * int((endTime - startTime) / self.timeBase)
			for pvController in pvControllers:
				prediction = pvController.doPrediction(startTime, endTime)
				prediction = list(interpolate(prediction, int((endTime - startTime) / self.timeBase)))
				pvPrediction = list(np.array(prediction) + np.array(pvPrediction))

			return pvPrediction[0]

		elif not pvControllers:
			for loadController in loadControllers:
				prediction = loadController.doPrediction(startTime, endTime)
				prediction = list(interpolate(prediction, int((endTime - startTime) / self.timeBase)))
				staticLoad = list(np.array(prediction) + np.array(staticLoad))

			return staticLoad[0]

		pvPrediction = [0.0] * int((endTime - startTime) / self.timeBase)
		for pvController in pvControllers:
			prediction = pvController.doPrediction(startTime, endTime)
			prediction = list(interpolate(prediction, int((endTime - startTime) / self.timeBase)))
			pvPrediction = list(np.array(prediction) + np.array(pvPrediction))

		staticLoad = [0.0] * int((endTime - startTime) / self.timeBase)
		for loadController in loadControllers:
			prediction = loadController.doPrediction(startTime, endTime)
			prediction = list(interpolate(prediction, int((endTime - startTime) / self.timeBase)))
			staticLoad = list(np.array(prediction) + np.array(staticLoad))

		return staticLoad[0] + pvPrediction[0]

	def getBaseLoads(self, startTime, endTime, historicDays):
		result = {}

		loadControllers = []
		pvControllers = []
		for child in self.children:
			if child.devtype == "vfLoadController":
				loadControllers.append(child)
			elif child.devtype == "vfPVController":
				pvControllers.append(child)

		if not loadControllers:
			for i in (0, historicDays):
				pvPrediction = [0.0] * int((endTime - startTime) / self.timeBase)
				for pvController in pvControllers:
					prediction = pvController.doPrediction(startTime, endTime)
					prediction = list(interpolate(prediction, int((endTime - startTime) / self.timeBase)))
					pvPrediction = list(np.array(prediction) + np.array(pvPrediction))

				result[i] = pvPrediction
			return result

		elif not pvControllers:
			for i in (0, historicDays):
				staticLoad = [0.0] * int((endTime - startTime) / self.timeBase)
				for loadController in loadControllers:
					prediction = loadController.getHistoricData(startTime - ((i + 1) * 24 * 3600), endTime - ((i + 1) * 24 * 3600))
					prediction = list(interpolate(prediction, int((endTime - startTime) / self.timeBase)))
					staticLoad = list(np.array(prediction) + np.array(staticLoad))

				result[i] = staticLoad
			return result

		pvPrediction = [0.0] * int((endTime - startTime) / self.timeBase)
		for pvController in pvControllers:
			prediction = pvController.doPrediction(startTime, endTime)
			prediction = list(interpolate(prediction, int((endTime - startTime) / self.timeBase)))
			pvPrediction = list(np.array(prediction) + np.array(pvPrediction))

		for i in range(0, historicDays):
			staticLoad = [0.0] * int((endTime - startTime) / self.timeBase)
			for loadController in loadControllers:
				prediction = loadController.getHistoricData(startTime - ((i + 1) * 24 * 3600), endTime - ((i + 1) * 24 * 3600))
				prediction = list(interpolate(prediction, int((endTime - startTime) / self.timeBase)))
				staticLoad = list(np.array(prediction) + np.array(staticLoad))

			baseLoad = list(np.array(staticLoad) + np.array(pvPrediction))
			result[i] = baseLoad

		return result

	def getFillLevel(self, toCharge, baseLoad):
		#toCharge = amount of energy to charge in Ws

		fillLevelIterator = min(baseLoad)
		full = False

		while not full:
			charged = 0
			for loadInterval in baseLoad:
				if loadInterval < fillLevelIterator:
					charged += (fillLevelIterator - loadInterval) * (self.timeBase / 3600)
				if charged >= toCharge:
					full = True
					break

			if not full:
				fillLevelIterator += 10

		return fillLevelIterator

	def getMaxFillLevel(self, baseLoads, child=None, job=None, startTime=None, endTime=None):
		FillLevels = []

		if child is None:
			totalCharge = 0
			for job_value in self.runningJobs.values():
				totalCharge += job_value['remainingCharge']

			for baseLoad_key, baseLoad_value in baseLoads.items():
				FillLevels.append(self.getFillLevel(totalCharge, baseLoad_value))

		else:
			for baseLoad_key, baseLoad_value in baseLoads.items():
				for i in range(0, len(baseLoad_value)):
					baseLoad_value[i] *= -1

				FillLevels.append(child.doJobPlanning(baseLoad_value, startTime, endTime, job, 1.0))

		return max(FillLevels)
