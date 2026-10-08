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


import util.helpers
from ctrl.loadCtrl import LoadCtrl

import linecache


class VfLoadCtrl(LoadCtrl):
	def __init__(self,  name,  dev, ctrl,  host):
		LoadCtrl.__init__(self,   name,  dev,  ctrl,  host)

		self.devtype = "vfLoadController"

	def timeTick(self, time):
		pass

	def doPrediction(self,  startTime,  endTime):
		if self.perfectPredictions:
			return self.dev.readValues(startTime, endTime)
		else:
			return self.doHistoricPrediction(startTime, endTime)

	def doHistoricPrediction(self, startTime, endTime):
		pass

	def getHistoricData(self, startTime, endTime):
		assert(endTime < self.host.time())
		return self.dev.readValues(startTime, endTime)

	def logStats(self, time):
		pass
