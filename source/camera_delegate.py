# -*- coding: utf-8 -*-
"""
Created on Mon May 15 12:21:21 2017

@author: quentinpeter
"""
from PyQt5 import QtCore
import sys
if sys.platform == "darwin":
    from controllers.camera_controller_placeholder import camera_controller
else:
    from controllers.camera_controller import camera_controller
    
class camera_delegate(QtCore.QObject):
    
    newShutter = QtCore.pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.controller = camera_controller()
        
    def reconnect(self):
        self.controller.reconnect()
        
    def get_image(self):
        return self.controller.get_image()
    
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