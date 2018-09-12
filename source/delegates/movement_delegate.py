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

from delegates.coordinates_solver import XmtoXs, XstoXm
from delegates.thread import lockmutex

# If I am on my mac, the stages are not connected
_TEST_ = False
if sys.platform == "darwin":
    _TEST_ = True

if _TEST_:
    from controllers.stage_controller_placeholder import (Linear_controller,
                                                          Cube_controller,
                                                          z_controller,
                                                          Stage_controller)
else:
    from controllers.stage_controller import (Linear_controller,
                                              Cube_controller,
                                              z_controller,
                                              Stage_controller)



class Movement_delegate(QtCore.QObject):
    """Delegate for movement.
    Pretty empty as the motion is done through motor and piezo
    """
    updatePosition = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        self.locked = False
        self.lockid = None

        self._piezo = Piezo(self._checklock, self.error)
        self._motor = Motor(self._checklock, self.error)

        self.motor_z_switcher = Motor_z_switcher(self._motor, self._piezo)

        self.coordinatesCorrected = self.motor.coordinatesCorrected

    # Normal things
    @property
    def piezo(self):
        return self._piezo

    @property
    def motor(self):
        return self._motor

    @lockmutex
    def _checklock(self, lockid=None):
        """Checks if the movement is locked"""

        if not self.locked:
            return True
        elif self.lockid == lockid:
            return True
        else:
            raise RuntimeError('Mouvment is locked!')

    @lockmutex
    def lock(self):
        """Locks the movement"""

        if not self._checklock(None):
            return None

        self.locked = True
        self.lockid = random.randint(0, 100)
        return self.lockid

    @lockmutex
    def unlock(self):
        """Unlocks the movement"""

        self.locked = False
        self.lockid = None

    @lockmutex
    def stop(self):
        """stops the movement"""

        self.piezo.stop()
        self.motor.stop()

    @lockmutex
    def ESTOP(self):
        """Emergency stop"""

        self.piezo.ESTOP()
        self.motor.ESTOP()

    @lockmutex
    def is_onTarget(self):
        """Checks if the stages reached the target"""

        return (self.piezo.is_onTarget()
                and self.motor.is_onTarget())

    @property
    @lockmutex
    def is_ready(self):
        """Checks if the stages are ready"""
        return self.motor.is_ready() and self.piezo.is_ready()

    # ==========================================================================
    #     Corrections
    # ==========================================================================
    @lockmutex
    def save_corrections(self, fn='corrections.txt'):
        """Saves the corrections"""
        mydict = {'motor': self.motor.corrections,
                  'piezo': self.piezo.corrections}

        def ndtolist(array):
            if isinstance(array, np.ndarray):
                return list(array)
            raise TypeError("Unknown Type")
        with open(fn, 'w') as f:
            json.dump(mydict, f, indent=4, default=ndtolist)

    @lockmutex
    def load_corrections(self, fn='corrections.txt'):
        """Loads the corrections"""

        try:
            with open(fn, 'r') as f:
                corrections = json.load(f)
        except FileNotFoundError:
            self.error.emit('No saved correction')
        self.motor.corrections = corrections['motor']
        self.piezo.corrections = corrections['piezo']


# =============================================================================
# Stages
# =============================================================================
class Stage(QtCore.QObject):
    """This is the abstract class that will coordinate the controllers"""
    move_signal = QtCore.pyqtSignal(list, float)
    coordinatesCorrected = QtCore.pyqtSignal(dict)

    def __init__(self, speed, checklock, error_signal):
        super().__init__()
        self._mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        self._speed = speed
        self._checklock = checklock
        self._lastXs = None
        self._ndim = 3
        self._corrections = {}
        self.reset_corrections()
        self.error_signal = error_signal

    # Positions

    @lockmutex
    def get_position(self, raw=False):
        """Returns the (raw?) position"""

        X = self._XSPOS()
        if not raw:
            X = self.XstoXm(X)

        return X

    def goto_position(self, XTo, speed=np.nan, *, wait=False, checkid=None,
                      useLastPos=False, isRaw=False):
        """Moves to the position

        Parameters:
        ----------
            Xm:
                Position to go to [um]
            speed:
                Speed [um/s]
            wait:
                Should the call be blocking?
            checkid:
                If the movment is locked, the checkid
            useLastPos:
                Use for performance. Avoid calling pos()
                (Might be useless)
            isRaw:
                Is Xm raw or corrected?

        Note:
            Any value of Xm set to nan will not be moved
        """

        # Check lock
        if not self._checklock(checkid):
            return
        self._mutex.lock()
        # get starting point
        XsFrom = None
        if useLastPos:
            XsFrom = self._lastXs
        else:
            XsFrom = self._XSPOS()

        XsTo, XmTo, Vs, travel_time = self.move_parameters(
            XTo, XsFrom, speed, isRaw)

        # Don't move if final = now
        if np.linalg.norm(XsTo - XsFrom) < 1e-3:
            self._mutex.unlock()
            return

        # Move
        self.move_signal.emit(list(XmTo), speed)
        self._MOVVEL(XsTo, Vs)
        self._mutex.unlock()
        # Wait for movment to end
        if wait:
            self.wait_end_motion(travel_time, 10)

    def move_parameters(self, XTo, XsFrom, speed, isRaw):
        """Get parameters needed to move the stages"""
        # Choose speed
        if np.isnan(speed):
            speed = self._speed

        XTo = np.asarray(XTo)
        # points to replace
        toreplace = np.isnan(XTo)
        # Get final point
        if isRaw:
            XsTo = XTo
            XsTo[toreplace] = XsFrom[toreplace]
            XmTo = self.XstoXm(XsTo)
        else:
            XmTo = XTo
            if np.any(toreplace):
                XmTo[toreplace] = self.XstoXm(XsFrom)[toreplace]
            XsTo = self.XmtoXs(XmTo)

        # Get correct speed for each axis
        Xdist = (XsTo - XsFrom)
        travel_time = np.linalg.norm(Xdist) / speed
        if travel_time > 0:
            Vs = np.abs(Xdist / travel_time)
        else:
            Vs = np.abs(Xdist)
        return XsTo, XmTo, Vs, travel_time

    position = property(get_position, goto_position)

    def wait_end_motion(self, travel_time, timeout=None):
        """Wait hte ned of motion"""

        time.sleep(travel_time)
        tstart = time.time()
        while not self.is_onTarget():
            if timeout is not None and time.time() - tstart > timeout:
                raise RuntimeError('The motion took too long to complete')
            time.sleep(.01)

    def move_by(self, dX, wait=False, checkid=None):
        """Move by dX. Conveninence wrapper around goto_position"""

        Xm = dX + self.position
        self.goto_position(Xm, wait=wait, checkid=checkid)

    @lockmutex
    def get_positionRange(self, axis=None):
        """Get position range. This is almost correct.
        (See corrections)"""

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

    @lockmutex
    def get_velocity(self):

        return self._speed

    @lockmutex
    def set_velocity(self, vel, checkid=None):
        if not self._checklock(checkid):
            return
        self._speed = vel

    velocity = property(get_velocity, set_velocity)

    @lockmutex
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
    @lockmutex
    def corrections(self, corrections):
        self._corrections["offset"] = np.asarray(corrections["offset"])
        self._corrections["rotation angles"] = np.asarray(
            corrections["rotation angles"])
        self.coordinatesCorrected.emit(self._corrections)

    def set_correction_key(self, key, value):
        self._corrections[key] = value
        self.coordinatesCorrected.emit(self._corrections)

    def reset_corrections(self):
        self.corrections = {
            "offset": np.zeros(3, float),
            "rotation angles": np.zeros(4, float)
        }

    @lockmutex
    def reconnect(self):
        pass

    @lockmutex
    def XstoXm(self, Xs):
        return XstoXm(Xs, self._corrections["offset"],
                      self._corrections["rotation angles"])

    @lockmutex
    def XmtoXs(self, Xm):
        return XmtoXs(Xm, self._corrections["offset"],
                      self._corrections["rotation angles"])

    @lockmutex
    def set_Z_zero(self):
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


class Motor(Stage):
    """Motor stage"""

    def __init__(self, checklock, error_signal):
        super().__init__(1000, checklock, error_signal)
        self.XY_c = Linear_controller()
        self.Z_c = z_controller()
        self._lastXs = self._XSPOS()

    @lockmutex
    def _XSPOS(self):
        XY = self.XY_c.get_position()
        Z = self.Z_c.get_position()
        X = np.asarray([*XY, Z])
        return X

    @lockmutex
    def _MOVVEL(self, Xs, V):
        self._lastXs = Xs
        self.XY_c.MOVVEL(Xs[:2], V[:2])
        self.Z_c.MOVVEL(Xs[2:], V[2:])

    @lockmutex
    def is_onTarget(self):
        return (self.XY_c.is_onTarget() and self.Z_c.is_onTarget())

    @lockmutex
    def _XSRANGE(self, axis):
        if axis < 2:
            return self.XY_c.get_pos_range(axis)
        elif axis == 2:
            return self.Z_c.get_pos_range(0)
        return [np.nan, np.nan]

    @lockmutex
    def _VRANGE(self, axis):
        if axis < 2:
            return self.XY_c.get_vel_range(axis)
        elif axis == 2:
            return self.Z_c.get_vel_range(0)
        return [np.nan, np.nan]

    @lockmutex
    def stop(self, wait=False, checkid=None):
        self.XY_c.stop()
        self.Z_c.stop()

    def ESTOP(self):
        self.XY_c.ESTOP()
        self.Z_c.ESTOP()

    @lockmutex
    def is_ready(self):
        return self.XY_c.is_ready() and self.Z_c.is_ready()

    @lockmutex
    def reconnect(self):
        self.XY_c.reconnect()
        self.Z_c.reconnect()


class Piezo(Stage):
    """Piezo stage"""

    def __init__(self, checklock, error_signal):
        super().__init__(1000, checklock, error_signal)
        self.XYZ_c = Cube_controller()
        self.XYZ_c.stageConnected.connect(self.reset)
        self.recording_macro = False
        self._lastXs = self._XSPOS()

    def reset(self, checkid=None, wait=False):
        self.reset_corrections()
        self.goto_position([0, 0, 0], checkid=checkid, wait=wait)

    @lockmutex
    def _XSPOS(self):
        return np.asarray(self.XYZ_c.get_position())

    @lockmutex
    def _MOVVEL(self, Xs, V):
        try:
            self._lastXs = Xs.copy()
            self.XYZ_c.MOVVEL(Xs, V)
            if self.recording_macro:
                self.XYZ_c.macro_wait()
        except self.XYZ_c.error as e:
            self.error_signal.emit("Error at " + str(Xs) + str(e))
            raise

    @lockmutex
    def is_onTarget(self):
        return np.all(self.XYZ_c.is_onTarget())

    @lockmutex
    def _XSRANGE(self, axis):
        ret = self.XYZ_c.get_pos_range(axis)
        return ret

    @lockmutex
    def _VRANGE(self, axis):
        return self.XYZ_c.get_vel_range(axis)

    @lockmutex
    def stop(self):
        self.XYZ_c.stop()

    def ESTOP(self):
        self.XYZ_c.ESTOP()

    @lockmutex
    def is_ready(self):
        return self.XYZ_c.is_ready()

    @lockmutex
    def macro_begin(self, name):
        self.recording_macro = True
        self.XYZ_c.MAC_BEG(name)

    @lockmutex
    def macro_end(self):
        self.recording_macro = False
        self.XYZ_c.MAC_END()

   
    def macro_start(self, name, wait=True):
        self._mutex.lock()
        self.XYZ_c.MAC_START(name)
        self._mutex.unlock()
        if wait:
            time.sleep(1)
            while self.is_macro_running():
                time.sleep(1)

    @lockmutex
    def macro_delete(self, name):
        self.XYZ_c.MAC_DEL(name)

    @lockmutex
    def macro_exists(self, name):
        return self.XYZ_c.macro_exists(name)

    @lockmutex
    def is_macro_running(self):
        return self.XYZ_c.is_macro_running()

    @property
    @lockmutex
    def isRecordingMacro(self):
        return self.XYZ_c.isRecordingMacro

    
    def run_waveform(self, time_step, X, wait=True):
        self._mutex.lock()
        # Get stage coordinates
        X[:, :3] = self.XmtoXs(X[:, :3])
        self._lastXs = X[-1, :3].copy()
        wait_time = self.XYZ_c.run_waveform(time_step, X)
        self._mutex.unlock()
        if wait:
            self.XYZ_c.wait_end_wave(wait_time)

    def controller_mutex(self):
        return self._mutex


class Motor_z_switcher():
    """Thus class is tasked with changing the z controller of the motor stage.
    This is slightly ugly so don't look too closely.

    It will basically mix motor and piezo.
    """

    def __init__(self, motor, piezo):
        super().__init__()
        self.motor = motor
        self.piezo = piezo
        self.piezo_z_controller = Piezo_z(piezo)
        self.motor_z_controller = motor.Z_c

    # Change Z slice
    def moved_z_controller(self, Zs):
        motor_pos = self.motor.get_position(raw=True)
        motor_pos[2] = Zs
        self.motor.move_signal.emit(list(self.motor.XstoXm(motor_pos)),
                                    self.motor._speed)

    def switch(self, piezo):
        if piezo:
            self.motor.wait_end_motion()
            self.piezo_z_controller.set_offset(self.motor.Z_c.get_position())
            self.motor.Z_c = self.piezo_z_controller
#            self.piezo_z_controller.move_signal.connect(self.moved_z_controller)
        else:
            self.motor.Z_c = self.motor_z_controller
#            self.piezo_z_controller.move_signal.disconnect(self.moved_z_controller)

        self.motor.coordinatesCorrected.emit(self.motor._corrections)


class Piezo_z(Stage_controller):
    """Singled out z direction to mix with the motor stage (see Motor_z_switcher)"""
    move_signal = QtCore.pyqtSignal(float)

    def __init__(self, piezo_controller):
        super().__init__()
        self.piezo = piezo_controller
        self.offset = 0
        piezo_controller.move_signal.connect(self.piezo_moved)

    def set_offset(self, offset):
        self.offset = offset

    def piezo_moved(self, Xm, V):
        self.move_signal.emit(self.offset + self.piezo.XmtoXs(Xm)[2])

    def get_position(self):
        return self.offset + self.piezo.XYZ_c.get_position()[2]

    def MOVVEL(self, Xs, V):
        piezo_pos = self.piezo.get_position(raw=True)
        piezo_pos[2] = Xs[0] - self.offset
        self.piezo.XYZ_c.MOVVEL(piezo_pos.copy(), [0, 0, V[0]])
        self.piezo.move_signal.emit(list(self.piezo.XstoXm(piezo_pos)), V)

    def get_pos_range(self, axis):
        return self.piezo.XYZ_c.get_pos_range(2) + self.offset

    def get_vel_range(self, axis):
        return self.piezo.XYZ_c.get_vel_range(2)

    def is_onTarget(self,):
        return self.piezo.XYZ_c.is_onTarget()

    def stop(self,):
        self.piezo.XYZ_c.stop()

    def ESTOP(self,):
        self.piezo.XYZ_c.ESTOP()

    def is_ready(self,):
        return self.piezo.XYZ_c.is_ready()