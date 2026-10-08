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

from util.modelComposer import ModelComposer

composer = ModelComposer("touchtable")

# Generic components
composer.add("misc/components.py")
composer.add("settings/settings_demostreet.py")

# Add the simulation environment
composer.add("environment/simulator.py")

# Add global environment like the sun and weather
composer.add("environment/global.py")

# Start of the household composition
composer.add("house/connectedhouse.py")
composer.add("house/baseload.py")

# Add a neighbourhood controller
composer.add("street/streetcontrol.py")

# Now instantiate one house and add the startsimulation command
composer.add("networks/network_generator.py")

# make a composition of all these files and load it
composer.compose()
composer.load()
