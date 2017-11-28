# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 17:48:43 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets
import numpy as np
import cv2
import tifffile
import matplotlib
cmap = matplotlib.cm.get_cmap('plasma')

from widgets.canvas import Canvas

class Canvas_delegate(QtCore.QObject):
    newrange = QtCore.pyqtSignal(float, float)
    liveSwitched = QtCore.pyqtSignal(bool)
    drawSwitched = QtCore.pyqtSignal(bool)
    
    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        self._canvas = Canvas()
        
        # Create timers
        self.live_timer = QtCore.QTimer()
        self.live_timer.timeout.connect(self.show_frame)

        self.draw_timer = QtCore.QTimer()
        self.draw_timer.timeout.connect(self.draw_current_position)
        
        #draw memory
        self.lastpos = [np.nan, np.nan]
        self.lastFracIntensity = np.nan
        
        self._pixelSize = 1
        self._vmin = 0
        self._vmax = 255
        
    def show_frame(self, frame=None):
        
        if frame is None:
            frame = self._parent.camera_delegate.get_image()
            frame = cv2.resize(frame, (frame.shape[1]//2, frame.shape[0]//2), 
                           interpolation=cv2.INTER_AREA)

        extent = (0, frame.shape[1]*self._pixelSize,
                  0, frame.shape[0]*self._pixelSize)
        
        self._canvas.update_image(
                frame, vmin=self._vmin, vmax=self._vmax, extent=extent)
        
    def show_image(self, image):
        self._canvas.imshow(image)
        
    def draw_current_position(self):
        newpos = self._parent.mouvment_delegate.position
        laserI = 0#self._parent.laser_delegate.get_intensity()
        lRange = self._parent.laser_delegate.get_range()
        f = (laserI - lRange[0]) / (lRange[1] - lRange[0])
        color = cmap(np.min((f, self.lastFracIntensity)))

        self._canvas.plot([self.lastpos[0], newpos[0]],
                          [self.lastpos[1], newpos[1]],
                          axis='equal', c=color)
        self.lastpos = newpos
        self.lastFracIntensity = f
        
    def save_im(self):
        fn = QtWidgets.QFileDialog.getSaveFileName(
            self._canvas, 'TIFF file', QtCore.QDir.homePath(),
            "Images (*.tif)")
        im = self._canvas.get_last_im()
        tifffile.imsave(fn[0], np.asarray(im, dtype='float32'))
        
    def switch_live(self, on):
        if on:
            self.switch_draw(False)
            self.live_timer.start(33)
        else:
            self.live_timer.stop()
        self.liveSwitched.emit(on)

    def switch_draw(self, on):
        if on:
            self.switch_live(False)
            self.draw_timer.start(100)
        else:
            self.draw_timer.stop()
            self.lastpos = [np.nan, np.nan]
            self.lastFracIntensity = np.nan
        self.drawSwitched.emit(on)
        
    def set_pixel_size(self, pxsize):
        factor = pxsize/self._pixelSize
        self._canvas.set_click_pos(self._canvas.click_pos*factor)
        self._pixelSize = pxsize
        self.update_im()
            
    def set_range(self, vmin=0, vmax=255):
        self.newrange.emit(vmin, vmax)
        self._vmin = vmin
        self._vmax = vmax
        self.update_im()

    def auto_range(self):
        im = self._canvas.get_last_im()
        vmin = np.percentile(im,1)
        vmax = np.percentile(im,99)
        self.set_range(vmin=vmin, vmax=vmax)
        
    def clear(self):
        self._canvas.clear()
        
    def update_im(self):
        if self._canvas.is_showing_image():
            self.clear()
            self.show_frame(self._canvas.get_last_im())