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


if useAuction:
	cpstreet = CongestionPoint()
	cpstreet.setUpperLimit('ELECTRICITY', 200*63*3)
	cpstreet.setLowerLimit('ELECTRICITY', -200*63*3)

	# Auctioneer, usually not in the house
	rootctrl = AuctioneerCtrl("Auctioneer",  sim, cpstreet)
	rootctrl.maxGeneration = 200*60*3    # We try to island here
	rootctrl.minGeneration = -200*60*3	# Set these two differently, based on an estimated power usage for example
	rootctrl.timeBase = ctrlTimeBase

	rootctrl.strictComfort = False
	rootctrl.islanding = False #useIslanding

