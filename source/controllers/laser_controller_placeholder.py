# -*- coding: utf-8 -*-
"""
Created on Mon May  1 11:18:20 2017

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


class laser_controller():
    def __init__(self):
        self.range = np.array([0, 10])
        self.intensity = 0
        self.state = False

    def reconnect(self):
        print("Connected Laser")

    def get_range(self):
        return self.range

    def set_intensity(self, I):
        self.intensity = I

    def get_intensity(self):
        return self.intensity

    def switch(self, on):
        self.state = on

    def get_state(self):
        return self.state
