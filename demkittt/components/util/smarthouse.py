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

#Based on code by Hermen Toersche
  
import binascii
import functools
import serial
import struct
import sys
import time


class SmartHouseControl():
    def __init__(self, dev):
        self.dev = dev
    
        # MCU network.c:134
        # RETURN_NODE_ID | COMMAND | Target | (DATA)
        # 5 Byte         | Byte    | Byte   | 6 Bytes  (left-hand byte is "client ID")
        self.PACKET_LENGTH = 5 + 2 + 1 + 5
        
        self.boards  = {"board1": 0x0A0E123437, "board2": 0x19030A3738, "board3": 0x1405133437, "board4": 0x1f040a3738, "board5": 0x1B15043138}
        
        # SmartController.ini mapping is completely broken
        self.devices = {
            "LightBackroom":    ("board1", (0, None, None)),
            "LightLiving":      ("board1", (1, None, None)),
            "LightBedroom":     ("board1", (2, None, None)),
            
            "LightKidsUp":      ("board2", (0, None, None)),
            "LightFrontLeftUp": ("board2", (1, None, None)),
            "LightBathroomUp":  ("board2", (2, None, None)),
        
            "LightBedroomDown": ("board3", (0, None, None)),
            "TvLiving":         ("board3", (1, None, None)),
            "LightToilet":      ("board3", (2, None, None)),
        
            "LightKitchenBlue": ("board4", (0, None, None)),
            "LightKitchenRed":  ("board4", (1, None, None)),
            "LightKitchen":     ("board4", (2, None, None)),
            
            "ShedRed":          ("board5", (0, None, None)),
            "ShedBlue":         ("board5", (1, None, None)),
            "ChargingPole":     ("board5", (2, None, None))
        }
        
        # Based on commandset.h
        # In MCU network.c:221, these are known as the "target" field content
        # Note that voltageSensors are often referred to just as sensors
        self.ports           = [0xC0, 0xC1, 0xC2]
        self.targets = self.ports
        
        self.fd = None
        self.maxTries = 3
        
        # Message types
        self.MSG_NoType           = 0x0E
        self.MSG_SetPWMValue      = 0x01  #   1 byte duty cycle in percent: 0..100
        self.MSG_EventTriggered   = 0xFE  # < 3 bytes: type from SENSOREVENT_* [1b] | value [2b MSG first]
        self.MSG_OK               = 0x00
        self.MSG_ERROR            = 0xFF
        # *) expect return message (errors still trigger messages; with (almost) same content?)
    
        self.statusMessages = []
       
    def setDevice(self, board, target, val):
        cnt = 0
        while cnt < self.maxTries:
            cnt += 1
            r = self.setState(board, target, val)
            time.sleep(0.01) #make sure that we dont't push the system over the limit
            if r == 0:
                break #all ok
       
    def openPort(self):
        self.fd = serial.Serial(self.dev, 115200, timeout=0, parity=serial.PARITY_NONE, stopbits=1, rtscts=1)    
        
    def closePort(self):
        self.fd.close()    
        
    def mkMsg(self, board, cmd, target, data=""):
        assert target in self.targets
        clientid = 0x42  # not sure
        assert len(data) <= 5
        msg = bytearray(struct.pack(">q", board)[-5:] + struct.pack("BBB", cmd, target, clientid) + data + bytearray(5 -len(data)))
        return msg
    
    def decodeMsg(self, data):
        assert len(data) == self.PACKET_LENGTH
        boardid = struct.unpack(">q", b"\0\0\0" + data[:5])
        cmd, target, clientid = struct.unpack("BBB", data[5:8])
        _data = data[8:13]
        decoded = _data
        # We do try to decode set messages, because these contain the original command in the error case
        if cmd == self.MSG_NoType:            decoded = None
        elif cmd == self.MSG_SetPWMValue:     decoded = struct.unpack(">B", _data[0:1])[0]
        elif cmd == self.MSG_OK:              decoded = None
        elif cmd == self.MSG_ERROR:           decoded = None
        return boardid, cmd, target, decoded
        
    def msgSetPWMValue(self, board, target, value):  # 0..100 int
        assert value >= 0 and value <= 100
        assert target in self.ports
        return self.mkMsg(board, self.MSG_SetPWMValue, target, struct.pack("BBBBB", value, value, value, value, value, ))
    
    def sendMsg(self, data):
        assert len(data) == self.PACKET_LENGTH
        self.fd.write(data)
        
    def receive(self, n=-1):
        # should block until exact number of bytes read
        if n == -1:
            n = self.PACKET_LENGTH
        data = self.fd.read(n)
        return bytearray(data)
    
    def received(self, data, acceptStatus):
        self.statusMessages
        msg = self.decodeMsg(data)
        boardid, cmd, target, info = msg
        if cmd in (self.MSG_NoType, self.MSG_EventTriggered, self.MSG_OK, self.MSG_ERROR):
            self.statusMessages.append(msg)
            if acceptStatus:
                sm = self.statusMessages[0]
                self.statusMessages = self.statusMessages[1:]
                return sm
            return self.receiveMsg()
        return msg
    
    def receiveMsg(self, acceptStatus=False, prepend=bytearray()):
        self.statusMessages
        if acceptStatus and len(self.statusMessages) != 0:
            sm = self.statusMessages[0]
            self.statusMessages = self.statusMessages[1:]
            return sm
        self.fd.timeout = None
        data = prepend + self.receive(self.PACKET_LENGTH - len(prepend))
        return self.received(data, acceptStatus)
    
    def consumeOK(self, board, target):
        m = self.receiveMsg(acceptStatus=True)
        _board, cmd, _target, decoded = m
        if cmd == self.MSG_OK:
            return 0
        else:
            return 1
#         raise Exception("Unexpected return command: %x" % cmd)
        
    def setState(self, board, target, val):
        self.sendMsg(self.msgSetPWMValue(board, target, int(val * 100)))
        self.consumeOK(board, target)