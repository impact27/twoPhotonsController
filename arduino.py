# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 15:55:13 2017

@author: tk391
"""

import serial
import time

# with serial.Serial('COM6') as arduino:
#    arduino.write('ON\n'.encode())
#    time.sleep(2)
#    arduino.write('OFF\n'.encode())
#%%
arduino = serial.Serial('COM6')
#%%
arduino.write('ON\n'.encode())
#%%
arduino.write('OFF\n'.encode())
