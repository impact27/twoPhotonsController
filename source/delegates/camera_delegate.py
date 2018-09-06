# -*- coding: utf-8 -*-
"""
Created on Mon May 15 12:21:21 2017

@author: quentinpeter
"""
from PyQt5 import QtCore
import sys
import numpy as np
if sys.platform == "darwin":
    from controllers.camera_controller_placeholder import Camera_controller
else:
    from controllers.camera_controller import Camera_controller


class Camera_delegate(QtCore.QObject):

    new_exposure_time = QtCore.pyqtSignal(float)
    state_auto_exposure_time = QtCore.pyqtSignal(bool)
    ext_shutterState = QtCore.pyqtSignal(bool)
    new_roi = QtCore.pyqtSignal()

    def mutex(f):
        def ret(cls, *args, **kargs):
            QtCore.QMutexLocker(cls.mutex)
            return f(cls, *args, **kargs)
        return ret
    
    def __init__(self):
        super().__init__()
        self.mutex = QtCore.QMutex()
        self.controller = Camera_controller(self._onConnect)
        self.isAuto = False
        self.reset_bg()
        self.roi0 = (0, 0, 100, 100)
        
    def _onConnect(self):
        self.roi0 = self.controller.roi

    @property
    def roi(self):
        """Return """
        return np.asarray(self.controller.roi)
    
    @mutex
    def roi_zoom(self, roi):
        roi = np.array(roi)
        cur_roi = np.array(self.controller.roi)
        roi[:2] += cur_roi[:2]
        self.controller.roi = roi
        self.new_roi.emit()

    @mutex
    def roi_reset(self):
        self.controller.roi = self.roi0
        self.new_roi.emit()

    @mutex
    def get_image(self, rmbg=True):
        im = self.controller.get_image()
        if self.isAuto:
            self.correct_exposure_time(im)
        if rmbg:
            im = im * 1. - self._bg
        return im

    @mutex
    def exposure_time_range(self):
        return self.controller.exposure_time_range()

    @mutex
    def set_exposure_time(self, time):
        self.new_exposure_time.emit(time)
        self.controller.exposure_time = time

    @mutex
    def get_exposure_time(self):
        return self.controller.get_exposure_time()

    exposure_time = property(get_exposure_time, set_exposure_time)

    @mutex
    def auto_exposure_time(self, on):
        self.state_auto_exposure_time.emit(on)
        self.isAuto = on

    @mutex
    def extShutter(self, on):
        self.ext_shutterState.emit(on)
        self.controller.ext_shutter(on)

    @mutex
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

    @mutex
    def reset_bg(self):
        self._bg = 0

    @mutex
    def set_bg(self):
        self._bg = self.controller.get_image()

    @mutex
    def restart_streaming(self):
        self.controller.restart_streaming()
