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

# Now comes the house model
# This is defined as a function, such that multiple houses can be created easily
# Note that the following function is used in network models, so keeping it this way makes integration of networks convenient
def addHouse(node, coordx, coordy, phase, houseNum):
	# First add add a smart meter
	sm = MeterDev("SmartMeter-House-"+str(houseNum),  sim, list(commodities)) #params: name, simHost
	#gm = MeterDev("SmartGasMeter-House-"+str(houseNum),  sim, commodities=['NATGAS'])

	# FIXME: Needs to be cleaned up to support also multiple phases. Now we have abalanced setup
	if node is not None:
		node.addMeter(sm, phase)

# ADDING A HEMS

	# Or an auction (PowerMatcher) controller
	if useAuction:
		cp = CongestionPoint()
		cp.setUpperLimit('ELECTRICITY', 20 * 200 * 3)
		cp.setLowerLimit('ELECTRICITY', -20 * 200 * 3)

		ctrl = AggregatorCtrl("Aggregator-"+str(houseNum), rootctrl, sim, cp)
		ctrl.strictComfort = False
		ctrl.islanding = useIslanding

