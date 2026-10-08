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

#!/usr/bin/python3

# Just a small test script to see if demand functions are doing what we expect them to do
# THIS IS NOT A UNITTEST
print("hi world")

from demandFunction import DemandFunction

f1 = DemandFunction()
f1.addPoint(1000, -1000)
f1.addPoint(100, 0)
f1.addPoint(0, 1000)
print("print") 
print(f1.function)

print(f1.demandForPrice(-1000))
print(f1.demandForPrice(0))
print(f1.demandForPrice(1000))
print(f1.demandForPrice(400))
print("P4D")
print(f1.priceForDemand(1000))
print(f1.priceForDemand(60))
print(f1.priceForDemand(0))

f2 = DemandFunction()
f2.addLine(3700, 1380, -1000, 400)
f2.addLine(0, 0, 401, 1000)
print("print") 
print(f2.function)

print(f2.demandForPrice(-1000))
print(f2.demandForPrice(0))
print(f2.demandForPrice(1000))
print(f2.demandForPrice(400))

f1.addFunction(f2)
print(f1.function)



f2 = DemandFunction()
f2.addPoint(0, 0)
print("print") 
print(f2.function)

print(f2.demandForPrice(-1000))
print(f2.demandForPrice(0))
print(f2.demandForPrice(1000))
print(f2.demandForPrice(400))

f2.resetFunction()
print(f2.function)

f2 = DemandFunction()
f2.addLine(3700, 1380, -800, 400)
f2.addLine(0, 0, 401, 800)
print("print") 
print(f2.function)

print(f2.demandForPrice(-1000))
print(f2.demandForPrice(0))
print(f2.demandForPrice(1000))
print(f2.demandForPrice(400))

f2.resetFunction()
print(f2.function)

f2.addLine(1,1,-1000, 1000)
print(f2.surface())

f3 = DemandFunction()
f3.addLine(2,2,-1000, 0)
f3.addLine(0,0,1, 1000)
print(f3.surface())
print(f2.difference(f3))
