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

    def __init__(self):
        super().__init__()
        self.mutex = QtCore.QMutex()
        self.controller = Camera_controller(self._onConnect)
        self.isAuto = False
        self.reset_bg()
        
    def _onConnect(self):
        self.roi0 = self.controller.roi

    @property
    def roi(self):
        """Return """
        return np.asarray(self.controller.roi)
    
    def roi_zoom(self, roi):
        QtCore.QMutexLocker(self.mutex)
        roi = np.array(roi)
        cur_roi = np.array(self.controller.roi)
        roi[:2] += cur_roi[:2]
        self.controller.roi = roi
        self.new_roi.emit()

    def roi_reset(self):
        QtCore.QMutexLocker(self.mutex)
        self.controller.roi = self.roi0
        self.new_roi.emit()

    def reconnect(self):

        QtCore.QMutexLocker(self.mutex)

        self.controller.reconnect()

    def get_image(self, rmbg=True):

        QtCore.QMutexLocker(self.mutex)

        im = self.controller.get_image()
        if self.isAuto:
            self.correct_exposure_time(im)
        if rmbg:
            im = im * 1. - self._bg
        return im

    def exposure_time_range(self):

        QtCore.QMutexLocker(self.mutex)

        return self.controller.exposure_time_range()

    def set_exposure_time(self, time):

        QtCore.QMutexLocker(self.mutex)

        self.new_exposure_time.emit(time)
        self.controller.set_exposure_time(time)

    def get_exposure_time(self):

        QtCore.QMutexLocker(self.mutex)

        return self.controller.get_exposure_time()

    exposure_time = property(get_exposure_time, set_exposure_time)

    def auto_exposure_time(self, on):

        QtCore.QMutexLocker(self.mutex)

        self.state_auto_exposure_time.emit(on)
        self.isAuto = on

    def extShutter(self, on):

        QtCore.QMutexLocker(self.mutex)

        self.ext_shutterState.emit(on)
        self.controller.ext_shutter(on)

    def correct_exposure_time(self, im):

        QtCore.QMutexLocker(self.mutex)

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

        QtCore.QMutexLocker(self.mutex)

        self._bg = 0

    def set_bg(self):

        QtCore.QMutexLocker(self.mutex)

        self._bg = self.controller.get_image()

    def restart_streaming(self):

        QtCore.QMutexLocker(self.mutex)

        self.controller.restart_streaming()
