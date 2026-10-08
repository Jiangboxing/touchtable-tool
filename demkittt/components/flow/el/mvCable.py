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

from flow.el.elCable import ElCable

class MvCable(ElCable):
    def __init__(self,  name,  flowSim, nodeFrom, nodeTo, host):
        ElCable.__init__(self,  name, flowSim, nodeFrom, nodeTo, host)
        
        self.devtype = "ElectricityMediumVoltageCable"
        self.hasNeutral = False
        
        # Mutual impedances of cables, are described in:
        # Reference: "Netten voor distributie van electriciteit" by Phase to Phase, 2012, section 8.2.8
		# https://phasetophase.nl/boek/index.html

        # Proper values can be obtained through the Types.xlsx file provided with the Gaia Demo download
        # The software, by Phase to Phase, can be obtained at: https://phasetophase.nl/vision-lv-network-design.html

        # The following values serve as an example
        self.impedance = [complex(0.18, 0.81), complex(0.045, 0.72), complex(0.05, 0.72), complex(0.05, 0.72)]
        
        self.length = 500    #in meters
        self.ampacity = 455  #amperes
        self.fuse = 0        #additional limit
        
