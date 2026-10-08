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

class LoadDev(Device):
	# FIXME: Load Device could use a slight cleanup to rely on instantiated readers in the config itself instead
	# FIXME: Readers themselves could also have a cleanup in the interface to make it easier to use
	def __init__(self,  name,  host, influx=False, reader=None):
		Device.__init__(self,  name,  host)
		
		self.devtype = "Load"
		
		#params
		self.filename = None
		self.filenameReactive = None
		self.filesource = None
		self.column = -1
		self.scaling = 1.0

		self.reader = reader
		self.readerReactive = None
		self.influx = influx
		self.infuxTags = None

		# Subtract data if centralized sensors are used
		self.subtractReaders = []
		# Format per entry: {reader: Reader(), reactive: False, scaling: 1}

	def startup(self):
		self.lockState.acquire()
		if self.reader == None:
			if self.influx:
				self.reader = InfluxDBReader(self.type, timeBase=self.timeBase, host=self.host, value = "W-power.real.c."+self.commodities[0])
				self.readerReactive = InfluxDBReader(self.type, timeBase=self.timeBase, host=self.host, value="W-power.imag.c." + self.commodities[0])
				if self.infuxTags is None:
					self.reader.tags = {"name": self.name}
					self.readerReactive.tags = {"name": self.name}
				else:
					self.reader.tags = self.infuxTags
					self.readerReactive.tags = self.infuxTags
			else:
				self.reader = CsvReader(dataSource=self.filename, timeBase=self.timeBase, column=self.column, timeOffset=self.timeOffset)
				if self.filenameReactive is not None and self.readerReactive is None:
					self.readerReactive = CsvReader(dataSource=self.filenameReactive, timeBase=self.timeBase, column=self.column, timeOffset=self.timeOffset)

		# persistence
		if self.persistence != None:
			watchlist = ["consumption", "plan"]
			self.persistence.setWatchlist(watchlist)

		self.lockState.release()

		Device.startup(self)

	def preTick(self, time):
		self.lockState.acquire()
		for c in self.commodities:	
			if self.host.timeBase <= self.timeBase:
				# if self.filenameReactive != None:
				# 	self.consumption[c] = complex(self.readValue(time), self.readValue(time, self.filenameReactive))
				# else:
				self.consumption[c] = self.readValue(time)
			else:
				assert(self.host.timeBase % self.timeBase == 0)
				#resample the profile:
				total = 0.0
				totalr = 0.0
				for i in range(0, int(self.host.timeBase/self.timeBase)): #Forward looking
					total += self.readValue(time+(i*self.timeBase))
					totalr += self.readValue(time+(i*self.timeBase), self.filenameReactive)
				self.consumption[c] = complex((total / (self.host.timeBase/self.timeBase)), (totalr / (self.host.timeBase/self.timeBase)))
		self.lockState.release()

	def timeTick(self,  time):
		self.prunePlan()
				
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
		r['filename'] = self.filename
		r['filenameReactive'] = self.filenameReactive
		r['scaling'] = self.scaling
		r['column'] = self.column
		self.lockState.release()

		return r

#### LOCAL HELPERS
	def readValue(self, time, filename=None, timeBase=None):
		if timeBase is None:
			timeBase = self.timeBase

		r = self.reader.readValue(time, timeBase=timeBase)
		if self.readerReactive is not None:
			rr = self.readerReactive.readValue(time, timeBase=timeBase)
			r = complex(r, rr)

		# Subtract other readers
		for s in self.subtractReaders:
			v = s['reader'].readValue(time, timeBase=timeBase) * s['scaling']
			if s['reactive'] is True:
				v = complex(0.0, v)

			# subtract:
			r -= v

		if r is not None:
			r = r  * self.scaling

		return r

	def readValues(self, startTime, endTime, filename=None, timeBase=None):
		if timeBase is None:
			timeBase = self.timeBase

		result = []
		time = startTime
		while time < endTime:
			result.append(self.readValue(time, None, timeBase))
			time += timeBase

		return result

		# result = self.reader.readValues(startTime, endTime, None, timeBase)
		#
		# for i in range(0, len(result)):
		# 	if result[i] is not None:
		# 		result[i] *= self.scaling
		#
		# return result