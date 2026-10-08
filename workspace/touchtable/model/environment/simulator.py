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


##### HERE STARTS THE REAL MODEL DEFINITION OF THE HOUSE TO BE SIMULATED #####
# First we need to instantiate the Host environment:
sim = PushHost(useMaster=False)

#Some simulation settings
sim.timeBase = timeBase
sim.timeOffset = timeOffset
sim.timezone = timeZone
sim.intervals = intervals
sim.monthLength = monthLength
sim.startTime = startTime
sim.db.database = database
sim.db.prefix = dataPrefix
# Use the following flags to log more/less details (significantly influences simulation speed)
sim.logDevices = logDevices
sim.logControllers = True 	# NOTE: Controllers do not log so much, keep this on True (default)!
sim.logFlow = logFlow
sim.enablePersistence = enablePersistence
if clearDB:
	sim.clearDatabase() 	# Removes and creates a database
