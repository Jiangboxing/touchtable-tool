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

evTypes = {
	"Tesla Model S P100D" :
		{
			"chargingPowers"	: [0, 150000], # Power in W
			"capacity"			: 100000, # Capacity in Wh
			"discrete"			: False,
			"supportDcMode"		: True,
			"support3pMode"		: True,
			"hybrid"			: False # Hybrid car or not, could be used for load shedding
		},
	# "Brand Name Type" :
	# 	{
	# 		"chargingPowers"	: [0, 150000], # Power in W
	# 		"capacity"			: 100000, # Capacity in Wh
	# 		"discrete"			: False,
	# 		"supportDcMode"		: True,
	# 		"support3pMode"		: True,
	#		"hybid"				: False
	# 	},

	"default" :
		{
			"chargingPowers"	: [0, 150000], # Power in W
			"capacity"			: 100000, # Capacity in Wh
			"discrete"			: False,
			"supportDcMode"		: True,
			"support3pMode"		: True,
			"hybrid"			: False
		}
}