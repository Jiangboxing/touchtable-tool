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



from dev.device import Device

import time as tm
import socket
import queue
import threading

import math

# Buffer device
class LabBufDev(Device):
	def __init__(self,  name,  host, meter = None, ctrl = None):
		Device.__init__(self,  name,  host)
		self.devtype = "Buffer"
		
		#params
		self.capacity = 12000 #in Wh
		self.initialSoC = 6000 #in Wh
		self.soc = self.initialSoC #state of charge

		self.prevConsumption = 0.0
		
		#define 2 entries for a continuous range
		self.chargingPowers = [-2500, 2500]
		#self.chargingPowers = [-3680.0, -3450.0, -3220.0, -2990.0, -2760.0, -2530.0, -2300.0, -2070.0, -1840.0, -1610.0, -1380.0, 0.0, 1380.0, 1610.0, 1840.0, 2070.0, 2300.0, 2530.0, 2760.0, 2990.0, 3220.0, 3450.0, 3680.0]
		self.discrete = False
		
		self.lossOverTime = 0
		
		#Marks to trigger replanning
		self.lowMark = 1000
		self.highMark = 11000 
		self.flagLowMark = False
		self.flagHighMark = False
		
		#state
		self.selfConsumption = 0.0
		
		self.balancing = False

		# Fixed param, required to make the buffer and the bufferconverter compatible with similar control methods
		self.cop = 1.0
		
		self.parent = None
		if meter != None:
			self.balancing = True
			self.meter = meter
			if ctrl != None:
				self.parent = ctrl

		# Socket properties:
		self.sockport = 8089 #Define the port
		self.sockip = 'localhost'
		self.server = None
		self.connected = False
		self.conn = None

		# Battery Specs
		self.scalingFactor = 31.5 / 12000.0
		self.nomVoltage = 12.0

		self.current = 0
		self.maxCurrent = 0.6
		self.voltage = self.nomVoltage


	def startup(self):
		self.soc = min(self.initialSoC, self.capacity)
		self.chargingPowers.sort()

		if self.highMark > self.capacity:
			self.highMark = 0.9 * self.capacity
			self.logWarning("Predefined highmark not appropriate. I fixed this for you!")
		if self.lowMark >= self.highMark or self.lowMark < 0:
			self.lowMark = 0.1 * self.capacity
			self.logWarning("Predefined lowmark not appropriate. I fixed this for you!")

		#initialize flags
		if self.soc > self.highMark:
			self.flagHighMark = True
		elif self.soc < self.lowMark:
			self.flagLowMark = True

		for c in self.commodities:
			self.consumption[c] = complex(0.0, 0.0)

		# FIXME: GERWIN: I hardcoded some params here to make sure that they are set correctly for now (disregarding th eoverall model specs)
		self.chargingPowers = [-2500, 2500]
		self.scalingFactor = 31.5 / 12000.0
		self.nomVoltage = 12.0

		self.current = 0
		self.maxCurrent = 0.6
		self.voltage = self.nomVoltage

		# Open socket
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind((self.sockip, self.sockport))
		self.server.listen(1)

		self.connected = False

		print("Waiting for LabView to connect")
		while True:
			self.conn, addr = self.server.accept() # Wait till we have a connection
			self.conn.settimeout(1)
			break

		# Not using htreading now
		self.newThread = threading.Thread(target=self.socketThread, args=[])
		self.newThread.start()


	def socketThread(self):
		print("Thread started, listening for data")
		while True:
			try:
				cmnd = self.conn.recv(23)  # The default size of the command packet is 4 bytes
				print(cmnd)
			except socket.timeout:
				cmnd=''

			if '{v:' in str(cmnd):
				s = str(cmnd.decode())
				f = "{}:vc" # Filter
				for char in f:
					s = s.replace(char, "")
				s = s.split(";")

				v = s[0]
				c = s[1]
				# Prevent NL / US decimal errors
				v = v.replace(",", ".")
				c = c.replace(",", ".")

				try:
					self.voltage = float(v)
				except:
					print("Error in converting received voltage into a float for use")
					print(v)

				if self.voltage == 0:
					self.voltage = self.nomVoltage

				self.flag = True # Signal that a new value is available
				print("voltage read: "+str(self.voltage))

			elif 'INIT' in str(cmnd):
				# Do the initialization action
				self.conn.sendall(b'INIT-DONE')
				self.connected=True

				tm.sleep(1)
				self.conn.sendall(('{C:0.000000;D:0.000000}').encode())
			elif 'QUIT' in str(cmnd):
				# Do the quiting action
				self.connected=False
				self.conn.sendall(b'QUIT-DONE')
				break

		# If all breaks, disconnect and close the server
		self.server.close()

	def preTick(self, time):
		consumption = 0
		for c in self.commodities:
			consumption += self.consumption[c].real
		
		#First update the SoC
		self.soc += consumption * (self.host.timeBase / 3600.0)
		self.soc -= self.selfConsumption * (self.host.timeBase / 3600.0)
		
		#now make sure that we are still in the SoC constraints:
		self.soc = min(self.capacity, max(self.soc, 0))
		
		#avoid weird rounding stuff:
		if self.soc >= self.capacity*0.99999:
			self.soc = self.capacity

		self.checkFillMarks()

	
	def timeTick(self,  time):			
		self.prunePlan()
		
		#Add the self-consumption properly
		self.selfConsumption = self.lossOverTime

		totalConsumption = 0

		# Normal operation with a controller
		if not self.balancing:

			for c in self.commodities:
				if c in self.plan and len(self.plan[c]) > 0:
					self.consumption[c] = complex(self.plan[c][0][1].real, 0.0)
				else:
					self.consumption[c] = complex(0.0, 0.0)
				totalConsumption += self.consumption[c].real


		# Special operation through a link with the smart meter where the battery tries to balance the system
		else:
			target = 0.0
			if self.parent != None:
				for c in self.commodities:
					# read out the global plan of a groupcontroller to adjust the target
					target += int(self.parent.getPlan(self.host.time(), c))

			load = 0.0
			if type(self.meter) is list:
				for m in self.meter:
					m.measure(self.host.time())
					load += m.consumption.real
			else:
				self.meter.measure(self.host.time())
				load = self.meter.consumption.real

			bufPower = 0.0
			for c in self.commodities:
				bufPower += self.consumption[c].real
			#and thus, the next power to balance is:
			desired = int(bufPower + (target - load))
			consumption = max(((-self.soc)/(self.host.timeBase/3600.0)),  min(desired,  ((self.capacity-self.soc)/(self.host.timeBase/3600.0)) ) )
			# Now set the consumption, divide over commodities:
			for c in self.commodities:
				self.consumption[c] = max(self.chargingPowers[0], min(consumption / float(len(self.commodities)), self.chargingPowers[-1]))


		# buffer underrun / overflow check and make the device fix this!
		if ((self.soc * (3600.0 / self.host.timeBase) + totalConsumption + self.selfConsumption) * (self.host.timeBase / 3600.0)) > self.capacity:
			#We have a buffer overflow:
			reduceBy = (((self.soc * (3600.0 / self.host.timeBase) + totalConsumption + self.selfConsumption) * (self.host.timeBase / 3600.0)) - self.capacity) / (self.host.timeBase / 3600.0) / len(self.commodities)
			for c in self.commodities:
				self.consumption[c] = max(self.chargingPowers[0], min(self.consumption[c].real-reduceBy, self.chargingPowers[-1]))

		elif ((self.soc * (3600.0 / self.host.timeBase) + totalConsumption + self.selfConsumption) * (self.host.timeBase / 3600.0)) < 0.0:
			#We have a buffer underflow:
			increaseBy = ((abs(self.soc * (3600.0 / self.host.timeBase) + totalConsumption + self.selfConsumption) * (self.host.timeBase / 3600.0))) / (self.host.timeBase / 3600.0) / len(self.commodities)
			for c in self.commodities:
				self.consumption[c] = max(self.chargingPowers[0], min(self.consumption[c].real+increaseBy, self.chargingPowers[-1]))

		for c in self.commodities:	
			#add optional reactive power	
			if c in self.plan and len(self.plan[c]) > 0:
				if self.consumption[c].real < self.chargingPowers[-1]:
					qmax = math.sqrt((self.chargingPowers[-1]*self.chargingPowers[-1]) - (self.consumption[c].real*self.consumption[c].real))
					self.consumption[c] += complex(0.0, max(-1*qmax, min(self.plan[c][0][1].imag, qmax)))



		# SENDING DATA TO LABVIEW
		try:
			self.current = (self.consumption['ELECTRICITY'].real / self.voltage) * self.scalingFactor
		except:
			print("Error, wrong voltage")
			self.voltage = self.nomVoltage
			self.current = (self.consumption['ELECTRICITY'].real / self.voltage) * self.scalingFactor

		# Send the data to the socket:
		if self.connected:
			value = self.current
			charge = 0.0
			discharge = 0.0

			# Diego, set the current here, negative is discharging
			# value = -0.3
			if value > 0:
				charge = value
				charge = min(charge, self.maxCurrent)
			else:
				discharge = abs(value)
				discharge = min(discharge, self.maxCurrent)

			data = '{C:'+format(charge, '.3f').replace(".", ",")+';D:'+format(discharge, '.3f').replace(".", ",")+'}'
			print("sending back: "+data)
			self.conn.sendall((data).encode())


	def logStats(self, time):
		try:
			for c in self.commodities:
				self.logValue("W-power.real.c." + c, self.consumption[c].real)
				self.logValue("W-power.imag.c." + c, self.consumption[c].imag)
				if c in self.plan and len(self.plan[c]) > 0:
					self.logValue("W-power.plan.real.c."+c, self.plan[c][0][1].real)
					self.logValue("W-power.plan.imag.c."+c, self.plan[c][0][1].imag)
		except:
			pass

		self.logValue("Wh-energy.soc", self.soc)
		self.logValue("W-power.real.secondary", self.selfConsumption)
		self.logValue("b-available", 1)

		for c in self.commodities:
			self.logValue("W-powerScaled.real.c." + c, self.consumption[c].real * self.scalingFactor)
		self.logValue("Wh-energyScaled.soc", self.soc * self.scalingFactor)
		self.logValue("V-voltage", self.voltage)
		self.logValue("V-current", self.current)

		
	def shutdown(self):
		pass

	def checkFillMarks(self):
		#request for a replanning on marks and (re)set the flags accordingly
		if self.controller is not None:
			#test for marks and set flags accordingly
			if self.soc <= self.lowMark and self.flagLowMark == False:
				self.zCast(self.controller, 'triggerEvent', "stateUpdate")
				self.flagLowMark = True
			if self.soc >= self.highMark and self.flagHighMark == False:
				self.zCast(self.controller, 'triggerEvent', "stateUpdate")
				self.flagHighMark = True

			#Reset the flags
			if self.flagHighMark == True and self.soc < self.highMark:
				self.flagHighMark = False
			if 	self.flagLowMark == True and self.soc > self.lowMark:
				self.flagLowMark = False

#### INTERFACING
	def getProperties(self):
		r = Device.getProperties(self) 	# Get the properties of the overall Device class, which already includes global properties

		# Populate the result dict
		r['soc'] = self.soc
		r['cop'] = self.cop
		r['capacity'] = self.capacity
		r['chargingPowers'] = self.chargingPowers
		r['selfConsumption'] = self.selfConsumption
		r['discrete'] = self.discrete
		return r
				
