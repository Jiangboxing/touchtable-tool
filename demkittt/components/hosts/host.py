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


from core.core import Core

from usrconf import *

from util.persistence import Persistence

import time
from datetime import datetime
import pytz
from pytz import timezone
import random

class Host(Core):
	def __init__(self, name="host"):
		# Type of simulation
		Core.__init__(self, name)

		# Time accounting, all in UTC! Use self.timezone to convert into local time
		self.timezone = timezone('Europe/Amsterdam')
		self.timeformat = "%d-%m-%Y %H:%M:%S %Z%z"

		self.timezonestr = 'Europe/Amsterdam'  # This is not a pytz object for Astral!
		self.latitude = 52.2215372
		self.longitude = 6.8936619

		# Setting the starttime and (default) offset for CSV files
		self.startTime = int(self.timezone.localize(datetime(2018, 1, 29)).timestamp())
		self.timeOffset = -1 * int(self.timezone.localize(datetime(2018, 1, 1)).timestamp())
			# Note that the offset will be added, so in general you want to have a negative sign, unless you have a crystal ball ;-)

		# Internal bookkeeping
		self.currentTime = 0
		self.previousTime = 0

		# Simulation settings
		self.timeBase = 60
		self.intervals = 7*1440

		self.randomSeed = 42
		self.executionTime = time.time()

		# Persistence
		self.persistence = None

		# network master used to propagate ticks through the network.
		self.networkMaster = False
		self.slaves = []

		# Actions:
		self.executeControl = True
		self.executeLoadFlow = True

		# Live interactive mode
		self.pause = False


	def startSimulation(self):
		self.currentTime = self.startTime
		self.previousTime = self.startTime

		#inject a seed:
		random.seed(self.randomSeed)

		self.startup()

	def startup(self):
		self.currentTime = self.startTime
		self.previousTime = self.startTime

		# persistence
		if self.enablePersistence:
			self.persistence = Persistence(self, self)
			watchlist = ["currentTime", "previousTime"]
			self.persistence.setWatchlist(watchlist)

		self.logMsg("Starting")

		self.db.createDatabase()

		for e in self.entities:
			e.startup()

		self.restoreStates()

	def shutdown(self):
		self.logMsg("Shutting down")
		for e in self.entities:
			e.shutdown()

		#write data
		self.db.writeData(True)

		# Save the state
		self.storeStates()

		print("Total execution time: "+str(time.time() - self.executionTime))
		self.logCsvLine('stats/sim/time', self.name+";"+str(time.time() - self.executionTime) )

		# Do a hard exit
		exit()

	def timeTick(self, time, absolute = False):
		if absolute:
			self.currentTime = time
		else:
			self.currentTime += time

		self.previousTime = self.currentTime

		if not self.liveOperation and (int(self.currentTime) % 3600) == 0:
			self.logMsg("Simulating: interval "+str(int((time - self.startTime)/self.timeBase))+" of "+str(self.intervals))

	# All times in UTC
	def time(self, timeBase = None):
		if timeBase is None:
			return self.currentTime
		else:
			return self.currentTime - (self.currentTime % timeBase)

	def timems(self):
		return float(self.currentTime) # This function should provide the time with milliseconds (as float) in real applications

	def timeObject(self):
		return datetime.fromtimestamp(self.currentTime, tz=pytz.utc)

	def timeHumanReadable(self, local=True):
		if local:
			# Display local time
			return self.timeObject().astimezone(self.timezone).strftime(self.timeformat)
		else:
			# Display UTC
			return self.timeObject().astimezone(pytz.utc).strftime(self.timeformat)

	def timeInterval(self):
		if self.currentTime == self.previousTime:
			return self.timeBase

		return self.currentTime - self.previousTime

	# Ticks
	def preTickEnvs(self, time):
		for e in self.environments:
			e.preTick(time)

		if self.networkMaster:
			self.zCall(self.slaves, 'preTickEnvs', time)

	def preTickDevs(self, time):
		for d in self.devices:
			d.preTick(time)

		if self.networkMaster:
			self.zCall(self.slaves, 'preTickDevs', time)

	def preTickCtrl(self, time):
		if self.executeControl:
			for c in self.controllers:
				c.preTick(time)

			if self.networkMaster:
				self.zCall(self.slaves, 'preTickCtrl', time)

	def preTickComps(self, time):
		for c in self.components:
			c.preTick(time)

		if self.networkMaster:
			self.zCall(self.slaves, 'preTickComps', time)

	def timeTickEnvs(self, time):
		for e in self.environments:
			e.timeTick(time)

		if self.networkMaster:
			self.zCall(self.slaves, 'timeTickEnvs', time)

	def timeTickDevs(self, time):
		for d in self.devices:
			d.timeTick(time)

		if self.networkMaster:
			self.zCall(self.slaves, 'timeTickDevs', time)

	def timeTickCtrl(self, time):
		if self.executeControl:
			for c in self.controllers:
				# print("TimeTick" + c.name)
				c.timeTick(time)

		if self.networkMaster:
			self.zCall(self.slaves, 'timeTickCtrl', time)

	def timeTickComps(self, time):
		for c in self.components:
			c.timeTick(time)

		if self.networkMaster:
			self.zCall(self.slaves, 'timeTickComps', time)

	def timeTickMeters(self, time):
		for m in self.meters:
			m.measure(time)

		if self.networkMaster:
			self.zCall(self.slaves, 'timeTickMeters', time)

	def simulateCosts(self, time):
		for c in self.costs:
			c.simulate(time)

		if self.networkMaster:
			self.zCall(self.slaves, 'simulateCosts', time)

	def simulateFlows(self, time):
		if self.executeLoadFlow:
			for f in self.flows:
				f.simulate(time)

		if self.networkMaster:
			self.zCall(self.slaves, 'simulateFlows', time)


	def postTickLogging(self, time, force = False):
		if self.logDevices:
			for d in self.devices:
				d.logStats(self.currentTime)
			for e in self.environments:
				e.logStats(self.currentTime)

		# Always log meters
		for m in self.meters:
				m.logStats(self.currentTime)

		if self.logControllers:
			for c in self.controllers:
				c.logStats(self.currentTime)
		else:
			self.logControllerStats(self.currentTime)

		for f in self.flows:
			f.logStats(self.currentTime) # Overall stats for flow

			if self.logFlow:
				for node in f.nodes:
					node.logStats(self.currentTime)
				for edge in f.edges:
					edge.logStats(self.currentTime)

		if self.networkMaster:
			self.zCall(self.slaves, 'postTickLogging', time)

		# Overall stats
		self.logDeviceStats(self.currentTime)

		self.db.writeData(force)

	def logHostValue(self, measurement,  value, time=None):
#         tags = {'devtype':self.devtype,  'name':self.name}
#         values = {measurement:value}
#         self.host.logValue(self.type,  tags,  values, time)
		data = "host,devtype="+self.devtype+",name="+self.name+" "+measurement+"="+str(value)
		self.host.logValuePrepared(data, time)


	def logDeviceStats(self, time):
		totalPower = complex(0.0, 0.0)
		totalPowerC = {}
		totalSoC = 0
		power = {}
		soc = {}

		#collect all data
		for d in self.devices:
			# First check if all entries are there, otherwise, make em
			if d.devtype not in power:
				power[d.devtype] =  {}
				soc[d.devtype] = 0.0

			for c in d.commodities:
				if c not in totalPowerC:
					totalPowerC[c] = complex(0.0, 0.0)
				if c not in power[d.devtype]:
					power[d.devtype][c] = complex(0.0, 0.0)

				if hasattr(d, 'consumption'):
					#now add this device to the lists
					totalPower += d.consumption[c]
					totalPowerC[c] += d.consumption[c]
					power[d.devtype][c] += d.consumption[c]

			#now check if we are a buffer!
			if hasattr(d, 'soc'):
				totalSoC += d.soc
				soc[d.devtype] += d.soc

		#Push the data to the storage
		self.logValuePrepared("host,devtype=total,name="+self.name+" W-power.real="+str(totalPower.real))
		self.logValuePrepared("host,devtype=total,name="+self.name+" W-power.imag="+str(totalPower.imag))
		self.logValuePrepared("host,devtype=total,name="+self.name+" Wh-soc="+str(totalSoC))

		#now per commodity
		for k, v in totalPowerC.items():
			self.logValuePrepared("host,devtype=total,name="+self.name+" W-power.real.c."+k+"="+str(v.real))
			self.logValuePrepared("host,devtype=total,name="+self.name+" W-power.imag.c."+k+"="+str(v.imag))

		#now per devtype
		for key in power.keys():
			for k,v in power[key].items():
				self.logValuePrepared("host,devtype="+key+",name="+self.name+" W-power.real.c."+k+"="+str(v.real))
				self.logValuePrepared("host,devtype="+key+",name="+self.name+" W-power.imag.c."+k+"="+str(v.imag))

		for k,v in soc.items():
			self.logValuePrepared("host,devtype="+k+",name="+self.name+" Wh-soc="+str(v))


	def logControllerStats(self, time):
		for c in self.controllers:
			# First check if all entries are there, otherwise, make em
			if c.devtype == "groupController":
				c.logStats(time)


	def restoreStates(self):
		if self.persistence is not None:
			self.persistence.load()

		for e in self.entities:
			e.restoreState()

	def storeStates(self):
		if self.persistence is not None:
			self.persistence.save()

		for e in self.entities:
			e.storeState()