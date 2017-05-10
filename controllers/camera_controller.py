# -*- coding: utf-8 -*-
"""
Created on Wed May 10 14:04:59 2017

@author: quentinpeter
"""
import numpy as np
from pixelink import PixeLINK

class camera_controller():
    def __init__(self):
        self.cam = PixeLINK()
    
    def exp_range(self):
        return [1.9e-5,.1]
        
    def get_image(self):
        return self.cam.grab()
        
    def set_shutter(self,time):
        amin, amax = self.exp_range()
        assert (time > amin and time < amax)
        self.cam.shutter = time