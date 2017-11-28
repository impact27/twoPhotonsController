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
import json

if sys.platform == "darwin":
    from controllers.stage_controller_placeholder import (linear_controller,
                                                          cube_controller,
                                                          z_controller)
else:
    from controllers.stage_controller import (linear_controller,
                                              cube_controller,
                                              z_controller)

class mouvment_delegate(QtCore.QObject):
    updatePosition = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self.locked = False
        self.lockid = None

        self.parent = parent

        self.piezzo = piezzo(self)
        self.motor = motor(self)

        self.error = self.parent.error
        
        self.coordinatesCorrected = self.motor.coordinatesCorrected

    def _checklock(self, lockid=None):
        if not self.locked:
            return True
        elif self.lockid == lockid:
            return True
        else:
            raise RuntimeError('Mouvment is locked!')

    def lock(self):
        if not self._checklock(None):
            return None

        self.locked = True
        self.lockid = random.randint(0, 100)
        return self.lockid

    def unlock(self):
        self.locked = False
        self.lockid = None
        
    def stop(self):
        self.piezzo.stop()
        self.motor.stop()

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
    def is_ready(self):
        return self.motor.is_ready() and self.piezzo.is_ready()

    #==========================================================================
    #     Corrections
    #==========================================================================

    def save_corrections(self):
        fn = 'corrections.txt'
        with open(fn, 'w') as f:
            json.dump(self.corrections, f, indent=4)

    def load_corrections(self):
        fn = 'corrections.txt'
        try:
            with open(fn, 'r') as f:
                corrections = json.load(f)
        except FileNotFoundError:
            self.parent.error.emit('No saved correction')
        self.corrections = corrections
    
    @property
    def corrections(self):
        return self.motor.corrections
    
    @corrections.setter
    def corrections(self, corrections):
        self.motor.corrections = corrections
        self.piezzo.corrections['rotation angle'] = corrections['rotation angle']
    
    
class controller(QtCore.QObject):

    move_signal = QtCore.pyqtSignal(list, float)
    coordinatesCorrected = QtCore.pyqtSignal(dict)

    def __init__(self, speed, parent):
        super().__init__()
        self._speed = speed
        self.parent = parent
        self._lastXs = None
        self._ndim = 3
        
        self._corrections={
                "offset": np.zeros(3),
                "slope": np.zeros(2),
                "rotation angle": 0,
                "stage diff angle": 0
                }

    def get_position(self, raw=False):
        X = self._XSPOS()
        if not raw:
            X = self.XstoXm(X)

        return X

    def goto_position(self, Xm, speed=np.nan, wait=False, checkid=None,
                      useLastPos=False, isRaw=False):
        """

        Any value of Xm set to nan will not be moved
        """
        self.move_signal.emit(list(Xm), speed)
        Xm = np.asarray(Xm)
        # Check lock
        if not self.parent._checklock(checkid):
            return

        # Choose speed
        if np.isnan(speed):
            speed = self._speed

        # get starting point
        XsFrom = None
        if useLastPos:
            XsFrom = self._lastXs
        else:
            XsFrom = self._XSPOS()

        # points to replace
        toreplace = np.isnan(Xm)
        # Get final point
        if isRaw:
            Xs = Xm
            Xs[toreplace] = XsFrom[toreplace]
        else:
            if np.any(toreplace):
                Xm[toreplace] = self.XstoXm(XsFrom)[toreplace]
            Xs = self.XmtoXs(Xm)

        self._lastXs = Xs

        # Don't move if final = now
        if np.linalg.norm(Xs - XsFrom) < 1e-3:
            return

        # Get correct speed for each axis
        Xdist = (Xs - XsFrom)
        Xtime = np.linalg.norm(Xdist) / speed
        V = np.abs(Xdist / Xtime)

        # Move
        self._MOVVEL(Xs, V, checkid=checkid)

        # Wait for movment to end
        if wait:
            time.sleep(Xtime)
            self.wait_end_motion()

    position = property(get_position, goto_position)

    def wait_end_motion(self):
        while not self.is_onTarget():
            time.sleep(.01)
                
    def move_by(self, dX, wait=False, checkid=None):
        """Move by dX. This is an easy way but makes a lot of calls"""
        Xm = dX + self.position
        self.goto_position(Xm, wait=wait, checkid=checkid)

    def get_positionRange(self, axis=None):
        ret = np.zeros((self._ndim, 2))
        for i in range(self._ndim):
            ret[i, :] = self._XSRANGE(i)

        Xss = np.stack(np.meshgrid(*ret), -1).reshape(-1, 3)
        Xms = np.apply_along_axis(self.XstoXm, 1, Xss)
        ret[:, 0] = np.min(Xms, 0)
        ret[:, 1] = np.max(Xms, 0)
        if axis is not None:
            return ret[axis]
        return ret

    positionRange = property(get_positionRange)

    def get_velocity(self):
        return self._speed

    def set_velocity(self, vel, checkid=None):
        if not self.parent._checklock(checkid):
            return
        self._speed = vel

    velocity = property(get_velocity, set_velocity)

    def get_velocityRange(self, axis=None):
        if axis is None:
            axis = np.arange(3)
        axis = np.ravel(axis)
        ret = np.zeros((len(axis), 2))
        for i, r in zip(axis, ret):
            r[:] = self._VRANGE(i)
        return np.squeeze(ret)

    velocityRange = property(get_velocityRange)
        
    @property
    def corrections(self):
        return self._corrections
    
    @corrections.setter
    def corrections(self, corrections):
        self._corrections = corrections
        self.coordinatesCorrected.emit(corrections)
    
    def _get_angle_matrices(self):
        theta = self._corrections["rotation angle"]
        phi =  self._corrections["stage diff angle"]
        
        c, s = np.cos(theta), np.sin(theta)
        R = np.array([[c, -s], [s, c]])
        
        c, s = np.cos(phi), np.sin(phi)
        M = np.array([[1, s], [0, c]])
        
        return R, M

    def reconnect(self):
        pass

    def XstoXm(self, Xs):
        R, M = self._get_angle_matrices()
        
        Xm = np.array(Xs, float)
        Xm[:2] = M@Xs[:2]
        Xm -= self._corrections['offset']
        Xm[:2] = np.linalg.inv(R)@Xm[:2]
        Xm[2] -= self._getZPlane(Xs[:2])
        return Xm

    def XmtoXs(self, Xm):
        R, M = self._get_angle_matrices()
        
        Xs = np.array(Xm, float)
        Xs[:2] = R@Xm[:2]
        Xs += self._corrections['offset']
        Xs[:2] = np.linalg.inv(M)@Xs[:2]
        Xs[2] += self._getZPlane(Xs[:2])
        return Xs

    def is_ready(self):
        pass
    
    def is_onTarget(self):
        pass
    
    def stop(self, wait=False):
        pass
    
    def ESTOP(self):
        pass

    def _XSPOS(self):
        pass

    def _MOVVEL(self, Xs, V, checkid=None):
        pass

    def _XSRANGE(self, axis):
        pass

    def _VRANGE(self, axis):
        pass
    
    def _getZPlane(self, XYstage):
        return np.dot(self._corrections["slope"], XYstage)


class motor(controller):
    def __init__(self, parent):
        super().__init__(1000, parent)
        self.XY_c = linear_controller()
        self.Z_c = z_controller()
        self.XY_c.waitState()

    def _XSPOS(self):
        XY = self.XY_c.get_position()
        Z = self.Z_c.get_position()
        X = np.asarray([*XY, Z])
        return X

    def _MOVVEL(self, Xs, V, checkid=None):
        self.parent.piezzo.motorMove(checkid=checkid)
        self.XY_c.MOVVEL(Xs[:2], V[:2])
        self.Z_c.MOVVEL(Xs[2:], V[2:])

    def is_onTarget(self):
        return (self.XY_c.is_onTarget() and self.Z_c.is_onTarget())

    def _XSRANGE(self, axis):
        if axis < 2:
            return self.XY_c.get_pos_range(axis)
        elif axis == 2:
            return self.Z_c.get_pos_range(0)
        return [np.nan, np.nan]

    def _VRANGE(self, axis):
        if axis < 2:
            return self.XY_c.get_vel_range(axis)
        elif axis == 2:
            return self.Z_c.get_vel_range(0)
        return [np.nan, np.nan]
    
    def stop(self, wait=False, checkid=None):
        self.XY_c.stop()
        self.Z_c.stop()
        
    def ESTOP(self):
        self.XY_c.ESTOP()
        self.Z_c.ESTOP()

    def is_ready(self):
        return self.XY_c.is_ready() and self.Z_c.is_ready()

    def reconnect(self):
        self.XY_c.reconnect()
        self.Z_c.reconnect()

class piezzo(controller):
    def __init__(self, parent):
        super().__init__(1000, parent)
        self.XYZ_c = cube_controller()
        self._corrections['offset'] = np.array([50, 50, 25])

    def motorMove(self, checkid=None):
        self._corrections['offset'][2] = 25
        self._corrections["slope"] = np.zeros(2)
        self.goto_position([0, 0, 0], checkid=checkid)

    def _XSPOS(self):
        return np.asarray(self.XYZ_c.get_position())

    def _MOVVEL(self, Xs, V, checkid=None):
        self.XYZ_c.MOVVEL(Xs, V)

    def is_onTarget(self):
        return self.XYZ_c.is_onTarget()

    def _XSRANGE(self, axis):
        ret = self.XYZ_c.get_pos_range(axis)
        return ret

    def _VRANGE(self, axis):
        return self.XYZ_c.get_vel_range(axis)
    
    def stop(self):
        self.XYZ_c.stop()

    def ESTOP(self):
        self.XYZ_c.ESTOP()

    def is_ready(self):
        return self.XYZ_c.is_ready()

    def reconnect(self):
        self.XYZ_c.reconnect()



