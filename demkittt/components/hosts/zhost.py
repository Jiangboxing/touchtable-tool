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


from core.zCore import ZCore
from host.host import Host

from usrconf import *

class ZHost(ZCore, Host):
	def __init__(self, name="host"):
		self.liveOperation = True
		ZCore.__init__(self, name)

		# Time accounting, all in UTC! Use self.timezone to convert into local time
		self.timezone = timezone('Europe/Amsterdam')
		self.timeformat = "%d-%m-%Y %H:%M:%S %Z%z"

		# Setting the starttime and (default) offset for CSV files
		self.startTime = int(self.timezone.localize(datetime(2018, 1, 29)).timestamp())
		self.timeOffset = -1 * int(self.timezone.localize(datetime(2018, 1, 1)).timestamp())
			# Note that the offset will be added, so in general you want to have a negative sign, unless you have a crystal ball ;-)

		# Internal bookkeeping
		self.currentTime = 0
		self.previousTime = 0

		# Simulation settings
		self.timeBase = 60
		self.intervals = 7*1440
		self.randomSeed = 42
		self.executionTime = time.time()

		# network master used to propagate ticks through the network.
		self.networkMaster = False
		self.slaves = []