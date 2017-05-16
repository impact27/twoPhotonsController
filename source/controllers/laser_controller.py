# -*- coding: utf-8 -*-
"""
Created on Wed May 10 14:03:02 2017

@author: quentinpeter

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import numpy as np
import serial

class laser_controller():
    
    def __init__(self):
        self.ser = None
        self.reconnect()
        
    def reconnect(self):
        del self.ser
        self.ser = serial.Serial('COM8', timeout=1)
        self.sendCommand('*IDN?')
        res=self.ser.readline().decode()
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
        #TODO: read better and return value
        self.sendCommand('V?')
        res=self.ser.readline().decode()
        return float(res[2:])
    
    def switch(self, on):
        if on:
            self.sendCommand('ON')
        else:
            self.sendCommand('OFF')
            
    def get_state(self):
        assert False, "Not Done"
        self.sendCommand('V?')
        res=self.ser.readline().decode()
        return float(res[2:])
        
    
    
#%%
if __name__ == '__main__':
    pass