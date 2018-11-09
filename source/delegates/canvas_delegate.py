# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 17:48:43 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets
import numpy as np
import cv2
import tifffile
from matplotlib.cm import get_cmap
import sys
cmap = get_cmap('plasma')

from widgets.canvas import MyMplCanvas
from delegates.thread import lockmutex


class Canvas_delegate(QtCore.QObject):
    newrange = QtCore.pyqtSignal(float, float)
    liveSwitched = QtCore.pyqtSignal(bool)
    drawSwitched = QtCore.pyqtSignal(bool)
    newclick = QtCore.pyqtSignal(np.ndarray)

    def __init__(self, parent):
        super().__init__()
        self._mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        self._parent = parent
        self._canvas = MyMplCanvas()
        self._thread = Canvas_Thread(self._canvas)

        # Create timers
        self.live_timer = QtCore.QTimer()
        self.live_timer.timeout.connect(self.show_frame)

        self.draw_timer = QtCore.QTimer()
        self.draw_timer.timeout.connect(self.draw_current_position)

        # draw memory
        self.lastpos = [np.nan, np.nan]
        self.lastFracIntensity = np.nan

        self._pixelSize = 1
        self._vmin = 0
        self._vmax = 255

        self.clear()
        self._lastim = np.zeros((2, 2))
        self._canvas.figure.canvas.mpl_connect(
            'button_press_event', self.onImageClick)
        self._canvas.figure.canvas.mpl_connect(
            'button_press_event', self.set_roi)
        self._canvas.figure.canvas.mpl_connect(
            'button_release_event', self.set_roi)
        self._canvas.figure.canvas.mpl_connect(
            'motion_notify_event', self.set_roi)

        self._click_pos = np.array([[np.nan, np.nan], [np.nan, np.nan]])

        self.ROI_select = None
        self.rescale_factor = 2
        self.cd = parent.camera_delegate

        def new_roi():
            self.clear()
            self.show_frame()
        self.cd.new_roi.connect(new_roi)

    def get_frame(self):
        frame = self._parent.camera_delegate.get_image()
        frame = cv2.resize(frame,
                           (frame.shape[1] // self.rescale_factor,
                            frame.shape[0] // self.rescale_factor),
                           interpolation=cv2.INTER_AREA)
        return frame

    @lockmutex
    def show_frame(self, frame=None):
        try:
            if frame is None:
                frame = self.get_frame()

            extent = (0, frame.shape[1] * self._pixelSize,
                      frame.shape[0] * self._pixelSize, 0)

            self.update_image(
                frame, vmin=self._vmin, vmax=self._vmax, extent=extent)
        except self._parent.camera_delegate.error:
            pass
        except BaseException as e:
            print("Can't show frame", e)

    @lockmutex
    def update_image(self, im, *args, **kwargs):
        self._lastim = im
        if self._imhandle is not None:

            self._imhandle.set_data(im)
            self._axes.draw_artist(self._imhandle)

            if self._crosshandle is not None:
                self._axes.draw_artist(self._crosshandle[0])

            if self._recthandle is not None:
                self._axes.draw_artist(self._recthandle[0])

            self._canvas.blit(self._axes.bbox)
        else:
            self.clear()
            self.imshow(im, *args, **kwargs)

    @lockmutex
    def clear(self):
        self._imhandle = None
        self._crosshandle = None
        self._recthandle = None
        self._twinx = None
        self._canvas.figure.clear()
        self._axes = self._canvas.figure.add_subplot(111)
        self.draw()

    @lockmutex
    def draw_current_position(self):
        md = self._parent.movement_delegate
        cmutex = md.piezo.controller_mutex()
        if not cmutex.tryLock():
            return
        try:
            if md.piezo.isRecordingMacro:
                return
            newpos = (md.motor.position + md.piezo.position)
            laserI = self._parent.laser_delegate.get_intensity()
            lRange = self._parent.laser_delegate.get_range()
            f = (laserI - lRange[0]) / (lRange[1] - lRange[0])
            color = cmap(np.min((f, self.lastFracIntensity)))
    
            self.plot([self.lastpos[0], newpos[0]],
                      [self.lastpos[1], newpos[1]],
                      axis='equal', c=color)
            self.lastpos = newpos
            self.lastFracIntensity = f
        finally:
            cmutex.unlock()

    @lockmutex
    def save_im(self):
        fn = QtWidgets.QFileDialog.getSaveFileName(
            self._canvas, 'TIFF file', QtCore.QDir.homePath(),
            "Images (*.tif)")
        im = self.get_last_im()
        tifffile.imsave(fn[0], np.asarray(im, dtype='float32'))

    @lockmutex
    def switch_live(self, on):
        if on:
            self.switch_draw(False)
            self.clear()
            self.live_timer.start(33)
        else:
            self.live_timer.stop()
        self.liveSwitched.emit(on)

    @lockmutex
    def switch_draw(self, on):
        if on:
            self.switch_live(False)
            self.draw_timer.start(100)
        else:
            self.draw_timer.stop()
            self.lastpos = [np.nan, np.nan]
            self.lastFracIntensity = np.nan
        self.drawSwitched.emit(on)

    @lockmutex
    def set_pixel_size(self, pxsize):
        factor = pxsize / self._pixelSize
        self.set_click_pos(self.click_pos * factor)
        self._pixelSize = pxsize
        self.redraw_image()

    @lockmutex
    def set_range(self, vmin=0, vmax=255):
        self.newrange.emit(vmin, vmax)
        self._vmin = vmin
        self._vmax = vmax
        self.redraw_image()

    @lockmutex
    def auto_range(self):
        im = self.get_last_im()
        vmin = np.percentile(im, 1)
        vmax = np.percentile(im, 99)
        self.set_range(vmin=vmin, vmax=vmax)

    @lockmutex
    def redraw_image(self):
        if self.is_showing_image():
            self.clear()
            self.show_frame(self.get_last_im())

    def get_last_im(self):
        return self._lastim

    @lockmutex
    def imshow(self, im, *args, **kwargs):
        self._lastim = im
        self.clear()

        self._imhandle = self._axes.imshow(im, *args, **kwargs)

        self._axes.axis('image')
        self._canvas.figure.colorbar(self._imhandle)

        if not np.all(np.isnan(self._click_pos)):
            self._crosshandle = self._axes.plot(
                self._click_pos[:, 1], self._click_pos[:, 0], 'r-x')

        self.draw()

    @lockmutex
    def plot(self, X, Y, fmt='-', axis='normal',
             twinx=False, draw=True, **kwargs):
        if self._imhandle is not None:
            self.clear()

        if twinx:
            if self._twinx is None:
                self._twinx = self._axes.twinx()
            ax = self._twinx
        else:
            ax = self._axes

        ax.plot(X, Y, fmt, **kwargs)
        self._axes.axis(axis)
        if draw:
            self.draw()

    @lockmutex
    def draw(self):
        self._thread.start()

    @lockmutex
    def get_ylim(self):
        return self._axes.get_ylim()

    @lockmutex
    def onImageClick(self, event):
        """A CLICK!!!!!!!!"""
        # Are we displaying an image?
        if self._imhandle is None or event.ydata is None or event.xdata is None:
            return

        if QtWidgets.QApplication.keyboardModifiers() != QtCore.Qt.ControlModifier:
            return
        # What button was that?
        if event.button == 1:
            idx = 0
        elif event.button == 3:
            idx = 1
        else:
            return

        self._click_pos[idx, :] = [float(event.ydata), float(event.xdata)]

        if self._crosshandle is not None:
            self._crosshandle[0].set_data(
                self._click_pos[:, 1], self._click_pos[:, 0])
        else:
            self._crosshandle = self._axes.plot(
                self._click_pos[:, 1], self._click_pos[:, 0], 'r-x')
        self.show_frame(self.get_last_im())
        self.newclick.emit(self._click_pos)

    def set_roi(self, event):
        if (self._canvas.toolbar._active ==
                "ZOOM" or self._canvas.toolbar._active == "PAN"):
            return

        # Are we displaying an image?
        if self._imhandle is None or event.ydata is None or event.xdata is None:
            return
        if QtWidgets.QApplication.keyboardModifiers() == QtCore.Qt.ControlModifier:
            return
        p0 = self.ROI_select
        p1 = [event.ydata, event.xdata]

        if event.name == 'button_press_event':
            self.ROI_select = p1

        if p0 is None:
            return

        if event.name == 'motion_notify_event':
            if self._recthandle is not None:
                self._recthandle[0].set_data(
                    [p0[1], p1[1], p1[1], p0[1], p0[1]],
                    [p0[0], p0[0], p1[0], p1[0], p0[0]])
            else:
                self._recthandle = self._axes.plot(
                    [p0[1], p1[1], p1[1], p0[1], p0[1]],
                    [p0[0], p0[0], p1[0], p1[0], p0[0]], 'r')
            self.show_frame(self.get_last_im())

        elif event.name == 'button_release_event':
            self._recthandle = None
            self.ROI_select = None
            roi = np.array([np.min([p0[1], p1[1]]),
                            np.min([p0[0], p1[0]]),
                            np.abs(p0[1] - p1[1]),
                            np.abs(p0[0] - p1[0])])
            if roi[2] < 5 or roi[3] < 5:
                return
            roi *= self.rescale_factor
            roi = np.round(roi)
            roi = np.array(roi, int)
            self.cd.roi_zoom((*roi,))

    @lockmutex
    def clear_click(self):
        self.set_click_pos(np.array([[np.nan, np.nan], [np.nan, np.nan]]))
        if self._crosshandle is not None:
            self._crosshandle[0].set_data(np.nan, np.nan)
        if self._imhandle is not None:
            self.show_frame()

    @property
    @lockmutex
    def click_pos(self):
        return self._click_pos

    @lockmutex
    def set_click_pos(self, pos):
        self._click_pos = pos
        self.newclick.emit(self._click_pos)

    @lockmutex
    def is_showing_image(self):
        return self._imhandle is not None

class Canvas_Thread(QtCore.QThread):
    def __init__(self, canvas):
        super().__init__()
        self._canvas = canvas

    def run(self):
        self._canvas.draw()