# -*- coding: utf-8 -*-
"""
Created on Tue May  2 09:33:38 2017

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

from .coordinates_delegate import coordinates_delegate
from .movement_delegate import movement_delegate
from .write_delegate import write_delegate
from .laser_delegate import laser_delegate
from .camera_delegate import camera_delegate
from .focus_delegate import Focus_delegate
from .canvas_delegate import Canvas_delegate
from .script_delegate import Script_delegate

from widgets.application_interface import ApplicationWindow


class Application_delegate(QtCore.QObject):
    error = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.camera_delegate = camera_delegate()
        self.laser_delegate = laser_delegate()

        # Create delegates for I/O
        self.canvas_delegate = Canvas_delegate(self)
        self.movement_delegate = movement_delegate(self)
        self.focus_delegate = Focus_delegate(self)

        # Create delegates for actions
        self.coordinates_delegate = coordinates_delegate(self)
        self.write_delegate = write_delegate(self)
        self.script_delegate = Script_delegate(self)

        self.mainWindow = ApplicationWindow(self, self.canvas_delegate._canvas)

    def ESTOP(self):
        self.focus_delegate.ESTOP()
        self.write_delegate.ESTOP()
        self.movement_delegate.ESTOP()
        self.script_delegate.ESTOP()
        self.coordinates_delegate.ESTOP()
        self.movement_delegate.unlock()
