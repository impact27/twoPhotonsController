# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 11:37:57 2017

@author: quentinpeter
"""

import serial
ser = serial.Serial('COM5', baudrate=115200, timeout=2)
ser.write(b'*IDN?\n\r')
res = ser.read(100)
ser.close()
print(res)
