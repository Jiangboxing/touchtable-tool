#!/usr/bin/python3

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


import sys, os, getopt, requests, time, importlib

print("\n\n")
print("                              yd.                                                                                       ")
print("                            `dMMN-                                                                                      ")
print("                           .mMMMMN:                                                                                     ")
print("                          -NMMMMMMM+                                                                                    ")
print("                         :NMMMMMMMMMo                                                                                   ")
print("                        +MMMMMMMMMMMMy`               .ddddddddddddddddddddd+                                           ")
print("                       oMMMMMMMMMMMMMMh`              .MMMMMMMMMMMMMMMMMMMMMo                                           ")
print("                     `yMMMMMMMMMMMMMMMMd.             .MMMm-------------sMMMo                                           ")
print("                    `/hhhhhhhhhhhhhhhhhho.............:MMMm.............sMMMs..........................................`")
print("                   .ho+++++++++++++++++++++++++++++++++oooo+++++++++++++ooooo+++++++++++++++++++++++++++++++++++++++++m/")
print("                  -d+        `/ssssssssssss/           :ossssssssssssssssss+`  `/s+.             .+s/   .`            m/")
print("                 :d/         /MMMMMMMMMMMMMMs`        .MMMMMMMMMMMMMMMMMMMMM/  /MMMmo.         .sNMMM- +my            m/")
print("                /d-          /MMMd+++++++dMMMy`       .MMMm++++++++++++++++/`  /MMMMMmo.     .oNMMMMM: sMm``````````  m/")
print("               od.           /MMMs       `yMMMh.      .MMMd                    /MMMNMMMmo. .omMMMNMMM: sMMmmmmmmmmmd` m/")
print("             `sh`            /MMMs        `sMMMd.     .MMMd                    /MMMy/dMMMmymMMMd/hMMM: sMm:::::::::-  m/")
print("            `yy`             /MMMs          oMMMm-    .MMMd                    /MMMs `+mMMMMMd/` yMMM: sMd            m/")
print("           .hs               /MMMs           +NMMN:   .MMMd                    /MMMs   `+dmd/`   yMMM: ./-            m/")
print("          `do                /MMMs            /NMMN/  .MMMm////////////////-   /MMMs      `      yMMM: :hhhhhhhhhhhy  m/")
print("         :+yh`               /MMMs             /MMMM- .MMMMMMMMMMMMMMMMMMMMM/  /MMMs             yMMM: .ooooooooooo+  m/")
print("        +MMssd.              /MMMs            .dMMMs  .MMMNyyyyyyyyyyyyyyyyo`  /MMMs             yMMM:           -so  m/")
print("       oMMMMhod-             /MMMs           -mMMMo   .MMMd                    /MMMs             yMMM: -s/`    .yNNs  m/")
print("     `yMMMMMMd+m:            /MMMs          :NMMN+    .MMMd                    /MMMs             yMMM: -dMd/`.yNNs.   m/")
print("    `hMMMMMMMMm+m/           /MMMs         +MMMN:     .MMMd                    /MMMs             yMMM:   /mMmNMy.     m/")
print("   .dMMMMMMMMMMN+d+          /MMMs        oMMMm-      .MMMd                    /MMMs             yMMM: .+++dMMm++++/  m/")
print("  -mMMMMMMMMMMMMN+ds         /MMMy.......yMMMd.       .MMMm................`   /MMMs             yMMM: /dddddddddddh` m/")
print(" :NMMMMMMMMMMMMMMMohy`       /MMMMMMMMMMMMMMh`        .MMMMMMMMMMMMMMMMMMMMN:  /MMMs             yMMM:                m/")
print(".mmmmmmmmmmmmmmmmmm/shyyyyyo `ymmmmmmmmmmmms           smmmmmmmmmmmmmmmmmmmh.  .hmh-             :dmy` -yyyyyyyyyyyyyyd:")
print(" ")
print("________________________________________________________________________________________________________________________\n")
print('DEMKit version 2020.1.beta\n')
print('Copyright (C) 2019 Computer Architecture for Embedded Systems and Mathematics of Operations Research groups,\n'
	  'Department of Electrical Engineering, Mathematics and Computer Science, '
	  'University of Twente, Enschede, the Netherlands')
print('This program comes with ABSOLUTELY NO WARRANTY.')
print('See the acompanying license for more information.')
print("________________________________________________________________________________________________________________________\n")

if(len(sys.argv) > 1):
	# Change working directory to script directory
	os.chdir(os.path.dirname(os.path.realpath(__file__)))

	#Load the user config
	sys.path.insert(0, 'conf')
	from usrconf import *

	try:
		if cfgVer != 3:
			print("Incorrect configuration version found. Make sure to have a proper conf/usrconf.py file! Please refer to the provided exanple.")
			exit()
		
		# Add trailing slash
		if componentPath[-1] != '\\' and componentPath[-1] != '/':
			componentPath += '/'
		if workspacePath[-1] != '\\' and workspacePath[-1] != '/':
			workspacePath += '/'
	except:
		print("Errors occured when loading the configuration file. Make sure to have a proper conf/usrconf.py file! Please refer to the provided exanple.")
		exit()

	print('pyDEM directory: '+componentPath)
	print('User model directory: '+workspacePath)

	#Load the DEM platform
	sys.path.insert(0, componentPath)
	
	modelPath = workspacePath
	modelName = ""
	
	#Get arguments:
	try:
		opts, args = getopt.getopt(sys.argv[1:],"f:m:n:s:u",["folder=","model=","number=","socket=","smarthouseusb="])
	except getopt.GetoptError:
		print("Usage:")
		print('demkit.py -f <folder> -m <model> [-d <database>] [-n <number>] [-s <socket>] [-u <smarthouseusb>]')
		sys.exit(2)
	
	#Parse arguments
	for opt, arg in opts:
		if opt in ("-f", "--folder"):
			if((arg[:1] == "/") or (arg[:2] == "~/")):
				modelPath = arg
			else:
				modelPath += arg
		elif opt in ("-m", "--model"):
			modelName = arg
		elif opt in ("-d", "--database"):
			influxDB = arg
		elif opt in ("-s", "--socket"):
			sockPath = arg
		elif opt in ("-u", "--smarthouseusb"):
			smarthouseUsb = arg
	
	print('Loading model: '+modelName+' from '+modelPath)
		
	#import the model path
	sys.path.insert(0, modelPath)

	#change the working directory to the model directory
	os.chdir(modelPath)

	#Load the desired model
	importlib.import_module(modelName)

	
else:
	print("Usage:")
	print('demkit.py -f <folder> -m <model> [-d <database>] [-c] [-s <socket>] [-u <smarthouseusb>]')
