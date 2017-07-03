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

################
Abstract away the different stages, put all units to um, 
Changes coordinates to be corrected
"""

import random
import numpy as np
from PyQt5 import QtCore
import sys
import time

if sys.platform == "darwin":
    from controllers.stage_controller_placeholder import (linear_controller, 
                                                          cube_controller,
                                                          z_controller)
else:
    from controllers.stage_controller import (linear_controller, 
                                              cube_controller,
                                              z_controller)



class controller():
    def __init__(self, speed, parent):
        super().__init__()
        self._speed = speed
        self.parent = parent
        self._lastXs = None
        self.zcoeff = np.zeros(3)
        self.ndim = 3
      
    
   
    def get_position(self, raw=False):
        X = self._XSPOS()
        if not raw:
            X = self.XstoXm(X)
        return X
   
    def goto_position(self, Xm, speed=np.nan, wait=False, checkid=None, 
                      useLastPos=False, isRaw=False):
        #Check lock
        if not self.parent._checklock(checkid):
            return
        
        #Choose speed
        if np.isnan(speed):
            speed = self._speed
        
        #get starting point
        XsFrom = None
        if useLastPos:
            XsFrom = self._lastXs
        else:
            XsFrom = self._XSPOS()
        
        #Get final point
        if isRaw:
            Xs=Xm
        else:
            Xs=self.XmtoXs(Xm)
        
        self._lastXs = Xs
        
        #Don't move if final = now
        if np.all(Xs == XsFrom):
            return
        
        #Get correct speed for each axis   
        Xdist=(Xs-XsFrom)
        Xtime=np.linalg.norm(Xdist)/speed
        V=Xdist/Xtime
        
        #Move
        self._MOVVEL(Xs, V)
        
        #Wait for movment to end
        if wait:
            time.sleep(Xtime)
            while not self.is_onTarget():
                time.sleep(.01)
                
    position =  property(get_position, goto_position)
                
    def get_positionRange(self, axis=None):
        ret = np.zeros((self.ndim,2))
        for i in range(self.ndim):
            ret[i,:] = self._XSRANGE(i)

        Xss = np.stack(np.meshgrid(*ret), -1).reshape(-1, 3)
        Xms = np.apply_along_axis(self.XstoXm, 1, Xss)
        ret[:,0] = np.min(Xms,0)
        ret[:,1] = np.max(Xms,0)
        return ret

    positionRange = property(get_positionRange)
    
    def get_velocity(self):
        return self._speed
    
    def set_velocity(self, vel, checkid=None):
        if not self.parent._checklock(checkid):
            return
        self._speed=vel
        
    velocity = property(get_velocity, set_velocity)
        
    def get_velocityRange(self, axis=None):
        if axis is None:
            axis = np.arange(3)
        axis = np.ravel(axis)
        ret = np.zeros((len(axis),2))
        for i,r in zip(axis, ret):
            r[:] = self._VRANGE(i)
        return np.squeeze(ret)   
    
    velocityRange = property(get_velocityRange)
    
    def set_Z_correction(self, coeffs):
        self.zcoeff = coeffs

    def state(self):
        pass
    
    def reconnect(self):
        pass      
                
    def _getZOrigin(self, XYstage):
        return np.dot(self.zcoeff[:2],XYstage) + self.zcoeff[2]
    
    def XstoXm(self, Xs):
        pass
    
    def XmtoXs(self, Xm):
        pass
    
    def is_onTarget(self):
        pass
    
    def _XSPOS(self):
        pass
           
    def _MOVVEL(self, Xs, V):
        pass
    
    def _XSRANGE(self, axis):
        pass
    
    def _VRANGE(self, axis):
        pass
    
    def ESTOP(self):
        pass

class motor(controller):
    def __init__(self, parent):
        super().__init__(1000, parent)
        self.XY_c = linear_controller()
        self.Z_c = z_controller()
        self.R = np.eye(2)
        self.M = np.eye(2)
        self.offset = np.zeros(2)
        self.ndim = 3
        
    def XstoXm(self, Xs):
        Xm = np.array(Xs)
        Xm[:2] = np.linalg.inv(self.R)@(self.M@Xs[:2]-self.offset)
        Xm[2] = Xs[2] - self._getZOrigin(Xs[:2])
        return Xm
    
    def XmtoXs(self, Xm):
        Xs = np.array(Xm)
        Xs[:2] = np.linalg.inv(self.M)@(self.R@Xm[:2]+self.offset)
        Xs[2] = Xm[2] + self._getZOrigin(Xs[:2])
        return Xs
    
    def _XSPOS(self):
        XY = self.XY_c.get_position()
        Z = self.Z_c.get_position()
        X = np.asarray([*XY, Z])
        X *= 1000 # units
        return X
            
    def _MOVVEL(self, Xs, V):
        self.parent.piezzo.motorMove()
        V=V/1000
        Xs=Xs/1000
        self.XY_c.MOVVEL(Xs[:2], V[:2])
        self.Z_c.MOVVEL(Xs[2:], V[2:])
        
    def is_onTarget(self):
        return (self.XY_c.is_onTarget() and self.Z_c.is_onTarget())
    
    def _XSRANGE(self, axis):
        if axis<2:
            return self.XY_c.get_pos_range(axis)*1000
        elif axis==2:
            return self.Z_c.get_pos_range(0)*1000
        return [np.nan, np.nan]
    
    def _VRANGE(self, axis):
        if axis<2:
            return self.XY_c.get_vel_range(axis)*1000
        elif axis==2:
            return self.Z_c.get_vel_range(0)*1000
        return [np.nan, np.nan]
    
    def ESTOP(self):
        self.XY_c.ESTOP()
        self.Z_c.ESTOP()
      
    def state(self):
        return self.XY_c.get_state() and self.Z_c.get_state()
    
    def reconnect(self):
        self.XY_c.reconnect()
        self.Z_c.reconnect()
        
    def set_XY_correction(self, R, M, offset):
        self.R = R
        self.M = M
        self.offset = offset
    
    
class piezzo(controller):
    def __init__(self, parent):
        super().__init__(1000, parent)
        self.XYZ_c = cube_controller() 
        self.R = np.eye(2)
        self.offset = np.array([50, 50, 25])
        self.ndim = 3
        
    def motorMove(self):
        self.goto_position([0,0,0], isRaw=True)
        self.zcoeff = np.zeros(3)
        
    def XstoXm(self, Xs):
        Xm = np.array(Xs) + self.offset      
        Xm[:2] = np.linalg.inv(self.R)@Xs[:2]
        Xm[2] = Xs[2] - self._getZOrigin(Xs[:2])
        return Xm 
    
    def XmtoXs(self, Xm):
        Xs = np.array(Xm)
        Xs[:2] = self.R@Xm[:2]
        Xs[2] = Xm[2] + self._getZOrigin(Xs[:2])
        return Xs - self.offset

    def _XSPOS(self):
        return self.XYZ_c.get_position()
           
    def _MOVVEL(self, Xs, V):
        self.XYZ_c.MOVVEL(Xs, V)
        
    def is_onTarget(self):
        return self.XYZ_c.is_onTarget()
    
    def _XSRANGE(self, axis):
        return self.XYZ_c.get_pos_range(axis)
    
    def _VRANGE(self, axis):
        return self.XYZ_c.get_vel_range(axis)    
    
    def ESTOP(self):
        self.XYZ_c.ESTOP()
        
    def state(self):
        return self.XYZ_c.get_state()
    
    def reconnect(self):
        self.XYZ_c.reconnect()
        
    def set_XY_correction(self, R):
        self.R = R
        

class mouvment_delegate(QtCore.QObject): 
    
    def __init__(self, parent):
        super().__init__()
        self.locked = False
        self.lockid = None
        
        self.parent = parent
        self.XYcorr = np.zeros(4)
        self.zcoeff = np.zeros(3)
        
        self.piezzo = piezzo(self)
        self.motor = motor(self)
        
        self.error = self.parent.error
    
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
        self.piezzo.ESTOP()
        self.motor.ESTOP()
        
    def is_onTarget(self):
        return (self.piezzo.is_onTarget()
                and self.motor.is_onTarget())
    
    @property
    def position(self):
        return self.motor.position + self.piezzo.position
    
    @property
    def state(self):
        return self.motor.state and self.piezzo.state
        
    #==========================================================================
    #     XY Correction
    #==========================================================================

    def set_XY_correction(self, coeffs):
        if self.locked:
            self.error.emit('Mouvment is locked!')
            return
        coeffs = np.array(coeffs)
        phi, theta, *offset=coeffs
        offset=np.asarray(offset)
        c,s=np.cos(theta),np.sin(theta)
        R=np.array([[c,-s],[s,c]])
        c,s=np.cos(phi),np.sin(phi)
        M=np.array([[1,s],[0,c]])
        
        self.XYcorr = coeffs
        
        self.motor.set_XY_correction(R, M, offset)
        self.piezzo.set_XY_correction(R)
        
        self.parent.orientationCorrected.emit(coeffs)
        
    def save_XY_correction(self, fn='XY.txt'):
        np.savetxt(fn, self.XYcorr)
        
    def load_XY_correction(self, fn='XY.txt'):
        try:
            self.set_XY_correction(np.loadtxt(fn))
        except FileNotFoundError:
            self.parent.error.emit('No saved correction')
        
    def get_XY_correction(self):
        return np.array(self.XYcorr)
    
    
    #==========================================================================
    #     Z Correction
    #==========================================================================        
   
    def set_Z_correction(self, coeffs):
        if self.locked:
            self.error.emit('Mouvment is locked!')
            return
        self.zcoeff=coeffs
        self.motor.set_Z_correction(coeffs)
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
    
    
        
    
        
        

        