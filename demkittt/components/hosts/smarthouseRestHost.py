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


from hosts.restHost import RestHost
from hosts.host import Host

from util.smarthouse import SmartHouseControl
from usrconf import *
import requests
import time as tm
from multiprocessing import Process

class SmarthouseRestHost(Host):
	def __init__(self, name="host", port = 5000, ohURL = 'http://localhost:8080'): #http://130.89.15.60:8080'): 
# 		Host.__init__(self, name)
		RestHost.__init__(self, name, port) 

		self.enablePersistence = False

		self.houseCtrl = None
		
		self.shBoards  = [0x0A0E123437, 0x19030A3738, 0x1405133437, 0x1f040a3738, 0x1B15043138]
		self.shPorts   = [0xC0, 0xC1, 0xC2]
		
		self.shDevices = {
            "TvBedroom":    	[0,0], #("board1", (0, None, None)),
            "LightLiving":      [0,1], #("board1", (1, None, None)),
            "LightBedroom":     [0,2], #("board1", (2, None, None)),
            
            "LightKidsUp":      [1,0], #("board2", (0, None, None)),
            "LightFrontLeftUp": [1,1], #("board2", (1, None, None)),
            "LightBathroomUp":  [1,2], #("board2", (2, None, None)),
        
            "LightBedroomDown": [2,0], #("board3", (0, None, None)),
            "TvLiving":         [2,1], #("board3", (1, None, None)),
            "LightToilet":      [2,2], #("board3", (2, None, None)),
        
            "LightKitchenBlue": [3,0], #("board4", (0, None, None)),
            "LightKitchenRed":  [3,1], #("board4", (1, None, None)),
            "LightKitchen":     [3,2], #("board4", (2, None, None)),
            
            "ShedRed":          [4,0], #("board5", (0, None, None)),
            "ShedBlue":         [4,1], #("board5", (1, None, None)),
            "ChargingPole":     [4,2]  #("board5", (2, None, None))
        }
		
		self.ohURL = ohURL
			
		self.ohTime = None	
		self.ohCtrl = None
		self.ohSeason = None
		
		self.minute = 0
		self.hour = 0	
		self.day = 0
		self.season = 1
		self.timeOffset = 0
			
		self.ctrlMode = 1
	
		self.cmdDevs = []
		self.cmdDevsprevious = []
		self.cmdOpenHAB = []
		self.cmdOpenHABprevious = []
		self.resOpenHAB = None

			
	def startup(self):
		#create an object to communicate data with the house
		self.houseCtrl = SmartHouseControl(smarthouseUsb)
	
		#wait for the complete system to boot
		self.bootAnimation()
		
		#get initial state of all openHAB items
		self.getAllOpenHAB()
		
		#start the socket
		RestHost.startup(self)		
		
	def timeTick(self, time, absolute = False):
		self.cmdOpenHABprevious = list(self.cmdOpenHAB)
		self.cmdDevsprevious = list(self.cmdDevs)
		
		try:
			self.houseCtrl.openPort()
		except:
			print("warning, problems encountered connecting to the device!")
		
		pDev = Process(target=self.setDeviceThread, args=(self.cmdDevsprevious,))
		pOH = Process(target=self.postOpenHABThread, args=(self.cmdOpenHABprevious,))
		pDev.start()
		pOH.start()

		self.cmdDevs = []
		self.cmdOpenHAB = []
		
		self.getAllOpenHAB()
				
		timeOfDay = self.currentTime%(60*60*24)
		self.day = int(self.currentTime%(60*60*24*7)/(60*60*24))
		self.hour = int(timeOfDay/3600)
		self.minute = int((timeOfDay%3600)/60)
			
		if  self.ohTime != None:
			h = str.format("{:02d}", self.hour)
			m = str.format("{:02d}", self.minute)
			s = str(h)+":"+str(m)
# 			print(s)
			self.postOpenHABItem(self.ohTime, str(s))
		
		# Do something with season here
		if self.ohSeason != None:
			self.season = int(self.getOpenHABItem(self.ohSeason))
			if self.season == 1: #winter
				self.timeOffset = 5*7*24*3600
			elif self.season == 2: #spring
				self.timeOffset = 18*7*24*3600
			elif self.season == 3: #summer
				self.timeOffset = 28*7*24*3600
			elif self.season == 4: #autumn
				self.timeOffset = 43*7*24*3600
		
		if self.ohCtrl != None:
			#see if we need islanding
			self.ctrlMode = int(self.getOpenHABItem(self.ohCtrl))
			
			if self.ctrlMode == 3:
				#Islanding
				for d in self.devices:
					d.strictComfort = False
				for c in self.controllers:
					c.strictComfort = False
					c.islanding = True
					c.discreteBids = True
			else:
				for d in self.devices:
					d.strictComfort = True
				for c in self.controllers:
					c.strictComfort = True
					c.islanding = False
					c.discreteBids = True
		
		#issue the normal timeTick
		RestHost.timeTick(self, time, absolute)
		
		#set everything in separate processes
		
# 		pOH.start()
		pDev.join()
		pOH.join()
		
		try:
			self.houseCtrl.closePort()
		except:
			print("warning, problems encountered connecting to the device!")

		Host.timeTick(self, time, absolute)
			
# Database

	def logValue(self,  measurement,  tags,  values, time=-1):
		if self.writeData:
			time = (self.minute*60) + (self.hour*3600)
			self.db.appendValue(measurement,  tags,  values, time)

	def logValuePrepared(self, data):
		time = (self.minute*60) + (self.hour*3600)
		self.db.appendValuePrepared(data, time)

#smarthouse functions		
	def setDevice(self, name, val):
		d = []
		d.append(name)
		d.append(val)
		self.cmdDevs.append(list(d))
	
	def setDeviceDirect(self, name, val):
		if name in self.shDevices:	
			try:
				d = self.shDevices[name]			
				self.houseCtrl.setDevice(self.shBoards[d[0]], self.shPorts[d[1]], val)
			except:		
				print("warning, problems encountered sending msg to device!")
		else:
			print("device with this name does not exist: "+name)

	def setDeviceDirectComplex(self, board, port, val):
		assert(False)
		try:
			self.houseCtrl.setDevice(board, port, val)
		except:		
			print("warning, problems encountered sending msg to device!")	

	def setDeviceThread(self, devs):
		for dev in devs:
			name = dev[0]
			val = dev[1]
			if name in self.shDevices:	
				try:
					d = self.shDevices[name]			
					self.houseCtrl.setDevice(self.shBoards[d[0]], self.shPorts[d[1]], val)
				except:		
					print("warning, problems encountered sending msg to device!")
			else:
				print("device with this name does not exist: "+name)
		
#OpenHAB message functions		
	def getOpenHAB(self, item):
		return requests.get(self.ohURL+'/rest/items/'+item+'/state').text
	
	def postOpenHAB(self, item, value):
		requests.post(self.ohURL+'/rest/items/'+item, data=str(value))
	
	def putOpenHAB(self, item, value):
		requests.put(self.ohURL+'/rest/items/'+item, data=str(value))

	def getOpenHABItem(self, item):
		for i in self.resOpenHAB:
			if i['name'] == item:
				return i['state']
	
	def getOpenHABItemDirect(self, item):
		return requests.get(self.ohURL+'/rest/items/'+item+'/state').text
	
	def getAllOpenHAB(self):
		self.resOpenHAB = requests.get(self.ohURL+'/rest/items').json()
	
	def postOpenHABItem(self, item, value):
		v = []
		v.append(item)
		v.append(value)
		self.cmdOpenHAB.append(list(v))
		
	def postOpenHABItemDirect(self, item, value):
		requests.post(self.ohURL+'/rest/items/'+item, data=str(value))
	
	def putOpenHABItem(self, item, value):
		requests.put(self.ohURL+'/rest/items/'+item, data=str(value))
		
	def postOpenHABThread(self, vals):
		for val in vals:
			item = val[0]
			value = val[1]
			requests.post(self.ohURL+'/rest/items/'+item, data=str(value))

# Sweet demo for startup :P	
	def bootAnimation(self):
		try:
			self.houseCtrl.openPort()
		except:
			print("warning, problems encountered connecting to the device!")
		
	#Make sure all is off	
		for d in self.shDevices.keys():
			self.setDeviceDirect(d, 0.0)
				
	#Initial animation
		for d in self.shDevices.keys():
			print(d)
	
			self.setDeviceDirect(d, 1.0)
			tm.sleep(0.1)
			self.setDeviceDirect(d, 0.0)
			tm.sleep(0.1)
			self.setDeviceDirect(d, 1.0)
			tm.sleep(0.1)
			self.setDeviceDirect(d, 0.0)
			tm.sleep(0.1)
		
			for i in range(0, 21):
				self.setDeviceDirect(d, i/20.0)
				tm.sleep(0.025)
		
	# Turn all off			
		for d in self.shDevices.keys():
			self.setDeviceDirect(d, 0.0)
		for d in self.shDevices.keys():
			self.setDeviceDirect(d, 0.0)		
			
	#Boot animation while waiting	
		startedOH = False
		startedInflux = False
		startedGrafana = False
		keepLooping = True
		
		blinkleds = ["ChargingPole", "TvLiving", "TvBedroom"]
		
		while keepLooping:	
			#Check for OpenHAB
			if not startedOH:
				try:
					r = requests.get('http://localhost:8080/basicui/app')
					if r.status_code == requests.codes.ok:
						print("OpenHAB started")
						startedOH = True
				except:
					print("Waiting for OpenHAB to start")
			
			#Check for InfluxDB
			if not startedInflux:
				try:
					r = requests.get('http://localhost:8086/')
					if r.status_code == 404:
						print("InfluxDB started")
						startedInflux = True
				except:
					print("Waiting for InfluxDB to start")
					
			if not startedGrafana:
				try:
					r = requests.get('http://localhost:3000/')
					if r.status_code == requests.codes.ok:
						print("Grafana started")
						startedGrafana = True
				except:
					print("Waiting for Grafana to start")

			if startedOH and startedInflux and startedGrafana:
				keepLooping = False
				break
			
			for d in blinkleds:
				if d == "ChargingPole" and not startedOH:
					self.setDeviceDirect(d, 0.0)
				elif d == "TvLiving" and not startedInflux:
					self.setDeviceDirect(d, 0.0)
				elif d == "TvBedroom" and not startedGrafana:
					self.setDeviceDirect(d, 0.0)
					
			tm.sleep(0.5)
			for d in blinkleds:
				self.setDeviceDirect(d, 1.0)
			tm.sleep(0.5)			
		
# 			for d in self.shDevices.keys():
# 				self.setDeviceDirect(d, 0.0)
# 			tm.sleep(1)
# 			for d in self.shDevices.keys():
# 				self.setDeviceDirect(d, 1.0)
# 			tm.sleep(1)
		
	#Clear the database
		self.clearDatabase()	
			
	# Slow fading out to ensure that all is stable at the end
		for i in range(0, 21):
			for d in self.shDevices.keys():		
				self.setDeviceDirect(d, (20.0-i)/20.0)
# 				tm.sleep(0.01)
				
		try:
			self.houseCtrl.closePort()
		except:
			print("warning, problems encountered connecting to the device!")
		
		