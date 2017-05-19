# -*- coding: utf-8 -*-
"""
Created on Mon May 15 12:21:21 2017

@author: quentinpeter
"""
from PyQt5 import QtCore
import sys
import numpy as np
if sys.platform == "darwin":
    from controllers.camera_controller_placeholder import camera_controller
else:
    from controllers.camera_controller import camera_controller
    
class camera_delegate(QtCore.QObject):
    
    newShutter = QtCore.pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.controller = camera_controller()
        self.isAuto = False
        
    def reconnect(self):
        self.controller.reconnect()
        
    def get_image(self):
        im = self.controller.get_image()
        if self.isAuto:
            self.correctShutter(im)
        return im
    
    def shutter_range(self):
        return self.controller.shutter_range()
        
    def set_shutter(self,time):
        try:
            self.newShutter.emit(time)
            self.controller.set_shutter(time)
        except:
            import sys
            print(sys.exc_info())
    def get_shutter(self):
        return self.controller.get_shutter()
    
    def autoShutter(self, on):
        self.isAuto = on
        
    def correctShutter(self, im):
        amax = np.max(im)
        time = self.controller.get_shutter()
        if amax < 200: # 4/5 of the intensity
            time = time*256/amax
            self.controller.set_shutter(time)
        elif amax>254:
            overprct = np.sum(im>254)/np.prod(np.shape(im))
            if overprct > .1: # 10% image overexposed
                self.controller.set_shutter(time/2)
            