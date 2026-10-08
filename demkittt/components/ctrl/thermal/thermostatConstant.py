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


from ctrl.thermal.thermostat import Thermostat

# Thermostat with constant setpoint for use in e.g. floor heating systems
class ThermostatConstant(Thermostat):
	def __init__(self, name, zone, ctrl, host):
		assert(ctrl == None) # This device does not support an external controller
		Thermostat.__init__(self, name, zone, ctrl, host)

		self.setpoint = None
			
	def startup(self):
		Thermostat.startup(self)

		if self.setpoint is None:
			# No setpoint set, use the average of the jobs
			self.jobs.sort()
			i = -1
			cnt = 0
			total = 0

			for job in self.jobs:
				if job[1]['setpoint'] > 18.0:
					total += job[1]['setpoint']
					cnt += 1

			self.setpoint = round( (total/float(cnt)) * 2.0) / 2.0

		self.temperatureSetpointHeating = self.setpoint
		self.temperatureSetpointCooling = self.setpoint



	def thermostatCtrl(self, time):
		# synchronize zone state:
		self.updateDeviceProperties()
		zoneTemperature = self.devData['temperature']

		if zoneTemperature > self.temperatureSetpointHeating + self.temperatureDeadband[1] and zoneTemperature < self.temperatureSetpointCooling + self.temperatureDeadband[2]:
			self.heatDemand = 0
		else:
			self.heatDemand = self.dev.doPrediction(time, time+self.timeBase, [self.temperatureSetpointHeating], [self.temperatureSetpointCooling], self.dev.minHeat, self.dev.maxHeat, self.timeBase)[0]

		# now set the valve
		self.dev.valveHeat = self.heatDemand

	def initializePredictors(self):
		pass

	def doUpperPrediction(self,  startTime,  endTime):
		result = []
		time = startTime
		while time < endTime:
			# add the sample
			result.append(self.setpoint)
			# Advance time
			time += self.timeBase

		return result

	def doLowerPrediction(self,  startTime,  endTime):
		result = []
		time = startTime
		while time < endTime:
			# add the sample
			result.append(self.setpoint)
			# Advance time
			time += self.timeBase

		return result