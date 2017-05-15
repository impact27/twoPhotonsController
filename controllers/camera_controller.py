# -*- coding: utf-8 -*-
"""
Created on Wed May 10 14:04:59 2017

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
from .pixelink import PixeLINK

class camera_controller():
    def __init__(self):
        self.cam = None
        self.reconnect()
        
    def reconnect(self):
        del self.cam
        self.cam = PixeLINK()
        
    
    def shutter_range(self):
        return [1.9e-5,.1]
        
    def get_image(self):
        return self.cam.grab()
        
    def set_shutter(self,time):
        amin, amax = self.exp_range()
        assert (time > amin and time < amax)
        self.cam.shutter = time
        
    def get_shutter(self):
        return self.cam.shutter