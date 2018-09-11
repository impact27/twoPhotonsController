# -*- coding: utf-8 -*-
"""
Created on Sun May  7 17:14:59 2017

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

import sys
from PyQt5 import QtCore

if sys.platform == "darwin":
    from controllers.laser_controller_placeholder import Laser_controller
else:
    from controllers.laser_controller import Laser_controller


class Laser_delegate(QtCore.QObject):
    newIntensity = QtCore.pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.controller = Laser_controller()
        self.I = 0

    def get_range(self):
        return self.controller.get_range()

    def set_intensity(self, V):
        if V is None:
            return
        if V != self.I:
            self.newIntensity.emit(V)
            self.controller.intensity = V
            self.I = V

    def get_intensity(self):
        return self.controller.intensity
    
    def VtoI(self, V):
        pass
    
    def ItoV(self, I):
        pass
        
    def set_calibration_curve(self, C):
        pass
        
        
