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

import pickle

import os
import copy

class Persistence():
	def __init__(self, entity, host, watchlist = None, format = "pickle", filename = None, append = None):
		self.entity = entity	# The entity to watch
		self.host = host		# The host it is attached to

		self.watchlist = watchlist		# list of variables to watch

		# Storage format
		self.format = format	# "pickle" , may add support for e.g. json in the future

		# Storage
		if filename is None:
			if append is None:
				self.filename = 'persistence/'+host.name+'/'+entity.name+'.dem'
			else:
				self.filename = 'persistence/'+host.name+'/'+entity.name+'/'+append+'.dem'
		else:
			self.filename = filename



		#self.init()

	def init(self):
		try:
			os.makedirs(os.path.dirname(self.filename), exist_ok=True)
			if not os.path.exists(self.filename):
				# Write an empty shell
				data = { } # Write only the time of recording

				f = open(self.filename, 'wb')
				pickle.dump(data, f)
				f.close()
		except:
			self.host.logError("Could not find or create persistence file: "+self.filename)

	def load(self, maxAge = None):
		if self.watchlist != None:
			if os.path.exists(self.filename):
				try:
					f = open(self.filename, 'rb')
					data = pickle.load(f)
					f.close()

					# Now load the data
					# Checking the time first
					if maxAge != None and 'time' in data:
						if data['timestamp'] < self.host.time() - maxAge:
							# data is too old, return
							return False

					# now scroll through the watchlist and restore variables
					for var in self.watchlist:
						try:
							if var in data:
								setattr(self.entity, var, copy.deepcopy(data[var]) ) # Deepcopy to make sure that all data is preserved. Object references are not supported!
						except:
							self.host.logWarning("Could not restore variable: "+var)
					return True # Notify that the persistence is executed

				except:
					self.host.logWarning("Could not open persistence file: "+self.filename)
					return False

	def save(self):
		if self.watchlist != None:
			try:
				os.makedirs(os.path.dirname(self.filename), exist_ok=True)
				f = open(self.filename+'.tmp', 'wb')

				data = {}
				for var in self.watchlist:
					if hasattr(self.entity, var):
						data[var] = copy.deepcopy(getattr(self.entity, var))
					else:
						self.host.logWarning("Could not save variable: "+var)

				# Write data in the tmp file
				pickle.dump(data, f)
				f.close()

				# Now move (and overwrite) the old file to avoid corruption:
				os.rename(self.filename+'.tmp', self.filename)

			except:
				self.host.logWarning("Could not save persistence file: "+self.filename)
				return False

	def setWatchlist(self, watchlist):
		self.watchlist = list(watchlist)