#!/usr/bin/python3

from dev.btsDev import BtsDev

import random

class TtBtsDev(BtsDev):
	def __init__(self, name, host):
		BtsDev.__init__(self, name, host)
		self.timeOffset = 0

	def preTick(self, time):
		if self.soc > self.capacity:
			self.soc = self.capacity

		# print(self.name, self.chargingPowers)

		# HERE
		newJob = False
		if not self.available:
			if self.host.timeObject().hour > 6 and self.host.timeObject().hour < 17:
				if random.randint(0, 60) < 2:
					newJob = True
			elif self.host.timeObject().hour >= 17 and self.host.timeObject().hour < 23:
				if random.randint(0, 60) < 8:
					newJob = True

		# Add a job
		if newJob:
			self.jobs = []
			self.currentJob = []
			self.currentJobIdx = -1

			charge = random.randint(int(self.capacity * 0.4), int(self.capacity*0.9))
			endTime = max(self.host.time() + 4500 + int((self.chargingPowers[-1]/charge)*3600), self.host.time() + random.randint(8*3600, 12*3600))
			self.addJob(self.host.time(), endTime, charge)

		BtsDev.preTick(self, time)

	def setProperties(self, evType):
		pass