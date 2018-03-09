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

from .coordinates_solver import XmtoXs, XstoXm

if sys.platform == "darwin":
    from controllers.stage_controller_placeholder import (linear_controller,
                                                          cube_controller,
                                                          z_controller)
else:
    from controllers.stage_controller import (linear_controller,
                                              cube_controller,
                                              z_controller)


class movement_delegate(QtCore.QObject):
    updatePosition = QtCore.pyqtSignal()

    def __init__(self, parent):
        super().__init__()
        self.mutex = QtCore.QMutex()
        self.locked = False
        self.lockid = None

        self.parent = parent

        self._piezzo = piezzo(self)
        self._motor = motor(self)

        self.error = self.parent.error

        self.coordinatesCorrected = self.motor.coordinatesCorrected

    @property
    def piezzo(self):
        return self._piezzo

    @property
    def motor(self):
        return self._motor

    def _checklock(self, lockid=None):

        QtCore.QMutexLocker(self.mutex)

        if not self.locked:
            return True
        elif self.lockid == lockid:
            return True
        else:
            raise RuntimeError('Mouvment is locked!')

    def lock(self):

        QtCore.QMutexLocker(self.mutex)

        if not self._checklock(None):
            return None

        self.locked = True
        self.lockid = random.randint(0, 100)
        return self.lockid

    def unlock(self):

        QtCore.QMutexLocker(self.mutex)

        self.locked = False
        self.lockid = None

    def stop(self):

        QtCore.QMutexLocker(self.mutex)

        self.piezzo.stop()
        self.motor.stop()

    def ESTOP(self):

        QtCore.QMutexLocker(self.mutex)

        self.piezzo.ESTOP()
        self.motor.ESTOP()

    def is_onTarget(self):

        QtCore.QMutexLocker(self.mutex)

        return (self.piezzo.is_onTarget()
                and self.motor.is_onTarget())

    @property
    def is_ready(self):

        QtCore.QMutexLocker(self.mutex)

        return self.motor.is_ready() and self.piezzo.is_ready()

    #==========================================================================
    #     Corrections
    #==========================================================================

    def save_corrections(self):

        QtCore.QMutexLocker(self.mutex)

        fn = 'corrections.txt'
        with open(fn, 'w') as f:
            mydict = {'motor': self.motor.corrections,
                      'piezzo': self.piezzo.corrections}

            def ndtolist(array):
                if isinstance(array, np.ndarray):
                    return list(array)
                raise TypeError("Unknown Type")

            json.dump(mydict, f, indent=4, default=ndtolist)

    def load_corrections(self):

        QtCore.QMutexLocker(self.mutex)

        fn = 'corrections.txt'
        try:
            with open(fn, 'r') as f:
                corrections = json.load(f)
        except FileNotFoundError:
            self.parent.error.emit('No saved correction')
        self.motor.corrections = corrections['motor']
        self.piezzo.corrections = corrections['piezzo']


class controller(QtCore.QObject):

    move_signal = QtCore.pyqtSignal(list, float)
    coordinatesCorrected = QtCore.pyqtSignal(dict)

    def __init__(self, speed, parent):
        super().__init__()
        self.mutex = QtCore.QMutex()
        self._speed = speed
        self.parent = parent
        self._lastXs = None
        self._ndim = 3
        self._corrections = {}
        self.reset_corrections()

    def reset_corrections(self):
        self.corrections = {
            "offset": np.zeros(3, float),
            "rotation angles": np.zeros(4, float)
        }

    def get_position(self, raw=False):

        QtCore.QMutexLocker(self.mutex)

        X = self._XSPOS()
        if not raw:
            X = self.XstoXm(X)

        return X

    def goto_position(self, Xm, speed=np.nan, wait=False, checkid=None,
                      useLastPos=False, isRaw=False):

        QtCore.QMutexLocker(self.mutex)

        """
        Any value of Xm set to nan will not be moved
        """

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
            Xm = self.XstoXm(Xs)
        else:
            if np.any(toreplace):
                Xm[toreplace] = self.XstoXm(XsFrom)[toreplace]
            Xs = self.XmtoXs(Xm)

        self.move_signal.emit(list(Xm), speed)
        self._lastXs = Xs

        # Don't move if final = now
        if np.linalg.norm(Xs - XsFrom) < 1e-3:
            return

        # Get correct speed for each axis
        Xdist = (Xs - XsFrom)
        Xtime = np.linalg.norm(Xdist) / speed
        V = np.abs(Xdist / Xtime)

        # Move
        self._MOVVEL(Xs, V)

        # Wait for movment to end
        if wait:
            time.sleep(Xtime)
            self.wait_end_motion()

    position = property(get_position, goto_position)

    def wait_end_motion(self):

        QtCore.QMutexLocker(self.mutex)

        while not self.is_onTarget():
            time.sleep(.01)

    def move_by(self, dX, wait=False, checkid=None):

        QtCore.QMutexLocker(self.mutex)

        """Move by dX. This is an easy way but makes a lot of calls"""
        Xm = dX + self.position
        self.goto_position(Xm, wait=wait, checkid=checkid)

    def get_positionRange(self, axis=None):

        QtCore.QMutexLocker(self.mutex)

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

        QtCore.QMutexLocker(self.mutex)

        return self._speed

    def set_velocity(self, vel, checkid=None):

        QtCore.QMutexLocker(self.mutex)

        if not self.parent._checklock(checkid):
            return
        self._speed = vel

    velocity = property(get_velocity, set_velocity)

    def get_velocityRange(self, axis=None):

        QtCore.QMutexLocker(self.mutex)

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

        QtCore.QMutexLocker(self.mutex)

        return self._corrections

    @corrections.setter
    def corrections(self, corrections):

        QtCore.QMutexLocker(self.mutex)
        self._corrections["offset"] = np.asarray(corrections["offset"])
        self._corrections["rotation angles"] = np.asarray(
            corrections["rotation angles"])
        self.coordinatesCorrected.emit(self._corrections)

    def set_correction_key(self, key, value):
        self._corrections[key] = value
        self.coordinatesCorrected.emit(self._corrections)

    def reconnect(self):

        QtCore.QMutexLocker(self.mutex)

        pass

    def XstoXm(self, Xs):

        QtCore.QMutexLocker(self.mutex)

        return XstoXm(Xs, self._corrections["offset"],
                      self._corrections["rotation angles"])

    def XmtoXs(self, Xm):

        QtCore.QMutexLocker(self.mutex)

        return XmtoXs(Xm, self._corrections["offset"],
                      self._corrections["rotation angles"])

    def set_Z_zero(self):

        QtCore.QMutexLocker(self.mutex)
        
        actualZ = self.position[2]
        offset = np.asarray(self.corrections["offset"], float)
        
        offset[2] += actualZ
        self.corrections["offset"] = offset
        self.coordinatesCorrected.emit(self.corrections)

    def offset_origin(self, newXm):
        corrections = self.corrections
        offset = corrections["offset"]
        offset = np.asarray(offset, float)
        oldXm = self.position
        offset += oldXm - newXm
        corrections["offset"] = offset
        self.corrections = corrections

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

    def _MOVVEL(self, Xs, V):
        pass

    def _XSRANGE(self, axis):
        pass

    def _VRANGE(self, axis):
        pass



    
class motor(controller):
    def __init__(self, parent):
        super().__init__(1000, parent)
        self.mutex = QtCore.QMutex()
        self.XY_c = linear_controller()
        self.XY_c.waitState()
        
        self.motor_z = z_controller()
        self.piezzo_z = zpiezzoController(parent, self.motor_z)
        
        self.Z_c = self.motor_z
        
    def switch_z_controller(self, piezzo):
        self.wait_end_motion()
        if piezzo:
            self.Z_c = self.piezzo_z
        else:
            self.Z_c = self.motor_z
            
        self.coordinatesCorrected.emit(self._corrections)

    def _XSPOS(self):

        QtCore.QMutexLocker(self.mutex)

        XY = self.XY_c.get_position()
        Z = self.Z_c.get_position()
        X = np.asarray([*XY, Z])
        return X

    def _MOVVEL(self, Xs, V):

        QtCore.QMutexLocker(self.mutex)

        self.XY_c.MOVVEL(Xs[:2], V[:2])
        self.Z_c.MOVVEL(Xs[2:], V[2:])

    def is_onTarget(self):

        QtCore.QMutexLocker(self.mutex)

        return (self.XY_c.is_onTarget() and self.Z_c.is_onTarget())

    def _XSRANGE(self, axis):

        QtCore.QMutexLocker(self.mutex)

        if axis < 2:
            return self.XY_c.get_pos_range(axis)
        elif axis == 2:
            return self.Z_c.get_pos_range(0)
        return [np.nan, np.nan]

    def _VRANGE(self, axis):

        QtCore.QMutexLocker(self.mutex)

        if axis < 2:
            return self.XY_c.get_vel_range(axis)
        elif axis == 2:
            return self.Z_c.get_vel_range(0)
        return [np.nan, np.nan]

    def stop(self, wait=False, checkid=None):

        QtCore.QMutexLocker(self.mutex)

        self.XY_c.stop()
        self.Z_c.stop()

    def ESTOP(self):
        self.XY_c.ESTOP()
        self.Z_c.ESTOP()

    def is_ready(self):

        QtCore.QMutexLocker(self.mutex)

        return self.XY_c.is_ready() and self.Z_c.is_ready()

    def reconnect(self):

        QtCore.QMutexLocker(self.mutex)

        self.XY_c.reconnect()
        self.Z_c.reconnect()


class piezzo(controller):
    def __init__(self, parent):
        super().__init__(1000, parent)
        self.mutex = QtCore.QMutex()
        self.XYZ_c = cube_controller()
        self.XYZ_c.stageConnected.connect(lambda: self.reset())
        self.XYZ_c.connect()

    def reset(self, checkid=None, wait=False):

        QtCore.QMutexLocker(self.mutex)

        self.reset_corrections()
        self.goto_position([0, 0, 0], checkid=checkid, wait=wait)

    def _XSPOS(self):

        QtCore.QMutexLocker(self.mutex)

        return np.asarray(self.XYZ_c.get_position())

    def _MOVVEL(self, Xs, V):

        QtCore.QMutexLocker(self.mutex)
        try:
            self.XYZ_c.MOVVEL(Xs, V)
        except self.XYZ_c.error:
            print("Error at ", Xs)
            raise

    def is_onTarget(self):

        QtCore.QMutexLocker(self.mutex)

        return self.XYZ_c.is_onTarget()

    def _XSRANGE(self, axis):

        QtCore.QMutexLocker(self.mutex)

        ret = self.XYZ_c.get_pos_range(axis)
        return ret

    def _VRANGE(self, axis):

        QtCore.QMutexLocker(self.mutex)

        return self.XYZ_c.get_vel_range(axis)

    def stop(self):

        QtCore.QMutexLocker(self.mutex)

        self.XYZ_c.stop()

    def ESTOP(self):
        self.XYZ_c.ESTOP()

    def is_ready(self):

        QtCore.QMutexLocker(self.mutex)

        return self.XYZ_c.is_ready()

    def reconnect(self):

        QtCore.QMutexLocker(self.mutex)

        self.XYZ_c.reconnect()
        
class zpiezzoController():
    
    def __init__(self, md, motor_z_controller):
        self.motor_c = motor_z_controller
        self.piezzo = md.piezzo
        
    def get_position(self):
        return self.motor_c.get_position() + self.piezzo.XYZ_c.get_position()[2]
    
    def MOVVEL(self, Xs, V):
        piezzo_pos = self.piezzo.get_position(raw=True)
        piezzo_pos[2] = Xs[0]-self.motor_c.get_position()
        self.piezzo.XYZ_c.MOVVEL(piezzo_pos, [0, 0, V[0]])
        self.piezzo.move_signal.emit(list(self.piezzo.XstoXm(piezzo_pos)), V)
    
    def is_onTarget(self,):
        return self.piezzo.XYZ_c.is_onTarget()
    
    def get_pos_range(self, axis):
        return self.piezzo.XYZ_c.get_pos_range(2) + self.motor_c.get_position()
    
    def get_vel_range(self, axis):
        return self.piezzo.XYZ_c.get_vel_range(2)
    
    def stop(self,):
        self.piezzo.stop()
        
    def ESTOP(self,):
        self.piezzo.ESTOP()
        
    def is_ready(self,):
        self.piezzo.is_ready()
        
    def reconnect(self,):
        pass

#    def _get_angle_matrices(self):
#
#        QtCore.QMutexLocker(self.mutex)
#
#        theta = self._corrections["rotation angle"]
#        phi = self._corrections["stage diff angle"]
#
#        c, s = np.cos(theta), np.sin(theta)
#        R = np.array([[c, -s], [s, c]])
#
#        c, s = np.cos(phi), np.sin(phi)
#        M = np.array([[1, s], [0, c]])
#
#        return R, M
#    def _getZPlane(self, XYstage):
#        return np.dot(self._corrections["slope"], XYstage)
#
#    def XstoXm(self, Xs):
#
#        QtCore.QMutexLocker(self.mutex)
#        R, M = self._get_angle_matrices()
#
#        Xm = np.array(Xs, float)
#        Xm[:2] = M@Xs[:2]
#        Xm -= self._corrections['offset']
#        Xm[:2] = np.linalg.inv(R)@Xm[:2]
#        Xm[2] -= self._getZPlane(Xs[:2])
#        return Xm
#
#    def XmtoXs(self, Xm):
#
#        QtCore.QMutexLocker(self.mutex)
#
#        R, M = self._get_angle_matrices()
#
#        Xs = np.array(Xm, float)
#        Xs[:2] = R@Xm[:2]
#        Xs += self._corrections['offset']
#        Xs[:2] = np.linalg.inv(M)@Xs[:2]
#        Xs[2] += self._getZPlane(Xs[:2])
#        return Xs
