# -*- coding: utf-8 -*-
"""
Created on Sun May  7 14:23:39 2017

@author: quentinpeter
"""

import numpy as np
from PyQt5 import QtCore
from gcode import gcode_reader, gcode_checker

class write_delegate(QtCore.QObject):
    def __init__(self, parent):
        self.parent=parent
        self.thread = write_thread(self.parent)
        
    def write(self, gfilename, xori, yori, Nx, Ny, dx, dy):
        with open(gfilename,'r') as f:
            gcommands = f.read()
        intensityRange = self.parent.laser_controller.get_range()
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


class write_thread(QtCore.QThread):
    def __init__(self, parent):
        super().__init__()
        self.md = parent.mouvment_delegate
        self.lc = parent.laser_controller
        self.error = None
        self.args = None
        self.lockid = None
        self.gcommands = None
     
    def set_args(self, gcommands, xori, yori, Nx, Ny, dx, dy):
        self.args = (xori, yori, Nx, Ny, dx, dy)
        self.gcommands = gcommands
        
    def run(self):
        self.lockid = self.md.lock()
        
        if self.lockid is None:
            self.error = "Unable to lock the mouvment"
            return
        
        XYStageLast= self.md.get_XY_position(rawCoordinates=True)
        
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
                
        self.md.unlock()
                
    def writeGCode(self, XYStageLast):
        defaultCubeSpeed=self.md.get_cube_velocity()
        writer = gwriter(self.md,self.lc,self.lockid, XYStageLast)
        writer.readGcommands(self.gcommands)
        self.md.set_cube_velocity(defaultCubeSpeed, checkid = self.lockid)
        
class gwriter(gcode_reader):
    
    def __init__(self, md, lc, lockid, XYStageLast):
        super().__init__()
        self.md = md
        self.lc = lc
        self.lc.set_intensity(0)
        self.lc.switch(True)
        self.lockid = lockid
        self.Xmlast = np.zeros(3)
        self.Xslast = None
        self.XYStageLast = XYStageLast
        
    def __del__(self):
        self.lc.set_intensity(0)
        self.lc.switch(False)
        
    def setIntensity(self,E):
        self.lc.set_intensity(E)
    
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
        