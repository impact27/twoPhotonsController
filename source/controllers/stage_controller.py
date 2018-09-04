# -*- coding: utf-8 -*-
"""
Created on Mon May  1 11:17:39 2017

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
from pipython import GCSDevice
import pipython
import time
import numpy as np
from PyQt5 import QtCore
import clr

from . import HW_conf
#import HW_conf

import sys
from System import Decimal
# constants
sys.path.append(r"C:\Program Files\Thorlabs\Kinesis")
# Add references so Python can see .Net
clr.AddReference("Thorlabs.MotionControl.Controls")
clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
clr.AddReference("Thorlabs.MotionControl.KCube.DCServoCLI")
import Thorlabs.MotionControl.Controls
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo

from .hardware_singleton import Hardware_Singleton

# ==============================================================================
# Stage controller
# ==============================================================================


class stage_controller(QtCore.QObject):

    def __init__(self):
        super().__init__()

    def reconnect(self):
        pass

    def get_position(self):
        pass

    def stop(self):
        pass

    def ESTOP(self):
        pass

    def is_onTarget(self):
        pass

    def get_pos_range(self, axis):
        pass

    def get_vel_range(self, axis):
        pass

    def MOVVEL(self, X, V):
        pass

    def is_ready(self):
        pass

# ==============================================================================
# Linear stages controller
# ==============================================================================
class HW_line(Hardware_Singleton):
    def __init__(self, name, ID):
        super().__init__(name)
        self._ID = ID

    def _open_connection(self):
        stage = GCSDevice(HW_conf.GCS_lin_controller_name)
        stage.ConnectUSB(self._ID)
        time.sleep(1)
        if stage.qCST()['1'] != HW_conf.GCS_lin_stage_name:
            print(stage.qCST()['1'])
            raise RuntimeError("Incorrect stage connected")
        print('Connected', stage.qIDN())
        stage.SVO(1, True)
        if not stage.qFRF()['1']:
            print("Reference move")
            stage.FRF(1)
        return stage

    def _close_connection(self):
        self.CloseConnection()

class Xline(HW_line):
    def __init__(self):
        super().__init__('X Line', HW_conf.XStageName)

class Yline(HW_line):
    def __init__(self):
        super().__init__('Y Line', HW_conf.YStageName)

class Linear_controller(stage_controller):
    def __init__(self):
        super().__init__()
        self.lines = [Xline(), Yline()]

    @property
    def connected(self):
        return np.all([l._isConnected for l in self.lines])

    def waitState(self, timeout=30):
        self.is_ready()
        startt = time.time()
        while not self.is_ready():
            time.sleep(.1)
            if time.time() - startt > timeout:
                raise RuntimeError("Linear Stage not responding")

    def MOVVEL(self, X, V):
        X, V = np.array([X, V]) / 1000
        for x, v, l in zip(X, V, self.lines):
            if v > 0:
                if v < 10e-6:
                    v = 10e-6
                l.VEL(1, v)
                l.MOV(1, x)

    def get_position(self):
        return np.asarray([l.qPOS()['1'] for l in self.lines],
                          dtype=float) * 1000

    def stop(self):
        for l in self.lines:
            try:
                l.HLT()
            except BaseException:
                pass

    def ESTOP(self):
        for l in self.lines:
            try:
                l.HLT()
            except BaseException:
                pass

    def is_onTarget(self):
        return np.all([l.qONT()['1'] for l in self.lines])

    def get_pos_range(self, axis):
        return np.array([0, 50.]) * 1000.

    def get_vel_range(self, axis):
        return np.array([0, 1.5]) * 1000.

    def is_ready(self):
        if np.any([l is None for l in self.lines]):
            return False
        return np.all([l.IsControllerReady() for l in self.lines])
# ==============================================================================
# Cube Controller
# ==============================================================================

class HW_E727(Hardware_Singleton):

    def __init__(self, callback=None):
        super().__init__('E727', callback)

    def _open_connection(self):
        stage = GCSDevice(HW_conf.GCS_cube_controller_name)
        stage.ConnectUSB(HW_conf.cubeName)
        time.sleep(2)
        print('Connected', stage.qIDN())
        if self.__cube.qCST()['1'] != HW_conf.GCS_cube_stage_name:
            print(self.__cube.qCST()['1'])
            raise RuntimeError("Incorrect stage connected")

        self.__cube.SVO([1, 2, 3], [True, True, True])
        self.__cube.ATZ([1, 2, 3], [0, 0, 0])
        return stage

    def _close_connection(self):
        self.CloseConnection()

class Cube_controller(stage_controller):
    # Reverse y and z
    stageConnected = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.__cube = HW_E727(self.stageConnected.emit)
        self.error = pipython.gcserror.GCSError
        self.internal_offset = np.asarray([50, 50, 50])
        self.Servo_Update_Time = 50e-6  # s 0x0E000200
        self.max_points = 250000  # 0x13000004

    def MOVVEL(self, X, V):
        X = X + self.internal_offset
        # Reverse y and z
        X[1:] = 100 - X[1:]
        self.__cube.VEL([1, 2, 3], list(np.abs(V)))
        self.__cube.MOV([1, 2, 3], list(X))

    def get_position(self):
        X = np.asarray(list(self.__cube.qPOS([1, 2, 3]).values()), dtype=float)
        # Reverse y and z
        X[1:] = 100 - X[1:]

        X -= self.internal_offset
        return X

    def stop(self):
        try:
            self.__cube.HLT()
        except BaseException:
            pass

    def ESTOP(self):
        try:
            self.__cube.HLT()
        except BaseException:
            pass

    def is_onTarget(self):
        return np.all(np.array(self.__cube.qONT([1, 2, 3]).values()))

    def get_pos_range(self, axis):
        return np.array([-50., 50.])

    def get_vel_range(self, axis):
        return np.array([0., 4000.])

    def is_ready(self):
        if not self.__cube.IsConnected():
            return False
        return self.__cube.IsControllerReady()

    def MAC_BEG(self, name):
        self.__cube.MAC_BEG(name)

    def MAC_END(self):
        self.__cube.MAC_END()

    def MAC_START(self, name):
        self.__cube.MAC_START(name)

    def MAC_DEL(self, name):
        self.__cube.MAC_DEL(name)

    def is_macro_running(self):
        return self.__cube.qRMC() != '\n'

    def macro_wait(self):
        self.__cube.send("WAC ONT? 1 = 1")
        self.__cube.send("WAC ONT? 2 = 1")
        self.__cube.send("WAC ONT? 3 = 1")

    def run_waveform(self, time_step, X):
        assert X.size < self.max_points
        assert np.shape(X)[1] == 3 or np.shape(X)[1] == 4

        rate = int(np.round(time_step / self.Servo_Update_Time))
        # Reverse y and z
        X[:, 1:3] = 100 - X[:, 1:3]

        # Set rate
        self.__cube.send(f"WTR 0 {rate} 1")

        # Send data
        for i in range(np.shape(X)[1]):
            self.__cube.send(f"WAV {i+1} X PNT 1 {X.shape[0]} " +
                             " ".join(str(e) for e in X[:, i]))

        idx = np.arange(np.shape(X)[1]) + 1

        # Connect to wave generator
        self.__cube.send("WSL " + " ".join(str(e) for e in np.repeat(idx, 2)))

        # limit to 1 scan
        self.__cube.send('WGC ' + " ".join(str(e) + ' 1' for e in idx))

        # GO
        self.__cube.send('WGO ' + " ".join(str(e) + ' 0x101' for e in idx))

        # wait
        time.sleep(50e-6 * rate * X.shape[0])
        while(self.__cube.IsGeneratorRunning()):
            time.sleep(0.1)

        # Clear tables
        self.__cube.send("WCL " + " ".join(str(e) for e in idx))


# =============================================================================
# Z Controller
# =============================================================================

class HW_zline(Hardware_Singleton):
    def __init__(self, callback):
        super().__init__('Z Line', callback)
        self._SN = HW_conf.kinesis_cube_serial

    def _open_connection(self):
        # Instructs the DeviceManager to build and maintain the list of
        # devices connected.
        DeviceManagerCLI.BuildDeviceList()

        kCubeDCServoMotor = KCubeDCServo.CreateKCubeDCServo(self._SN)

        # Establish a connection with the device.
        kCubeDCServoMotor.Connect(self._SN)

        # Wait for the device settings to initialize. We ask the device to
        # throw an exception if this takes more than 5000ms (5s) to complete.
        kCubeDCServoMotor.WaitForSettingsInitialized(5000)

        # Initialize the DeviceUnitConverter object required for real world
        # unit parameters.
        kCubeDCServoMotor.GetMotorConfiguration(self._SN)

        # This starts polling the device at intervals of 250ms (0.25s).
        kCubeDCServoMotor.StartPolling(20)

        # We are now able to enable the device for commands.
        kCubeDCServoMotor.EnableDevice()

        assert(kCubeDCServoMotor.IsActuatorDefined)

        print("Zstage Connected")

        velocity_parameters = kCubeDCServoMotor.GetVelocityParams()
        velocity_parameters.MaxVelocity = Decimal(1)
        kCubeDCServoMotor.SetVelocityParams(velocity_parameters)

        if not kCubeDCServoMotor.Status.IsHomed:
            kCubeDCServoMotor.Home(0)

        return kCubeDCServoMotor

    def _close_connection(self):
        self.ShutDown()

class z_controller(stage_controller):
    # Reverse z
    def __init__(self):
        super().__init__()
        self._kCubeDCServoMotor = HW_zline(self.onConnect)
        self.posmin = -12000
        self.posmax = 0

    def get_position(self):
        Z = float(str(self._kCubeDCServoMotor.Position)) * 1e3
        # Reverse z
        Z = - Z
        return Z

    def ESTOP(self):
        try:
            self.stop()
        except BaseException:
            pass

    def is_onTarget(self):
        return (abs(float(str(self._kCubeDCServoMotor.Position))
                    - float(str(self._kCubeDCServoMotor.TargetPosition)))
                < 1e-6) and not self._kCubeDCServoMotor.IsDeviceBusy

    def get_pos_range(self, axis):
        return [self.posmin, self.posmax]

    def get_vel_range(self, axis):
        return [
            0,
            1000 * self._kCubeDCServoMotor.AdvancedMotorLimits.VelocityMaximum]

    def MOVVEL(self, X, V):
        if V[0] < 1e-3:
            return
        elif V[0] < 2:
            V[0] = 2
            print("Speed too small")
        # Reverse z
        Z = - X[0]
        self.set_velocity(V[0])
        self._move_to(Z)

    def is_ready(self):
        return not self._kCubeDCServoMotor.IsDeviceBusy

    def set_velocity(self, V):
        V = V / 1000
        try:
            velocity_parameters = self._kCubeDCServoMotor.GetVelocityParams()
            velocity_parameters.MaxVelocity = Decimal(float(V))
            self._kCubeDCServoMotor.SetVelocityParams(velocity_parameters)
        except Thorlabs.MotionControl.DeviceManagerCLI.DeviceException as exc:
            print("Can't set velocity {}".format(V))

    def home(self):
        try:
            # We pass in a wait timeout of zero to indicates we don't care how
            # long it takes to perform the home operation.
            self._kCubeDCServoMotor.Home(0)

        except BaseException:
            print("Unable to return device to home position\n")
            raise

    def _move_to(self, pos, timeout=0):
        try:
            pos = pos / 1000
            # Move the device to position 0. We specify 0 as the wait timeout
            # as we don't care how long it takes.
            self._kCubeDCServoMotor.MoveTo(Decimal(float(pos)), timeout)
        except Thorlabs.MotionControl.DeviceManagerCLI.DeviceMovingException:
            print("Ignored, Already moving")
        except BaseException:
            print("Unable to move to position\n", sys.exc_info()[0])
            raise

    def stop(self):
        try:
            # We ask the device to throw an exception if the operation takes
            # longer than 1000ms (1s).
            self._kCubeDCServoMotor.Stop(1000)

#        except Thorlabs.MotionControl.GenericMotorCLI.MoveTimeoutException:
#            pass  # that is what stop does
        except BaseException:
            print("Unable to stop\n", sys.exc_info()[0])
            raise

    def is_homing(self):
        return self._kCubeDCServoMotor.Status.IsHoming

    def onConnect(self):
        self._posmin = float(str(self._kCubeDCServoMotor.AdvancedMotorLimits
                                 .LengthMinimum)) * 1e3
        self._posmax = float(str(self._kCubeDCServoMotor.AdvancedMotorLimits
                                 .LengthMaximum)) * 1e3

# ==============================================================================
# Helper functions
# ==============================================================================


def getPIListDevices():
    gcs = GCSDevice(HW_conf.GCS_lin_controller_name)
    return gcs.EnumerateUSB()


if __name__ == "__main__":
    print(getPIListDevices())
    # %%
    cc = Cube_controller()
    cc.connect()
    time.sleep(5)
    # %%
    cc.MAC_BEG('test')
