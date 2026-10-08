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

from datetime import datetime
from pytz import timezone

timeZone = timezone('Europe/Amsterdam')
startTime = int(timeZone.localize(datetime(2019, 1, 1)).timestamp())
timeOffset = -1 * int(timeZone.localize(datetime(2019, 1, 1)).timestamp())

timeBase = 15*60 # Default timebase
intervals = float('inf')	# Simulating 7 days of data (calculations based on the timeBase)
monthLength = 1


# Data storage settings
database = 'dem'					# Database to store results
dataPrefix = ''						# A prefix (optional) can be used to put multiple simulations in one database conveniently. NOTE: Disable the cleardatabase!
clearDB = True						# Clear the database or not. !

# Number of houses, not used in the demohouse:
numOfHouses = 6

# ALPG input
alpgFolder = 'alpg/output/demo/'
useALPG = True 	# Use ALPG data

# Logging:
logDevices = True
logFlow = True

# Restore data on restart (for demo purposes)
enablePersistence = False

# Enable control:
# NOTE: AT MOST ONE OF THESE MAY BE TRUE! They can all be False, however
useCtrl = False	# Use smart control, defaults to Profile steering
useAuction = True	# Use an auction instead, NOTE useMC must be False!
usePlAuc = False	# Use a planned auction instead (Profile steering planning, auction realization), NOTE useMC must be False!

# Specific options for control
useCongestionPoints = False # Use congestionpoints
useMultipleCommits = False	# Commit multiple profiles at once in profile steering
useChildPruning = False		# Remove children after each iteration that haven't provided substantial imporvement
useIslanding = False		# Use islanding mode

# Specific for device control:
useFillMethod = True		# Use a sort of valley filling approach with only the battery

ctrlTimeBase = 900		# Timebase for controllers
useEC = True			# Use Event-based control
usePP = False			# Use perfect predictions (a.k.a no predictions)
useQ = False				# Perform reactive power optimization
useMC = False			# Use three phases and multicommodity control
# Note either EC or PP should be enabled






# NOTE: No need to modify lines below
if useMC:
	assert(useAuction == False)
	assert(usePlAuc == False)

### MODEL CREATION ####

# Now it is time to create the complete model using the loaded modules
if useMC:
	commodities = ['EL1', 'EL2', 'EL3']
	weights = {'EL1': (1/3), 'EL2': (1/3), 'EL3': (1/3)}
else:
	commodities = ['ELECTRICITY']
	weights = {'ELECTRICITY': 1}

# Initialize the random seed. Not required, but definitely preferred
random.seed(1337)
