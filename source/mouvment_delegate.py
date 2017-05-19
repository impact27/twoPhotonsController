# -*- coding: utf-8 -*-
"""
Created on Wed May  3 13:56:26 2017

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
import random
import numpy as np
from PyQt5 import QtCore
import sys

if sys.platform == "darwin":
    from controllers.stage_controller_placeholder import (linear_controller, 
                                                          cube_controller)
else:
    from controllers.stage_controller import (linear_controller, 
                                              cube_controller)



class mouvment_delegate(QtCore.QObject):
    
    error = QtCore.pyqtSignal(str) 
    
    def __init__(self, parent):
        super().__init__()
        self.linear_controller = linear_controller()
        self.cube_controller = cube_controller()
        
        self.R = np.eye(2)
        self.offset = np.zeros(2)
        self.zcoeff = np.zeros(3)
        self.locked = False
        self.lockid = None
        
        self.cubeSpeed = 1000
        self.XYSpeed = 1000
        self.parent = parent
        self.theta = 0
     
    def XsToXm(self, Xs):
        Xs = np.asarray(Xs)
        return 1000*self._getXYMaster(Xs/1000)
    
    def _getXYStage(self, XYmaster):
        return self.R@XYmaster+self.offset
    
    def _getXYMaster(self, XYstage):
        return np.linalg.inv(self.R)@(XYstage-self.offset)
    
    def _get_cube_Xs(self, XmCube, XsOrigin=None):
        
        if XsOrigin is None:
            XsOrigin = self.get_XY_position(rawCoordinates=True)
            
        XStageLocal = self.R@XmCube[:2]
        
        Xs = np.zeros_like(XmCube)
        Xs[:2] = XStageLocal
        Xs[2] = XmCube[2] + self._getZOrigin(XsOrigin+XStageLocal)
        return Xs
    
    def _get_cube_Xm(self, XsCube, XsOrigin=None):
        
        if XsOrigin is None:
            XsOrigin = self.get_XY_position(rawCoordinates=True)
            
        XStageLocal = XsCube[:2]
        
        Xm = np.zeros_like(XsCube)
        Xm[:2] = np.linalg.inv(self.R)@XStageLocal
        Xm[2] = XsCube[2] - self._getZOrigin(XsOrigin+XStageLocal)
        return Xm
    
    def _getZOrigin(self, XYstage):
        return np.dot(self.zcoeff[:2],XYstage) + self.zcoeff[2]
    
    def _checklock(self,lockid):
        if not self.locked:
            return True
        elif self.lockid==lockid:
            return True
        else:
            self.error.emit('Mouvment is locked!')
            return False
        
    def lock(self):
        if not self._checklock(None):
            return None
        
        self.locked=True
        self.lockid=random.randint(0,100)
        return self.lockid
        
    def unlock(self):
        self.locked=False
        self.lockid=None
        
    def ESTOP(self):
        self.linear_controller.ESTOP()
        self.cube_controller.ESTOP()
        
    def is_onTarget(self):
        return (self.linear_controller.is_onTarget()
                and self.cube_controller.is_onTarget())
    
    def get_laser_XY_position(self, rawCoordinates = False, linOnly = False):
        X=self.get_XY_position(True)
        if not linOnly:
            X = X + self.get_cube_position(raw = True)[:2]
        if rawCoordinates:
            return X
        X = self.XsToXm(X)
        return X
        
        
    #==========================================================================
    #     Linear Stage
    #==========================================================================
    def get_XY_state(self):
        return self.linear_controller.get_state()
    
    def XY_reconnect(self):
        self.linear_controller.reconnect()

    def set_XY_correction(self, coeffs):
        if self.locked:
            self.error.emit('Mouvment is locked!')
            return
        theta, *offset=coeffs
        offset=np.asarray(offset)
        c,s=np.cos(theta),np.sin(theta)
        R=np.array([[c,-s],[s,c]])
        self.R=R
        self.theta = theta
        self.offset=offset/1000
        self.parent.orientationCorrected.emit(np.array([theta, *offset]))
        
    def save_XY_correction(self, fn='XY.txt'):
        np.savetxt(fn, [self.theta, *self.offset*1000] )
        
    def load_XY_correction(self, fn='XY.txt'):
        try:
            self.set_XY_correction(np.loadtxt(fn))
        except FileNotFoundError:
            self.parent.error.emit('No saved correction')
        
    def get_XY_correction(self):
        theta = np.arccos(self.R[0,0])
        offset = self.offset*1000
        return np.array([theta, *offset])
    
    def get_XY_position(self, rawCoordinates = False):
        X = self.linear_controller.get_position()
        X *= 1000 # units
        if rawCoordinates:
            return X
        X = self.XsToXm(X)
        return X
    
    def get_XY_PosRange(self, axis):
        return self.linear_controller.get_pos_range(axis)*1000
    
    def get_XY_VelRange(self, axis):
        return self.linear_controller.get_vel_range(axis)*1000
    
    def get_XY_velocity(self):
        return self.XYSpeed
    
    def set_XY_velocity(self, vel, checkid=None):
        if not self._checklock(checkid):
            return
        
        self.XYSpeed=vel
    
    def goto_XY_position(self, Xm, XsFrom=None, speed=None, wait=False,
                         checkid=None):
        if not self._checklock(checkid):
            return
        if speed is None:
            speed = self.XYSpeed
            
        speed = speed/1000
        if XsFrom is not None:
            XsFrom=np.asarray(XsFrom)/1000
        Xm=np.asarray(Xm)/1000
        Xs=self._getXYStage(Xm)
        self.cube_controller.set_normV(self.cubeSpeed)
        self.cube_controller.goto_position([0,0,0],wait=wait)
        self.linear_controller.set_normV(speed)
        self.linear_controller.goto_position(Xs, Xfrom=XsFrom,wait=wait)
        return Xs*1000
    
    
    #==========================================================================
    #     Cube Stage
    #==========================================================================    
    def get_cube_state(self):
        return self.cube_controller.get_state()
    
    def cube_reconnect(self):
        self.cube_controller.reconnect()
    
    def set_Z_correction(self, coeffs):
        if self.locked:
            self.error.emit('Mouvment is locked!')
            return
        self.zcoeff=coeffs
        self.parent.tiltCorrected.emit(coeffs)
        
    def save_Z_correction(self, fn='Z.txt'):
        np.savetxt(fn, self.zcoeff )
        
    def load_Z_correction(self, fn='Z.txt'):
        try:
            self.set_Z_correction(np.loadtxt(fn))
        except FileNotFoundError:
            self.parent.error.emit('No saved correction')
        
        
    def get_Z_correction(self):
        return self.zcoeff
    
    def get_cube_position(self, raw = False):
        X = self.cube_controller.get_position()
        if raw:
            return X
        X = self._get_cube_Xm(X)
        return X
      
    def get_cube_PosRange(self, axis):
        return self.cube_controller.get_pos_range(axis)
    
    def get_cube_VelRange(self, axis):
        return self.cube_controller.get_vel_range(axis)
    
    def get_cube_velocity(self):
        return self.cubeSpeed
    
    def set_cube_velocity(self, vel, checkid=None):
        if not self._checklock(checkid):
            return
        self.cubeSpeed = vel
        
    def goto_cube_position(self, XMasterCube, XsFrom=None, speed=None,
                 rawPos=False, XStageOrigin=None, wait=False, checkid=None):
        
        if not self._checklock(checkid):
            return

        if speed is None:
            speed = self.cubeSpeed
         
        if rawPos:
            Xs=XMasterCube
        else:
            Xs = self._get_cube_Xs(XMasterCube, XStageOrigin)
        
        self.cube_controller.set_normV(speed)
        self.cube_controller.goto_position(Xs, Xfrom=XsFrom, wait=wait)
        return Xs
        
        

        