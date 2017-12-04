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
import serial
from .HW_conf import camera_shutter_COM, pixeLINK_SN


class camera_controller():
    def __init__(self):
        self.cam = None
        self.reconnect()
        self._ext_shutter = serial.Serial(camera_shutter_COM)
        self._ext_shutter.write('OFF\n'.encode())

    def __del__(self):
        self._ext_shutter.close()

    def reconnect(self):
        del self.cam
        self.cam = PixeLINK(serialNumber=pixeLINK_SN)

    def exposure_time_range(self):
        return [1.9e-5, .1]

    def get_image(self):
        im = self.cam.grab()
        im = im[::-1, ::-1]
        return im

    def set_exposure_time(self, time):
        amin, amax = self.exposure_time_range()
        if time < amin:
            time = amin
        elif time > amax:
            time = amax
        try:
            self.cam.shutter = time
        except BaseException:
            print(f"Unable to set shutter time {time}")

    def get_exposure_time(self):
        return self.cam.shutter

    def restart_streaming(self):
        self.cam.streaming = False
        self.cam.streaming = True

    def ext_shutter(self, Open):
        if Open:
            self._ext_shutter.write('ON\n'.encode())
        else:
            self._ext_shutter.write('OFF\n'.encode())
