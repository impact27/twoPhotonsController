# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 13:30:56 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import sys
import matplotlib
cmap = matplotlib.cm.get_cmap('plasma')
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


class Canvas(MyMplCanvas):
    
    newclick = QtCore.pyqtSignal(np.ndarray)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clear()
        self._lastim = np.zeros((2, 2))
        self.figure.canvas.mpl_connect('button_press_event', self.onImageClick)
        self._click_pos = np.array([[np.nan, np.nan], [np.nan, np.nan]])
        self._crosshandle = None
        
    def clear(self):
        self._imhandle = None
        self.figure.clear()
        self._axes = self.figure.add_subplot(111)
        self.draw()
        
    def get_last_im(self):
        return self._lastim
    
    def imshow(self, im, *args, **kwargs):
        self._lastim = im
        self.figure.clear()
        self._axes = self.figure.add_subplot(111)
        
        self._imhandle = self._axes.imshow(im, *args, **kwargs)
        
        self._axes.axis('image')
        self.figure.colorbar(self._imhandle)
        
        if not np.all(np.isnan(self._click_pos)):
            self._crosshandle = self._axes.plot(
                    self._click_pos[:,1], self._click_pos[:,0], 'r-x')
        
        self.draw()
        
    def update_image(self, im, *args, **kwargs):
        self._lastim = im
        if self._imhandle is not None:
            
            self._imhandle.set_data(im)
            self._axes.draw_artist(self._imhandle)
            
            if self._crosshandle is not None:
                self._axes.draw_artist(self._crosshandle[0])
            
            self.blit(self._axes.bbox)
        else:
            self.imshow(im, *args, **kwargs)
    
    def plot(self, X, Y, fmt='-', axis='normal', twinx=False, **kwargs):
        if self._imhandle is not None:
            self.clear()
        ax = self._axes
        if twinx:
            ax = self._axes.twinx()
        ax.plot(X, Y, fmt, **kwargs)
        self._axes.axis(axis)
        self.draw()
    
    def onImageClick(self, event):
        """A CLICK!!!!!!!!"""
        # Are we displaying an image?
        if self._imhandle is None or event.ydata is None or event.xdata is None:
            return
        
        #What button was that?
        if event.button == 1:
            idx = 0
        elif event.button == 3:
            idx = 1
        else:
            return
        
        self._click_pos[idx, :] = [float(event.ydata), float(event.xdata)]
        
        self._crosshandle = self._axes.plot(
                    self._click_pos[:,1], self._click_pos[:,0], 'r-x')
        self.update_image(self.get_last_im())
        self.newclick.emit(self._click_pos)
        
        
    
    def clear_click(self):
        self.set_click_pos(np.array([[np.nan, np.nan], [np.nan, np.nan]]))
        self._crosshandle = None
        if self._imhandle is not None:
            self.update_image(self.get_last_im())
    
    @property
    def click_pos(self):
        return self._click_pos
    
    def set_click_pos(self, pos):
        self._click_pos = pos
        self.newclick.emit(self._click_pos)
            
    def is_showing_image(self):
        return self._imhandle is not None
    # TODO: give to focus    
        
    def plotZCorr(self, data, fit):
        try:
            list_Z, list_I, list_size = data
            self.clear()
            for Z, I, size in zip(list_Z, list_I, list_size):
                self.plot(Z, I, 'x')
                goodsize = size < 4 * np.min(size)
                self.plot(Z[goodsize], size[goodsize], '.C2', twinx=True)
                
            fitI = np.poly1d(fit)(Z)
#            self.plot(Z[fitI>0], fitI[fitI>0], '-')
            self.draw()
        except:
            print("Can't Plot!!!",sys.exc_info()[0])
                
    
    
    
        
    
    
