# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 13:30:56 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clear()
        self._lastim=np.zeros((2,2))
        self._autoc = False
        self.figure.canvas.mpl_connect('button_press_event',self.onImageClick)
        self._click_pos=(0, 0)
        self._crosshandle = None
        
    def imshow(self, im , vmax = None):
        self._lastim=im
        self.figure.clear()
        self._axes = self.figure.add_subplot(111)
        self._imhandle=self._axes.imshow(im, vmax = vmax)
        self._axes.axis('image')
        self.figure.colorbar(self._imhandle)
        self.draw()
       
#    @profile
    def frameshow(self, im):
        self._lastim=im
        if self._imhandle is not None:
            self._imhandle.set_data(im[::2, ::2])
#            if self._autoc:
#                self._imhandle.set_clim(im.min(), im.max())
            self._axes.draw_artist(self._imhandle)
            if self._crosshandle is not None:
                self._axes.draw_artist(self._crosshandle[0])
            self.blit(self._axes.bbox)
        else:
            self.imshow(im[::2, ::2], vmax = 255)
            
    def clear(self):
        self._imhandle=None
        self.figure.clear()
        self._axes = self.figure.add_subplot(111)
        self.draw()
        
    def plot(self, X, Y, fmt='-', axis='normal', **kwargs):
        if self._imhandle is not None:
            self.clear()
        self._axes.plot(X, Y, fmt, **kwargs)
        self._axes.axis(axis)
        self.draw()
        
    def get_im(self):
        return self._lastim
    
    def onImageClick(self,event):
        """A CLICK!!!!!!!!"""
        #When someone clicks
        self._click_pos = (int(event.xdata),int(event.ydata))
        if self._imhandle is not None:
            self._crosshandle = self._axes.plot(*(self._click_pos), 'rx')
            self.frameshow(self._lastim)
        