# -*- coding: utf-8 -*-
"""
Created on Mon May  1 11:18:20 2017

@author: quentinpeter
"""

import numpy as np
class laser_controller():
    def __init__(self):
        self.range = np.array([0, 10])
        self.intensity = 0
    
    def get_range(self):
        return self.range
    
    def set_intensity(self, I):
        self.intensity = I   
        
    def get_intensity(self):
        return self.intensity
    
    def switch(self, on):
        pass
    