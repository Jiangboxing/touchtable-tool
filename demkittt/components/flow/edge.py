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

from flow.flowEntity import FlowEntity

class Edge(FlowEntity):
    def __init__(self,  name,  flowSim, nodeFrom, nodeTo, host):
        FlowEntity.__init__(self,  name, host)
        
        self.devtype = "edge" 
        self.flowSim = flowSim
        
        #register this edge to the flowSim and host
        self.flowSim.edges.append(self)
        
        self.nodes = []
        self.nodes.append(nodeFrom)
        self.nodes.append(nodeTo)
        
        nodeFrom.edges.append(self)
        nodeTo.edges.append(self)
        
    def startup(self):
        self.reset()
        
    def shutdown(self):
        pass    
    
    def reset(self, restoreGrid = True):
        pass   
    
    def logStats(self, time):
        pass
    
    def otherNode(self, node):
        assert(len(self.nodes) == 2)
        if self.nodes[0] == node:
            return self.nodes[1]
        else:
            return self.nodes[0]