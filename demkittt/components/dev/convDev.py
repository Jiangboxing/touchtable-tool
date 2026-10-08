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


from util.influxdbReader import InfluxDBReader
from util.csvReader import CsvReader
import util.helpers

from dev.device import Device

# FIXME: For now, this device is a dummy to test basic functionality for optimization ofy hybrid systems using Profile Steering

class ConvDev(Device):
	def __init__(self,  name,  host):
		Device.__init__(self,  name,  host)
		
		self.devtype = "Converter"
		
		self.commodities = ['ELECTRICITY', 'HEAT']
		# FIXME: We do not support multiple commodities on both sides yet
		self.commoditiesIn = ['ELECTRICITY']
		self.commoditiesOut = ['HEAT']
		self.cop = {'HEAT': -4}

		self.powers = [0, 4000] # Note, negative options

	def startup(self):
		self.lockState.acquire()
		# persistence
		if self.persistence != None:
			watchlist = ["consumption", "plan"]
			self.persistence.setWatchlist(watchlist)

		self.lockState.release()

		assert(len(self.commoditiesIn) == 1) 	# For now we support only one input
		assert(len(self.powers) == 2) 	# For now we only support a continuous range

		Device.startup(self)


	def preTick(self, time):
		# self.lockState.acquire()
		# self.prunePlan()
		#
		# for c in self.commodities:
		# 	if c in self.plan and len(self.plan[c]) > 0:
		# 		self.consumption[c] = self.plan[c][0][1].real
		# 	else:
		# 		self.consumption[c] = complex(0.0, 0.0)
		#
		# self.lockState.release()
		pass

	def timeTick(self,  time):
		self.lockState.acquire()
		self.prunePlan()

		for c in self.commodities:
			if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
				self.consumption[c] = self.plan[c][0][1].real
			else:
				self.consumption[c] = complex(0.0, 0.0)

		self.lockState.release()
				
	def logStats(self, time):
		self.lockState.acquire()
		try:
			for c in self.commodities:
				self.logValue("W-power.real.c." + c, self.consumption[c].real)
				self.logValue("W-power.imag.c." + c, self.consumption[c].imag)
				if self.smartOperation and c in self.plan and len(self.plan[c]) > 0:
					self.logValue("W-power.plan.real.c."+c, self.plan[c][0][1].real)
					self.logValue("W-power.plan.imag.c."+c, self.plan[c][0][1].imag)
		except:
			pass
		self.lockState.release()

#### INTERFACING
	def getProperties(self):
		r = Device.getProperties(self) 	# Get the properties of the overall Device class, which already includes global properties

		self.lockState.acquire()
		# Populate the result dict
		r['cop'] = self.cop
		r['powers'] = self.powers
		r['commoditiesIn'] = self.commoditiesIn
		r['commoditiesOut'] = self.commoditiesOut
		self.lockState.release()

		return r
