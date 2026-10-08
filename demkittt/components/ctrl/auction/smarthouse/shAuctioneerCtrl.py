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

from ctrl.auction.auctioneerCtrl import AuctioneerCtrl


class ShAuctioneerCtrl(AuctioneerCtrl):
    def __init__(self,  name,  host):
        AuctioneerCtrl.__init__(self, name, host) #Parent is empty

        self.ohItem = None
        self.ohTarget = None
        self.ohMode = None
        
        self.ctrlMode = 1
            
    def clearMarket(self):    
        #read objectives from OpenHAB
        if self.ohCtrl != None:
            #see if we need islanding
            self.ctrlMode = int(self.host.getOpenHABItem(self.ohCtrl))
        
        if self.ctrlMode == 1:
            self.host.postOpenHABItem(self.ohItem, 0.2)
            self.nextAuction = self.host.time() + self.auctionInterval*self.timeBase 
            return #no control this interval
        
        if self.ctrlMode == 2:
            self.strictComfort = True
            self.islanding = False
            self.discreteBids = True
        if self.ctrlMode == 3:
            self.strictComfort = False
            self.islanding = True
            self.discreteBids = True
        
        if self.ohTarget != None:
            #see if we need islanding
            self.ctrlTarget = int(self.host.getOpenHABItem(self.ohTarget))
            
            self.maxGeneration = -self.ctrlTarget
            self.minGeneration = -self.ctrlTarget

        #Run the auction
        AuctioneerCtrl.clearMarket(self)
        
        #set the price
        if self.ohItem != None:
            #Price transformation
            p = 0.2 + (self.currentPrice / 10000.0)
            s = str.format("{:.2f}", p)
            self.host.postOpenHABItem(self.ohItem, s)
            
        self.logValue("target", self.ctrlTarget)  
        self.logValue("realprice", p)  
        
        #log some data to OpenHAB
 