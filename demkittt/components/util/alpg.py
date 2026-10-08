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

#helper function to convert some input data from the ALPG into lists for model creation

def listFromFile(fname):
	result = []
	cnt = 0
	fin = open(fname, 'r')
	for line in fin:
		arr = []
		line = line.split(':')[1]
		line = line.rstrip()
		s = line.split(',')
		for element in s:
			if(element != ''):
				arr.append(float(element))
		result.append(arr)
		cnt += 1
	return result

def listFromFileStr(fname):
	result = []
	cnt = 0
	fin = open(fname, 'r')
	for line in fin:
		arr = []
		line = line.split(':')[1]
		line = line.rstrip()
		s = line.split(',')
		for element in s:
			if(element != ''):
				arr.append((element))
		result.append(arr)
		cnt += 1
	return result

def indexFromFile(fname, hnum):
	cnt = 0
	fin = open(fname, 'r')
	for line in fin:
		line = int(line.split(':')[0])
		if line == hnum:
			return cnt
		cnt += 1
	return -1


