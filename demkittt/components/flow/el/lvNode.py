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

class LvNode(ElNode):
    def __init__(self,  name,  flowSim, host):
        ElNode.__init__(self,  name,  flowSim, host)
        
        self.devtype = "ElectricityLowVoltageNode"
        
        self.hasNeutral = True
        
        #params
        self.nominalVoltage = [0.0, 230.0, 230.0, 230.0]      
        self.angles = [0.0, -150.0, 90.0, -30.0]
        
        #limits
        self.maxVoltage = 230.0*1.1
        self.minVoltage = 230.0*0.9
        self.maxVuf = 2
