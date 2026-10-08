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


import requests

from dev.loadDev import LoadDev

class HassLoadDev(LoadDev):
	def __init__(self,  name,  host, influx=False, reader=None):
		LoadDev.__init__(self, name, host, influx, reader)

		self.url = "https://localhost:8123"
		self.bearer = ""
		self.sensor = "sensor.total_power" # Sensor name as known to Home Assistant

		# Update rate:
		self.lastUpdate = -1
		self.updateInterval = 1 # Update every minute

		# see https://developers.home-assistant.io/docs/en/external_api_rest.html

	# Fixme make async
	def preTick(self, time):
		# We should not be a bad citizen to the service
		self.lockState.acquire()
		if (self.host.time() - self.lastUpdate)  > self.updateInterval:
			try:
				value = 0.0 # Jus tto be sure if all fails

				# Try to get the sensor information
				url = self.url+"/api/states/"+self.sensor
				headers = {
					'Authorization': 'Bearer '+self.bearer,
					'content-type': 'application/json',
				}

				# Try to access the data
				r = requests.get(url, headers=headers)
				if r.status_code != 200:
					self.logWarning("Could not connect to Home Assistant. Errorcode: "+str(r.status_code)+ "\t\t" + r.text)

				data = r.json()

				# Now retrieve the data we'd like:
				value = data['state']
				value = value.replace("," , ".") # Fix decimals
				value = float(value) * self.scaling

				# Now, value contains the power production by the pv setup, now we can set it as consumption:
				for c in self.commodities:
					self.consumption[c] = complex(value / len(self.commodities), 0.0)

				# If all succeeded:
				self.lastUpdate = self.host.time()
			except:
				self.logWarning("Home Assistant service error")

		self.lockState.release()