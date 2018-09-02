# -*- coding: utf-8 -*-
"""
Created on Mon May  1 11:17:56 2017

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


class camera_controller():
    def __init__(self):
        self.exposure_time = .01
        self._roi = (0, 0, 100, 100)

    def reconnect(self):
        print('Connected Camera')

    def get_image(self):
        data = np.exp(-(np.arange(100)-50)**2/(2*20))
        data = data[:, np.newaxis] * data[np.newaxis, :]
        data = data/np.max(data) * 256
        data = np.random.rand() * data
        data = data[self._roi[1]:self._roi[1]+self._roi[3],
                    self._roi[0]:self._roi[0]+self._roi[2]]
        return data

    def exposure_time_range(self):
        return [1.9e-5, .1]

    def set_exposure_time(self, time):
        self.exposure_time = time

    def get_exposure_time(self):
        return self.exposure_time

    def ext_shutter(self, Open):
        pass

    def restart_streaming(self):
        pass

    @property
    def roi(self):
        return self._roi

    @roi.setter
    def roi(self, ltwhTuple):
        self._roi = ltwhTuple
