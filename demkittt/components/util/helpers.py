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


import os
import numpy as np

# Interpolate based on the timebase difference (optional give a length to check)
def interpolatetb(input, oldTimeBase, newTimeBase, outputLenght=-1):
	if oldTimeBase < newTimeBase and newTimeBase%oldTimeBase == 0:
		cnt = 0
		sum = 0
		result = []

		for i in range(0, len(input)):
			sum += input[i]
			cnt += 1
			if cnt == int(newTimeBase/oldTimeBase) or i == len(input)-1:
				result.append(sum / int(newTimeBase/oldTimeBase))
				sum = 0
				cnt = 0
	else:
		result = np.interp(np.arange(0, len(input), (newTimeBase / oldTimeBase)), list(range(0, len(input))), input)

	if outputLenght > -1:
		assert(len(result) == outputLenght)

	return result

# Interpolate based on the desired new length
def interpolate(input, outputLength):
	result = np.interp(np.arange(0, len(input), (len(input)/ outputLength)), list(range(0, len(input))),input)
	if len(result) > outputLength:
		result = result[0:outputLength]
	assert(len(result) == outputLength)
	return result

def interpolatePoint(in1, in2, time1, time2, time):
	assert(time2 > time1)
	return ( in1 + ((in2 - in1) / (time2-time1)) * (time - time1) )



def writeCsvLine(fname, line):
	os.makedirs(os.path.dirname(fname), exist_ok=True)
	if not os.path.exists(fname): 
		#overwrite
		f = open(fname, 'w')
	else:
		#append
		f = open(fname, 'a')
	f.write(line + '\n')
	f.close()
	
def writeCsvRow(fname, col, data):
	os.makedirs(os.path.dirname(fname), exist_ok=True)
	if col == 0:
		with open(fname, 'w') as f:
			for l in range(0, len(data)):
				f.write(str(round(data[l])) + '\n')
	else:
		with open(fname, 'r+') as f:
			lines = f.readlines()
			f.seek(0)
			f.truncate()
			j = 0
			for line in lines:
				line = line.rstrip()
				line = line + ';' + str(round(data[j])) + '\n'
				f.write(line)
				j = j + 1	


