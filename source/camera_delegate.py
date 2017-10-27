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

    new_exposure_time = QtCore.pyqtSignal(float)
    state_auto_exposure_time = QtCore.pyqtSignal(bool)
    ext_shutterState = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.controller = camera_controller()
        self.isAuto = False
        self.pixelSize = 1 / 20  # TODO: check that
        self.reset_bg()

    def reconnect(self):
        self.controller.reconnect()

    def get_image(self, rmbg=True):
        im = self.controller.get_image()
        if self.isAuto:
            self.correct_exposure_time(im)
        if rmbg:
            im = im * 1. - self._bg
        return im

    def exposure_time_range(self):
        return self.controller.exposure_time_range()

    def set_exposure_time(self, time):
        self.new_exposure_time.emit(time)
        self.controller.set_exposure_time(time)

    def get_exposure_time(self):
        return self.controller.get_exposure_time()

    exposure_time = property(get_exposure_time, set_exposure_time)

    def auto_exposure_time(self, on):
        self.state_auto_exposure_time.emit(on)
        self.isAuto = on

    def extShutter(self, on):
        self.ext_shutterState.emit(on)
        self.controller.ext_shutter(on)

    def correct_exposure_time(self, im):
        amax = np.max(im)
        time = self.controller.get_exposure_time()
        if amax < 200:  # 4/5 of the intensity
            time = time * 256 / amax
            self.set_exposure_time(time)
        elif amax > 254:
            overprct = np.sum(im > 254) / np.prod(np.shape(im))
            if overprct > .1:  # 10% image overexposed
                self.set_exposure_time(time / 2)

    def reset_bg(self):
        self._bg = 0

    def set_bg(self):
        self._bg = self.controller.get_image()
