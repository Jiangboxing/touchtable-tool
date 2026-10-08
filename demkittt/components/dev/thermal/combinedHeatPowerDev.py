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


from dev.thermal.thermalBufConvDev import ThermalBufConvDev

#Bufferconverter device
#Note that the buffer level is based on the secondary side, i.e. heat

class CombinedHeatPowerDev(ThermalBufConvDev):
	def __init__(self,  name,  host):
		ThermalBufConvDev.__init__(self,  name,  host)
		self.devtype = "BufferConverter"

		self.commodities = ['ELECTRICITY', 'NATGAS', 'HEAT'] # INPUT, OUTPUT
		self.producingPowers = [0, 13500] # Output power of the source, in HEAT

		# Commodity wise cop, converted from HEAT:
		self.cop = {'ELECTRICITY': (-13.5/6.0), 'NATGAS': (13.5/21.0)}
		# Values from https://gasengineering.nl/pdf/EC_POWER%20specs%20tijdelijk%20NL.pdf

		# How to read these values? Each 1 "quantity" of natural gas consumed produces 13.5/21.0 heat. Each 1 "quantity" of electricity consumed, produces -13.5/6.0 units of heat.
		# Note that electricity is produced, hence the negative sign, so each 1 produced electricity also produces 13.5/6.0 heat (obviously by consuming natural gas).

		self.heatProduction = 0.0 # This variable holds the heat production internally of the device

		self.capacity = 0.0
		self.soc = 0.0
		self.initialSoC = 0.0

		self.lowMark = 0
		self.highMark = 0

		self.producingTemperatures = [0.0, 60.0]	# Output power of the source

	def startup(self):
		ThermalBufConvDev.startup(self)

		assert(len(self.commodities) == 3)