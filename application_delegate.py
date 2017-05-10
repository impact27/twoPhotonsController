# -*- coding: utf-8 -*-
"""
Created on Tue May  2 09:33:38 2017

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
from PyQt5 import QtCore, QtWidgets
from orientation_delegate import orientation_delegate
from mouvment_delegate import mouvment_delegate
from tilt_delegate import tilt_delegate
from gcode import gcode_draw
from write_delegate import write_delegate
import matplotlib
cmap = matplotlib.cm.get_cmap('plasma')

from controllers.camera_controller import camera_controller
from controllers.laser_controller import laser_controller



class application_delegate(QtCore.QObject):
    error = QtCore.pyqtSignal(str)
    liveSwitched = QtCore.pyqtSignal(bool)
    drawSwitched = QtCore.pyqtSignal(bool)
    def __init__(self,imageCanvas):
        super().__init__()
        self.mouvment_delegate = mouvment_delegate()
        self.camera_controller = camera_controller()
        self.laser_controller = laser_controller()
        
        self.orientation_delegate = orientation_delegate(self)
        self.tilt_delegate = tilt_delegate(self)
        self.write_delegate = write_delegate(self)
        
        self.live_timer = QtCore.QTimer()
        self.live_timer.timeout.connect(self.showCameraFrame)
        
        self.draw_timer = QtCore.QTimer()
        self.draw_timer.timeout.connect(self.drawPos)
        
        self.imageCanvas=imageCanvas
        
        self.mouvment_delegate.error.connect(lambda astr: 
                                            self.error.emit(astr))
            
        self.lastpos=[np.nan, np.nan]
        self.lastFracIntensity=np.nan
    
    def switch_live(self, on):
        if on:
            self.switch_draw(False)
            self.live_timer.start(100)
        else:
            self.live_timer.stop()
            self.clearFig()
        self.liveSwitched.emit(on)
            
        
    def switch_draw(self, on):
        if on:
            self.switch_live(False)
            self.draw_timer.start(100)
        else:
            self.draw_timer.stop()
            self.lastpos=[np.nan, np.nan]
            self.lastFracIntensity=np.nan
        self.drawSwitched.emit(on)

        
    def drawPos(self):
        newpos=self.mouvment_delegate.get_laser_XY_position()
        laserI=self.laser_controller.get_intensity()
        lRange=self.laser_controller.get_range()
        f=(laserI-lRange[0])/(lRange[1]-lRange[0])
        color=cmap(np.min((f,self.lastFracIntensity)))
        
        self.imageCanvas.plot([self.lastpos[0], newpos[0]],
                              [self.lastpos[1], newpos[1]], c=color)
        self.lastpos=newpos
        self.lastFracIntensity=f
    
    
    def correct_orientation(self):
        theta, origin=self.orientation_delegate.solve()
        
        if np.isnan(theta):
            self.error.emit('Not enough data points!')
        else:
            self.mouvment_delegate.set_XY_correction(theta, origin)
    
    def correct_tilt(self):
        
        zcoeffs = self.tilt_delegate.solve()
        
        if np.any(np.isnan(zcoeffs)):
            self.error.emit("Can't correct tilt")
        else:
            self.mouvment_delegate.set_Z_correction(zcoeffs)
        
    def showCameraFrame(self):
        frame=self.camera_controller.get_image()
        self.imageCanvas.setimage(frame)
        
    def clearFig(self):
        self.imageCanvas.clear()
        
    def ESTOP(self):
        self.mouvment_delegate.ESTOP()
        self.tilt_delegate.thread.terminate()
        self.write_delegate.thread.terminate()
    
    def goto_XY_position(self, xpos, ypos):
        self.mouvment_delegate.goto_XY_position(np.array([xpos,ypos]))
        
    def draw_device(self, xori, yori, gpath, Nx, Ny, dx, dy):
        
        greader = gcode_draw()
        greader.readFile(gpath)
        
        gwritten = greader.getDrawing()
        
        if Nx==1:
            dx=1
        if Ny==1:
            dy=1
        for x in np.arange(xori, xori+Nx*dx, dx):
            for y in np.arange(yori, yori+Ny*dy, dy):
                self.imageCanvas.plot(gwritten[:,0]+x,gwritten[:,1]+y)
        
        
    def write_device(self, xori, yori, gpath, Nx, Ny, dx, dy):
        self.write_delegate.write( gpath, xori, yori, Nx, Ny, dx, dy)
        
        
    def get_image(self,z=None):
        im = self.camera_controller.get_image(z)
        self.imageCanvas.setimage(im)
        return im
    
    def manualFocus(self):
        self.mouvment_delegate.goto_cube_position([0,0,25],rawPos=True)
        
        