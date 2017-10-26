# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 13:30:56 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import cv2
#==============================================================================
# Plot canevas
#==============================================================================


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self._axes = fig.add_subplot(111)

        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class ImageCanvas(MyMplCanvas):
    
    newrange = QtCore.pyqtSignal(float, float)
    newclick = QtCore.pyqtSignal(np.ndarray, float)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clear()
        self._lastim = np.zeros((2, 2))
        self._autoc = False
        self.figure.canvas.mpl_connect('button_press_event', self.onImageClick)
        self._click_pos = np.array([[np.nan, np.nan], [np.nan, np.nan]])
        self._crosshandle = None
        self._pixelSize = 1

    def set_pixel_size(self, pxsize):
        factor = pxsize/self._pixelSize
        self._click_pos *= factor
        self._pixelSize = pxsize
        if self._imhandle is not None:
            self.imshow()
            self.update_click()
            
        
    def imshow(self, im=None, vmin=0, vmax=255):
        self.newrange.emit(vmin, vmax)
        if im is None:
            im = self._lastim
            if im is None:
                print("No image!")
                return
        self._lastim = im
        self.figure.clear()
        self._axes = self.figure.add_subplot(111)
        extent = (0, im.shape[0]*self._pixelSize,
                  0, im.shape[1]*self._pixelSize)
        self._imhandle = self._axes.imshow(im, vmin=vmin, vmax=vmax, extent=extent)
        self._axes.axis('image')
        self.figure.colorbar(self._imhandle)
        self.draw()

    def auto_range(self):
        im = self.get_im()
        vmin = np.percentile(im,1)
        vmax = np.percentile(im,99)
        self.imshow(vmin=vmin, vmax=vmax)
#    @profile
    def frameshow(self, im):
        self._lastim = im
        if self._imhandle is not None:
            im = cv2.resize(im, tuple(np.array(im.shape)//2), 
                            interpolation=cv2.INTER_AREA)
            self._imhandle.set_data(im)
#            if self._autoc:
#                self._imhandle.set_clim(im.min(), im.max())
            self._axes.draw_artist(self._imhandle)
            if self._crosshandle is not None:
                self._axes.draw_artist(self._crosshandle[0])
            self.blit(self._axes.bbox)
        else:
            self.imshow(im)

    def clear(self):
        self._imhandle = None
        self.figure.clear()
        self._axes = self.figure.add_subplot(111)
        self.draw()

    def plot(self, X, Y, fmt='-', axis='normal', twinx=False, **kwargs):
        if self._imhandle is not None:
            self.clear()
        ax = self._axes
        if twinx:
            ax = self._axes.twinx()
        ax.plot(X, Y, fmt, **kwargs)
        self._axes.axis(axis)
        self.draw()

    def get_im(self):
        return self._lastim

    def onImageClick(self, event):
        """A CLICK!!!!!!!!"""
        # Are we displaying an image?
        if self._imhandle is None:
            return
        
        #What button was that?
        if event.button == 1:
            idx = 0
        elif event.button == 3:
            idx = 1
        else:
            return
        
        self._click_pos[idx, :] = [float(event.ydata), float(event.xdata)]
        self.update_click()
        
    def update_click(self):
        self._crosshandle = self._axes.plot(self._click_pos[:,1], 
                                            self._click_pos[:,0], 'r-x')
        self.frameshow(self._lastim)
        
        dist = np.sqrt(np.dot(self._click_pos[0], self._click_pos[1]))
        
        self.newclick.emit(self._click_pos, dist)

            
    def plotZCorr(self, X, Y, Y2):
        self.clear()
        self.plot(
            X[Y < 4 * np.min(Y)], Y[Y < 4 * np.min(Y)], '.')
        self.plot(X, Y2, 'x', twinx=True, c='C1')
        self.draw()
