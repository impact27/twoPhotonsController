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
from .stage_controller import HW_E727

class Laser_controller():

    def __init__(self):
        self._HW = HW_E727(self.onConnect)
        self._V = 0

    def onConnect(self):
        self._HW.SVO(4, False)
        self._HW.SVA(4, 0)

    def get_range(self):
        return np.array([0, 10])
    
    @property
    def intensity(self):
        if not self._HW.IsConnected():
            return 0
        return float(self._HW.qVOL(4)[4]) 

    @intensity.setter
    def intensity(self, V):
        amin, amax = self.get_range()
        if V < amin:
            V = amin
        if V > amax:
            V = amax
        self._V = V
        self._HW.SVA(4, V)

    def get_state(self):
        return self._HW.IsConnected() and self._HW.IsControllerReady()



# %%
if __name__ == '__main__':
    lc = Laser_controller()

#import time
#import serial
# class old_laser_controller():
#
#    def __init__(self):
#        self.ser = None
#        self.reconnect()
#        self.buffer = ''
#
#    def readline(self, timeout=1):
#        start = time.time()
#        while '\n' not in self.buffer and time.time() < start + timeout:
#            self.buffer += self.ser.read_all().decode()
#        if '\n' not in self.buffer:
#            raise RuntimeError("Laser timeout")
#        idx = self.buffer.find('\n') + 1
#        ret = self.buffer[:idx]
#        self.buffer = self.buffer[idx:]
#        return ret
#
#    def reconnect(self):
#        del self.ser
#        self.ser = serial.Serial(laser_power_COM, timeout=1)
#        self.sendCommand('*IDN?')
#        res = self.readline()
#        print(res)
#
#    def sendCommand(self, cmd):
#        self.buffer = ''
#        self.ser.write('{}\n'.format(cmd).encode())
#
#    def __del__(self):
#        self.ser.close()
#
#    def get_range(self):
#        return np.array([0, 10])
#
#    def set_intensity(self, V):
#        amin, amax = self.get_range()
#        if V < amin:
#            V = amin
#        if V > amax:
#            V = amax
#        self.sendCommand('V {:.2f}'.format(V))
#
#    def get_intensity(self):
#        self.sendCommand('V?')
#        res = self.readline()
#        return float(res[2:-2])
#
#    def switch(self, on):
#        if on:
#            self.sendCommand('ON')
#        else:
#            self.sendCommand('OFF')
#
#    def get_state(self):
#        self.sendCommand('OUT?')
#        res = self.readline()[:-2]
#        if res == 'OUT ON':
#            return True
#        elif res == 'OUT OFF':
#            return False
#        else:
#            print(res)
#            return None
