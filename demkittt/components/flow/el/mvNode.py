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

from flow.el.elNode import ElNode

class MvNode(ElNode):
    def __init__(self,  name,  flowSim, host):
        ElNode.__init__(self,  name,  flowSim, host)
        
        self.devtype = "ElectricityMediumVoltageCable"
        
        self.hasNeutral = False
        
        #params
        self.nominalVoltage = [0.0, 6062.0, 6062.0, 6062.0] # 10.5V phase to phase
        self.angles = [0.0, 0.0, -120, 120]
        
        #limits
        self.maxVoltage = 6062.0*1.1
        self.minVoltage = 6062.0*0.9
        self.maxVuf = 2.0 # %
