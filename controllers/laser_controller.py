# -*- coding: utf-8 -*-
"""
Created on Wed May 10 14:03:02 2017

@author: quentinpeter
"""
import numpy as np
import serial

class laser_controller():
    
    def __init__(self):
        self.ser = serial.Serial('COM8', timeout=1)
        self.sendCommand('*IDN?')
        
        res=self.ser.read(100)
        print(res)
        
    def sendCommand(self, cmd):
        self.ser.write('{}\n'.format(cmd).encode())
        
    def __del__(self):
        self.ser.close()

    def get_range(self):
        return np.array([0,10])
    
    def set_intensity(self, V):
        amin, amax = self.get_range()
        assert (V > amin and V < amax)
        self.sendCommand('V {:.2f}'.format(V))
        
    def get_intensity(self):
        self.sendCommand('V?')
        res=self.ser.read(100)
        print(res)
        return res
    
    def switch(self, on):
        if on:
            self.sendCommand('ON')
        else:
            self.sendCommand('OFF')
    
    
#%%
lc=laser_controller()
