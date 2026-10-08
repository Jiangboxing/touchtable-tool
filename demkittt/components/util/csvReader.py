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

from itertools import islice
from util.reader import Reader
import os

class CsvReader(Reader):
	def __init__(self,  dataSource, timeBase = 900, column = -1, timeOffset=0):
		Reader.__init__(self, timeBase, column, timeOffset)

		#params
		self.dataSource = dataSource
		self.column = column
		self.timeOffset = timeOffset

		# Check if the datasource exists
		if dataSource != None:
			assert(os.path.isfile(self.dataSource)) # Check if the file exists

	def retrieveValues(self, startTime, endTime = None, value = None, tags = None):
		startTime += self.timeOffset
		endTime += self.timeOffset

		# Note, in this context the value is the filename
		startLine = int(startTime / self.timeBase)
		endLine = None

		if endTime != None and startTime != endTime:
			endLine = int(endTime / self.timeBase)

		if value == None:
			value = self.dataSource

		# Now read the data
		with open(value,'r') as f:  # https://stackoverflow.com/questions/1767513/read-first-n-lines-of-a-file-in-python
			tmpCache = list(islice(f, startLine, endLine))
		f.close()

		result = []
		for l in tmpCache:
			if self.column == -1:
				result.append(float(l))
			else:
				result.append(float(l.split(';')[self.column]))

		return result