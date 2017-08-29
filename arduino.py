# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 15:55:13 2017

@author: tk391
"""

import serial
import time

arduino = serial.Serial('COM4')
arduino.write('ON\n'.encode())
time.sleep(10)
arduino.write('OFF\n'.encode())
arduino.close()


with arduino as serial.Serial('COM4'):
    arduino.write('ON\n'.encode())
    time.sleep(10)
    arduino.write('OFF\n'.encode())