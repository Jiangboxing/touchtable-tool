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



from ctrl.bufCtrl import BufCtrl
from ctrl.auction.bufAuctionCtrl import BufAuctionCtrl

# TimeShiftable controller
class PaBufCtrl(BufCtrl, BufAuctionCtrl):
	def __init__(self,  name,  dev,  ctrl,  host):
		BufAuctionCtrl.__init__(self,  name, None, None, None)
		BufCtrl.__init__(self,   name,  dev,  ctrl,  host)

		self.useEventControl = False
		
		self.devtype = "BufferController"
	
	def preTick(self, time):
		BufCtrl.preTick(self, time)
		BufAuctionCtrl.preTick(self, time)	
		
	def timeTick(self, time):
		BufCtrl.timeTick(self, time)
		BufAuctionCtrl.timeTick(self, time)	