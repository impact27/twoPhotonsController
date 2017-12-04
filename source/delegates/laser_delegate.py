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
    from controllers.laser_controller_placeholder import laser_controller
else:
    from controllers.laser_controller import laser_controller


class laser_delegate(QtCore.QObject):

    switched = QtCore.pyqtSignal(bool)
    newIntensity = QtCore.pyqtSignal(float)

    def __init__(self):
        super().__init__()
        self.mutex = QtCore.QMutex()
        self.controller = laser_controller()
        self.I = self.controller.get_intensity()
        self.state = self.controller.get_state()

    def reconnect(self):

        QtCore.QMutexLocker(self.mutex)

        self.controller.reconnect()

    def get_range(self):

        QtCore.QMutexLocker(self.mutex)

        return self.controller.get_range()

    def set_intensity(self, V):

        QtCore.QMutexLocker(self.mutex)

        if V != self.I:
            self.newIntensity.emit(V)
            self.controller.set_intensity(V)
            self.I = self.controller.get_intensity()

    def get_intensity(self):

        QtCore.QMutexLocker(self.mutex)

        return self.controller.get_intensity()

    def switch(self, state):

        QtCore.QMutexLocker(self.mutex)

        if state != self.state:
            self.state = state
            self.controller.switch(state)
            self.switched.emit(state)

    def get_state(self):

        QtCore.QMutexLocker(self.mutex)

        return self.state
