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
        return 0
        #TODO: read better and rteurn value
        self.sendCommand('V?')
        res=self.ser.read(100)
        return res
    
    def switch(self, on):
        if on:
            self.sendCommand('ON')
        else:
            self.sendCommand('OFF')
    
    
#%%
if __name__ == '__main__':
    pass
