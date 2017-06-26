# -*- coding: utf-8 -*-
"""
Created on Sun May  7 14:23:39 2017

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
from PyQt5 import QtCore
from gcode import gcode_reader, gcode_checker
from serial.serialutil import SerialTimeoutException

class write_delegate(QtCore.QObject):
    def __init__(self, parent):
        self.parent=parent
        self.thread = write_thread(self.parent)
        self.thread.finished.connect(self.endwrite)
        
    def write(self, gfilename, xori, yori, Nx, Ny, dx, dy):
        with open(gfilename,'r') as f:
            gcommands = f.read()
        intensityRange = self.parent.laser_delegate.get_range()
        posRange=np.asarray([
                self.parent.mouvment_delegate.get_cube_PosRange(0),
                self.parent.mouvment_delegate.get_cube_PosRange(1),
                self.parent.mouvment_delegate.get_cube_PosRange(2)
                ])
        speedRange = self.parent.mouvment_delegate.get_cube_VelRange(0)
        
        checker = gcode_checker(intensityRange, posRange, speedRange)
            
        if not checker.gcode_inrange(gcommands):
            self.parent.error.emit("GCode values out of range")
            return
        
        self.thread.set_args(gcommands, xori, yori, Nx, Ny, dx, dy)
        self.thread.start()
        
    def endwrite(self):
        self.parent.newPosition.emit()


class write_thread(QtCore.QThread):
    def __init__(self, parent):
        super().__init__()
        self.md = parent.mouvment_delegate
        self.ld = parent.laser_delegate
        self.error = None
        self.args = None
        self.lockid = None
        self.gcommands = None
        self.parent = parent
     
    def set_args(self, gcommands, xori, yori, Nx, Ny, dx, dy):
        self.args = (xori, yori, Nx, Ny, dx, dy)
        self.gcommands = gcommands
        
    def run(self):
        try:
            self.lockid = self.md.lock()
            
            if self.lockid is None:
                self.error = "Unable to lock the mouvment"
                return
            
            XYStageLast = None
            
            xori, yori, Nx, Ny, dx, dy = self.args
            
            if Nx==1:
                dx=1
            if Ny==1:
                dy=1
                
            for par,y in enumerate(np.arange(yori, yori+Ny*dy, dy)):
                #Want to draw s
                parity=2*((par+1)%2)-1
                for x in np.arange(xori, xori+Nx*dx, dx)[::parity]:
                    
                    Xorigin=np.asarray([x, y])
                    XYStageLast=self.md.goto_XY_position(
                         Xorigin, XsFrom=XYStageLast, 
                         wait=True, checkid=self.lockid)
                    self.writeGCode(XYStageLast)
                    
            
        except SerialTimeoutException:
            self.parent.error('Timeout')
            
        self.md.unlock()
                
    def writeGCode(self, XYStageLast):
        defaultCubeSpeed=self.md.get_cube_velocity()
        writer = gwriter(self.md,self.ld,self.lockid, XYStageLast)
        writer.readGcommands(self.gcommands)
        self.md.set_cube_velocity(defaultCubeSpeed, checkid = self.lockid)
        
class gwriter(gcode_reader):
    
    def __init__(self, md, ld, lockid, XYStageLast):
        super().__init__()
        self.md = md
        self.ld = ld
        self.ld.set_intensity(0)
        self.lockid = lockid
        self.Xmlast = np.zeros(3)
        self.Xslast = None
        self.XYStageLast = XYStageLast
        
    def __del__(self):
        self.ld.set_intensity(0)
        self.ld.switch(False)
        
    def setIntensity(self,E):
        self.ld.set_intensity(E)
    
    def moveTo(self,X,Y,Z):
        Xmto = np.asarray([X, Y, Z])
        Xmto[np.isnan(Xmto)] = self.Xmlast[np.isnan(Xmto)]
        self.Xslast = self.md.goto_cube_position(
                                Xmto, XsFrom=self.Xslast,
                                XStageOrigin=self.XYStageLast,
                                wait=True, checkid=self.lockid)
        self.Xmlast=Xmto
    
    def setSpeed(self,F):
        self.md.set_cube_velocity(F, checkid=self.lockid)
        
    def stop(self):
        self.ld.switch(False)
        