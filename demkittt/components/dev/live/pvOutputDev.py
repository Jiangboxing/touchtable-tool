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


from dev.curtDev import CurtDev

from util.influxdbReader import InfluxDBReader

from bs4 import BeautifulSoup
import requests

class PvOutputDev(CurtDev):
	def __init__(self,  name,  host, influx=True, reader=None):
		CurtDev.__init__(self,  name,  host, influx, reader)
		
		self.devtype = "Curtailable"

		self.url = "https://pvoutput.org/intraday.jsp?id=28320&sid=25938"
		# By default, we take a nice array of panels in Enschede
		# The url should point to a Live page (intraday) of a solar panel setup

		# Update rate:
		self.lastUpdate = -1
		self.updateInterval = 300


	def startup(self):
		CurtDev.startup(self)

	# FIXME: Make async
	def preTick(self, time):
		self.lockState.acquire()
		# We should not be a bad citizen to the service
		if (self.host.time() - self.lastUpdate)  > self.updateInterval:
			try:
				r = requests.get(self.url)
				if r.status_code != 200:
					self.logWarning("Could not connect to PVOutput. Errorcode: "+str(r.status_code)+ "\t\t" + r.text)

				data = r.text

				# Now retrieve the data we'd like:
				soup = BeautifulSoup(data, 'html.parser')
				value = soup.find(id="dashPowerOut").text
				value = value.replace("," , "") # Fix decimals
				value = value.replace("." , "")
				value = -1 * float(value) * self.scaling

				# Now, value contains the power production by the pv setup, now we can set it as consumption:
				for c in self.commodities:
					self.consumption[c] = complex(value / len(self.commodities), 0.0)

				# If all succeeded:
				self.lastUpdate = self.host.time()
			except:
				self.logWarning("PVOutput service error")

		self.lockState.release()