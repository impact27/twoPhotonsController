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
from .pixelink import PixeLINK
import serial
from .HW_conf import camera_shutter_COM, pixeLINK_SN, pixeLINK_MaxROI
import numpy as np

from .hardware_singleton import Hardware_Singleton


class HW_camera(Hardware_Singleton):
    def __init__(self, callback):
        super().__init__("Camera", callback)
        
    def _open_connection(self):
        return PixeLINK(serialNumber=pixeLINK_SN)
    
    def _close_connection(self):
        self.close()
    
class HW_shutter(Hardware_Singleton):
    def __init__(self):
        super().__init__("Shutter")
        
    def _open_connection(self):
        shutter = serial.Serial(camera_shutter_COM)
        shutter.write('OFF\n'.encode())
        return shutter
    
    def _close_connection(self):
        self.close()

class Camera_controller():
    def __init__(self, callback=None):
        self.shape = np.asarray(pixeLINK_MaxROI)
        self.cam = HW_camera(self.onCamConnect)
        self._ext_shutter = HW_shutter()
        
        self.callback = callback
        
        self.flip_image = True
        
    def onCamConnect(self):
        self.roi_reset()
        if self.callback is not None:
            self.callback()

    def exposure_time_range(self):
        return [1.9e-5, .1]

    def get_image(self):
        im = self.cam.grab()
        if self.flip_image:
            im = im[::-1, ::-1]
        return im

    @property
    def exposure_time(self):
        return self.cam.shutter
    
    @exposure_time.setter
    def exposure_time(self, time):
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

    @property
    def roi(self):
        roi = np.asarray(self.cam.roi)
        if self.flip_image:
            roi[:2] = self.shape - (roi[:2]+roi[2:])
        return roi

    @roi.setter
    def roi(self, roi):
        roi = np.asarray(roi)
        if self.flip_image:
            roi[:2] = self.shape - (roi[:2]+roi[2:])

        streaming = self.cam.streaming
        self.cam.streaming = False
        try:
            self.cam.roi = tuple(roi)
        except BaseException as e:
            print(roi[0] + roi[2], roi[1]+roi[3])
            print(e)
        self.cam.streaming = streaming
        
    def roi_reset(self):
        self.roi = (0, 0, *self.shape)

# %%
#from matplotlib.pyplot import figure, imshow
#cc = camera_controller()
# cc.ext_shutter(True)
# print(cc.roi)
# %%
#cc.roi = (500, 500, 1023,1005)
# print(cc.get_image().shape)
# imshow(cc.get_image())
