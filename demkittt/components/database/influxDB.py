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
import time as tm
from usrconf import *
import os
import threading

class InfluxDB():
	def __init__(self, host):
		self.host = host

		self.address = influxUrl
		self.port = influxPort
		self.database = influxDB
		self.prefix = ""

		self.username = ""
		self.password = ""

		
		self.data = ""
		self.maxBuffer = 500000

		self.storeBackup = False 	# Store data by default in a backup file
		self.restoreBackup = True	# Restore backup when connection to DB is restored
		self.autoCleanup = True 	# Cleanup text files when data is restored after a hiccup
		self.errorFlag = False
		self.filepath = 'data/'+host.name+'/influxDB/' # Location to store the backup

		self.useSysTime = False # Use system time instead of host time

		self.restoring =threading.Lock()
		
	def appendValue(self,  measurement, tags,  values,  time):
		#create tags
		tagstr = ""
		for key,  value in tags.items():
			if not tagstr == "":
				tagstr += ","
			tagstr += key + "="+value
			
#		create vals	
		valsstr = ""
		for key,  value in values.items():
			if not valsstr == "":
				valsstr += ","
			valsstr += key+ "="+str(value)
		
		# Check the time
		timestr = str(int(time * 1000000000.0))
		if self.useSysTime:
			time = str(tm.time())
			timestr = time.replace('.', '')
			timestr += "000"
		
		s = self.prefix + measurement + ","	
		s += tagstr + " "
		s += valsstr + " "	
		s += timestr
		s += '\n'
		
		self.data += s

	def appendValuePrepared(self,  data, time):
		timestr = str(int(time * 1000000000.0))
		if self.useSysTime:
			time = str(tm.time())
			timestr = time.replace('.', '')
			timestr += "000"
		self.data += self.prefix + data + " " + timestr + "\n"

	def writeData(self,  force = False):
		if len(self.data) > self.maxBuffer or force:
			success = self.writeToDatabase(self.data)

			if not success or self.storeBackup:
				self.writeTextFile()

				if not success:
					self.errorFlag = True

			# Clear cache
			self.data = ""

			if success:
				if self.errorFlag:
					# Connection to database is established again, lets load from the text files
					if self.restoring.acquire(blocking=False):
						self.host.runInThread(self, 'loadTextFiles') #self.loadTextFiles()



	def writeToDatabase(self, data):
		result = True
		try:
			r = requests.post(self.address+ ':'+self.port+ '/write?db='+self.database,  auth=(self.username, self.password), data=data)
			if r.status_code != 204:
				if not self.errorFlag:
					print("ERROR: [InfluxDB] Could not write to database. Errorcode: "+str(r.status_code)+ "\t\t" + r.text)
				result = False

		except:
			if not self.errorFlag:
				print("ERROR: [InfluxDB] Could not connect to database, is it running?")
			result = False

		return result


	def clearDatabase(self):
		print("clearing database "+self.database)
		payload = {'q':"DROP DATABASE "+self.database}
		try:
			r = requests.post(self.address+ ':'+self.port+ '/query',  auth=(self.username, self.password), data=payload)
			if r.status_code != 200:
				print("WARNING: [InfluxDB] Could not drop the database. Check your InfluxDB. Errorcode: "+str(r.status_code)+ "\t\t" + r.text)
		except:
			print("WARNING: [InfluxDB] Could not connect to database, is it running?")

		print("removing backup files")
		self.cleanupTextFiles()

		print("creating database " + self.database)
		self.createDatabase()

	def createDatabase(self):
		payload = {'q': "CREATE DATABASE " + self.database}
		try:
			r = requests.post(self.address + ':' + self.port + '/query',  auth=(self.username, self.password), data=payload)
			if r.status_code != 200:
				print("WARNING: [InfluxDB] Could not create the database. make sure that it does not start with numbers and does not contain dashes. Errorcode: "+str(r.status_code)+ "\t\t" + r.text)
		except:
			print("WARNING: [InfluxDB] Could not connect to database, is it running?")






	def writeTextFile(self):
		# Writing into files based on the date, YYYYMMDD:
		name = self.host.timeObject().astimezone(self.host.timezone).strftime("%Y%m%d")
		self.filename = self.filepath+name+'.dem'

		try:
			os.makedirs(os.path.dirname(self.filename), exist_ok=True)
			f = open(self.filename, 'a')
			f.write(self.data)
			f.close()
		except:
			print("WARNING: [InfluxDB] Could not find or create backup file: "+self.filename)

	# FIXME Make async?
	def loadTextFiles(self):
		# First see if we have files to load
		if self.restoreBackup:
			self.createDatabase()

			print("MESSAGE: [InfluxDB] Connection available, restoring backups")

			try:
				# Open each file
				folder = os.listdir(self.filepath)
				for filename in folder:

					# Handle each file
					if os.path.isfile(self.filepath+filename):
						f = open(self.filepath+filename, 'r')

						# Read file and write when the size exceeds the size
						data = ""
						for line in f:
							data += line
							if len(data) > self.maxBuffer:
								self.writeToDatabase(data)
								data = ""

						# Flush the last part
						self.writeToDatabase(data)
						data = ""
						f.close()

						# After all data is written, let's delete the file if required
						if self.autoCleanup:
							os.remove(self.filepath+filename)

				# Finally, we can remove the error flag
				self.errorFlag = False

				print("MESSAGE: [InfluxDB] Backups restored")

				self.restoring.release()

			except:
				print("WARNING: [InfluxDB] Could not resore backups")

	def cleanupTextFiles(self):
		if self.autoCleanup:
			try:
				# Open each file
				folder = os.listdir(self.filepath)
				for filename in folder:
					if os.path.isfile(self.filepath+filename):
						os.remove(self.filepath+filename)
			except:
				print("ERROR: [InfluxDB] Could not remove files")