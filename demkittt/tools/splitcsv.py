#!/usr/bin/python3

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


import sys

if len(sys.argv) == 1:
	print("Error, need two arguments: ./splitcsv.py folder input.file")
p = sys.argv[1]
i = p+'/'+sys.argv[2]


fi = open(i,  'r')
line = fi.readline();
cols = len(line.split(';'))

print("cols to be processed: "+str(cols))

for c in range(0, cols):
	print("col: "+str(c))
	
	out = []
	o = p+'/'+sys.argv[2].split('.')[0]+"-"+str(c)+".csv"
	fo = open(o, 'w')
	
	fi.seek(0)
	for line in fi:
		fo.write(line.rstrip().split(';')[c] + '\n')
		
	fo.close()
