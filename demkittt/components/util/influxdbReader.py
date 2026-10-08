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

import requests

from util.reader import Reader
from usrconf import *

class InfluxDBReader(Reader):
	def __init__(self, measurement, address=influxUrl, port=influxPort, database=influxDB, timeBase=60, aggregation='mean', offset=None, raw=False, value="W-power.real.c.ELECTRICITY", tags={}, host=None):
		Reader.__init__(self, timeBase, -1, offset, host)

		self.cacheFuture = False # Allow to cache future data. Useful in case of given simulation data

		#params
		self.timeBase = timeBase
		self.offset = offset

		if address[0:4] != "http":
			address = "http://" + address
		
		self.address = address
		self.port = port
		self.database = database
		self.user = ""
		self.password = ""
		self.prefix = ""

		self.measurement = measurement
		self.aggregation = aggregation
		self.raw = raw

		self.value = value
		self.tags = tags


	def retrieveValues(self, startTime, endTime=None, value=None, tags=None):
		if endTime is None:
			endTime = startTime + self.timeBase
		if value is None:
			value = self.value
		if tags is None:
			tags = self.tags

		# Create a string from the tags to put in the query
		condition = ""
		if tags:
			for tag_key, tag_value in tags.items():
				condition += '(\"' + tag_key + '\" = \'' + tag_value + '\') AND '

		query = 'SELECT ' + self.aggregation + '(\"' + value + '\") FROM \"' + self.measurement + '\" WHERE ' + condition + 'time >= ' + str(
			startTime) + '000000000 AND time < ' + str(endTime) + '000000000 GROUP BY time(' + str(
			self.timeBase) + 's) fill(previous) ORDER BY time ASC'  # LIMIT '+str(l)

		r = self.getData(query, startTime, endTime)

		return r

	def getData(self, query, startTime, endTime):
		url = self.address + ":" + str(self.port) + "/query"

		payload = {}
		payload['db'] = self.database
		payload['u'] = self.user
		payload['p'] = self.password
		payload['q'] = query


		r = requests.get(url, params=payload)
		
		if self.raw:
			return r.json()
		else:
			result = [None] * int((endTime - startTime) / self.timeBase)
			try:
				if('series' in r.json()['results'][0]):
					idx = 0
					d = r.json()['results'][0]['series'][0]['values']
					for value in d:
						result[idx] = value[1]
						idx += 1
			except:
				pass

			return result