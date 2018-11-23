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
from pipython import GCSDevice, GCSError
import pipython
import time
import numpy as np
from PyQt5 import QtCore
import clr
import warnings

from errors import logError
from delegates.thread import lockmutex
import sys
from System import Decimal
# constants
sys.path.append(r"C:\Program Files\Thorlabs\Kinesis")
# Add references so Python can see .Net
clr.AddReference("Thorlabs.MotionControl.Controls")
clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
clr.AddReference("Thorlabs.MotionControl.KCube.DCServoCLI")
import Thorlabs.MotionControl.Controls
from Thorlabs.MotionControl.DeviceManagerCLI import (
        DeviceManagerCLI, 
        DeviceNotReadyException,
        MoveToInvalidPositionException,
        MoveTimeoutException)
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo

from errors import MotionError, HardwareError
if __name__ == "__main__":
    import HW_conf
    from hardware_singleton import Hardware_Singleton

else:
    from . import HW_conf
    from .hardware_singleton import Hardware_Singleton

VMAX = 10000

# ==============================================================================
# Stage controller
# ==============================================================================

class Stage_controller(QtCore.QObject):

    def __init__(self):
        super().__init__()

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

    def wait_end_motion(self, timeout=60):
        """Wait end of motion"""
        time.sleep(0.1)
        tstart = time.time()
        while self.is_moving():
            if timeout is not None and time.time() - tstart > timeout:
                raise MotionError('The motion took too long to complete')
            time.sleep(.01)

    def is_moving(self):
        raise NotImplementedError("is_moving not implemented")

# ==============================================================================
# Linear stages controller
# ==============================================================================


def try_connect(fconnect, Error, max_tests=20):
    connected = False
    Ntests = 0
    while not connected and Ntests < max_tests:
        try:
            fconnect()
            connected = True
        except Error:
            logError()
            time.sleep(1)
            Ntests += 1
            if Ntests == max_tests:
                raise


class HW_line(Hardware_Singleton):
    def __init__(self, name, ID):
        super().__init__(name)
        type(self)._ID = ID

    def _open_connection(self):
        stage = GCSDevice(HW_conf.GCS_lin_controller_name)

        try_connect(lambda: stage.ConnectUSB(type(self)._ID),
                    GCSError)

        time.sleep(1)
        if stage.qCST()['1'] != HW_conf.GCS_lin_stage_name:
            print(stage.qCST()['1'])
            raise HardwareError("Incorrect stage connected")
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


class HW_E727(Hardware_Singleton):

    def __init__(self, callback=None):
        super().__init__('E727', callback)

    def _open_connection(self):
        stage = GCSDevice(HW_conf.GCS_cube_controller_name)
        try_connect(lambda: stage.ConnectUSB(HW_conf.cubeName),
                    GCSError)
#        time.sleep(2)
        stage.WGO([1, 2, 3, 4], [0, 0, 0, 0])
        print('Connected', stage.qIDN())
        if stage.qCST()['1'] != HW_conf.GCS_cube_stage_name:
            print(stage.qCST()['1'])
            raise HardwareError("Incorrect stage connected")

        stage.SVO([1, 2, 3, 4], [True, True, True, False])
        if np.any(np.logical_not(list(stage.qATZ([1, 2, 3]).values()))):
            stage.ATZ([1, 2, 3], [0, 0, 0])
            while not stage.IsControllerReady() or np.any(list(
                    stage.IsMoving([1, 2, 3]).values())):
                time.sleep(0.1)
            stage.VEL([1, 2, 3], [500, 500, 500])
            stage.MOV([1, 2, 3], [50, 50, 50])
            time.sleep(0.1)
        while not stage.IsControllerReady() or np.any(list(
                stage.IsMoving([1, 2, 3]).values())):
            time.sleep(0.1)
        stage.IsRecordingMacro = False
        return stage

    def _close_connection(self):
        self.CloseConnection()


class HW_zline(Hardware_Singleton):
    def __init__(self, callback):
        super().__init__('Z Line', callback)

    def _open_connection(self):
        _SN = HW_conf.kinesis_cube_serial

        # Instructs the DeviceManager to build and maintain the list of
        # devices connected.
        DeviceManagerCLI.BuildDeviceList()

        kCubeDCServoMotor = KCubeDCServo.CreateKCubeDCServo(_SN)

        # Establish a connection with the device.
        try_connect(lambda: kCubeDCServoMotor.Connect(_SN),
                    DeviceNotReadyException)

        # Wait for the device settings to initialize. We ask the device to
        # throw an exception if this takes more than 5000ms (5s) to complete.
        kCubeDCServoMotor.WaitForSettingsInitialized(5000)

        # Initialize the DeviceUnitConverter object required for real world
        # unit parameters.
        kCubeDCServoMotor.GetMotorConfiguration(_SN)

        # This starts polling the device at intervals of 250ms (0.25s).
        kCubeDCServoMotor.StartPolling(20)

        # We are now able to enable the device for commands.
        kCubeDCServoMotor.EnableDevice()

        if not (kCubeDCServoMotor.IsActuatorDefined):
            raise HardwareError("Actuator not defined")

        print("Zstage Connected")

        velocity_parameters = kCubeDCServoMotor.GetVelocityParams()
        velocity_parameters.MaxVelocity = Decimal(1)
        kCubeDCServoMotor.SetVelocityParams(velocity_parameters)

        if not kCubeDCServoMotor.Status.IsHomed:
            kCubeDCServoMotor.Home(0)

        return kCubeDCServoMotor

    def _close_connection(self):
        self.ShutDown()


# =============================================================================
# Linear stage
# =============================================================================

class Linear_controller(Stage_controller):
    def __init__(self, callback):
        super().__init__()
        self.lines = [Xline(), Yline()]
        self._connect_callback = callback
        for l in self.lines:
            l.on_connect_signal.connect(self.on_connect)
        
    def on_connect(self):
        if self.isConnected:
            self._connect_callback()

    @property
    def isConnected(self):
        return np.all([l._isConnected for l in self.lines])

    def connect(self):
        for l in self.lines:
            l._connect()

    def disconnect(self):
        for l in self.lines:
            l._disconnect()

    def waitReady(self, timeout=30):
        startt = time.time()
        while not self.is_ready():
            time.sleep(.1)
            if time.time() - startt > timeout:
                raise HardwareError("Linear Stage not responding")

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
            except BaseException as e:
                print(e)

    def ESTOP(self):
        for l in self.lines:
            try:
                l.HLT()
            except BaseException as e:
                print(e)

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

    def is_moving(self):
        return np.any([l.IsMoving()['1'] for l in self.lines])
# ==============================================================================
# Cube Controller
# ==============================================================================


class Cube_controller(Stage_controller):
    # Reverse y and z
    stageConnected = QtCore.pyqtSignal()

    def no_macro(f):
        def ret(cls, *args, **kargs):
            if cls.isRecordingMacro:
                raise HardwareError(
                    "Can't use that function while recording a macro")
            else:
                return f(cls, *args, **kargs)
        return ret

    def __init__(self):
        super().__init__()
        self._mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        self.__cube = HW_E727(self.setup)
        self.error = pipython.gcserror.GCSError
        self.internal_offset = np.asarray([50, 50, 50])
        self.Servo_Update_Time = 50e-6  # s 0x0E000200
        self.max_points = 2**18  # 0x13000004
        self.clip_out_of_range = False

    def setup(self):
        self.stageConnected.emit()
        self.setup_measure()
        
    @property
    def isRecordingMacro(self):
        return self.__cube.IsRecordingMacro

    def disconnect(self):
        self.__cube._disconnect()

    def connect(self):
        self.__cube._connect()

    def isConnected(self):
        return self.__cube._isConnected()

    def controller(self):
        return self.__cube

    @lockmutex
    def MOVVEL(self, X, V):
        X = X + self.internal_offset
        # Reverse y and z
        X[1:] = 100 - X[1:]

        if not (np.all(X >= 0) and np.all(X <= 100)):
            if self.clip_out_of_range:
                clip_neg = X[X<0]
                clip_pos = X[X>100] - 100
                X[X<0] = 0
                X[X>100] = 100
                warnings.warn(RuntimeWarning(f"Clipping {clip_neg} {clip_pos}"))
            else:
                raise MotionError(f"Target Position is out of range! {X}")

        V = np.abs(V)
        V[V < 1e-3] = 1e-3
        self.__cube.VEL([1, 2, 3], list(V))
        self.__cube.MOV([1, 2, 3], list(X))

    @lockmutex
    @no_macro
    def get_position(self):
        X = np.asarray(list(self.__cube.qPOS([1, 2, 3]).values()), dtype=float)
        # Reverse y and z
        X[1:] = 100 - X[1:]

        X -= self.internal_offset
        return X

    @lockmutex
    @no_macro
    def stop(self):
        try:
            self.__cube.HLT()
        except BaseException as e:
                print(e)
    def ESTOP(self):
        try:
            self.__cube.HLT()
        except BaseException as e:
                print(e)

    @lockmutex
    @no_macro
    def is_onTarget(self):
        return np.all(list(self.__cube.qONT([1, 2, 3]).values()))

    def get_pos_range(self, axis):
        return np.array([-50., 50.])

    def get_vel_range(self, axis):
        return np.array([0., 4000.])

    @lockmutex
    @no_macro
    def is_ready(self):
        if not self.__cube.IsConnected():
            return False
        return self.__cube.IsControllerReady()

    @lockmutex
    @no_macro
    def is_moving(self):
        return np.any(list(self.__cube.IsMoving().values()))

    @lockmutex
    def MAC_BEG(self, name):
        self.__cube.IsRecordingMacro = True
        self.__cube.errcheck = False
        self.__cube.MAC_BEG(name)
        self.__cube.send('ERR?')

    @lockmutex
    def MAC_END(self):
        self.__cube.IsRecordingMacro = False
        self.__cube.errcheck = True
        self.__cube.MAC_END()

    @lockmutex
    def MAC_START(self, name):
        self.__cube.MAC_START(name)
        time.sleep(1)

    @lockmutex
    def MAC_DEL(self, name):
        self.__cube.MAC_DEL(name)

    @lockmutex
    def macro_exists(self, name):
        rep = self.__cube.qMAC()
        return name.lower() in [s.strip().lower() for s in rep.split('\n')]

    @lockmutex
    @no_macro
    def is_macro_running(self):
        return self.__cube.qRMC() != '\n'

    @lockmutex
    def macro_wait(self):
        self.__cube.send("WAC ONT? 1 = 1")
        self.__cube.send("WAC ONT? 2 = 1")
        self.__cube.send("WAC ONT? 3 = 1")
        
    def waveToController(self, X):
        X[..., :3] = X[..., :3] + self.internal_offset
        # Reverse y and z
        X[:, 1:3] = 100 - X[:, 1:3]
        return X
    
    def waveFromController(self, X):
        X = np.asarray(X)
        # Reverse y and z
        X[:, 1:3] = 100 - X[:, 1:3]
        
        X[..., :3] = X[..., :3] - self.internal_offset
        
        return X

    @lockmutex
    @no_macro
    def run_waveform(self, time_step, X, measure_time_step=None):
        
        if X.size >= self.max_points:
            raise MotionError(
                    "The wavepoints has more points than the controller can handle")
        if not (np.shape(X)[1] == 3 or np.shape(X)[1] == 4):
            raise MotionError("Waveform shape is incorrect! {np.shape(X)}")
        
        if measure_time_step is not None:
            self.setup_measure_rate(measure_time_step)
        # Go to first pos
        self.MOVVEL(X[0, :3], np.ones(3) * 1000)

        rate = int(np.round(time_step / self.Servo_Update_Time))

        X = self.waveToController(X)

        if not (np.all(X[..., :3] > 0) and np.all(X[..., :3] < 100)):
            if not self.clip_out_of_range:
                raise MotionError("Some points in the waveform are out of bounds.")

        # Set rate
        old_rate = self.__cube.qWTR()
        if old_rate[0] != [rate, 1]:
            print('Change rate', old_rate[0])
            self.__cube.send(f"WTR 0 {rate} 1")

        idx = np.arange(np.shape(X)[1]) + 1

        # Clear tables
        self.__cube.send("WCL " + " ".join(str(e) for e in idx))

        # Send data
        slice_size = 50
        for i in range(np.shape(X)[1]):
            append = 'X'
            for point_idx in np.arange(0, np.shape(X)[0], slice_size):
                data = X[point_idx:point_idx + slice_size, i]
                cmd = (f"WAV {i+1} {append} PNT 1 {len(data)} " +
                       " ".join(f'{e:.3f}' for e in data))
                self.__cube.send(cmd)
                append = '&'

        # Connect to wave generator
        self.__cube.send("WSL " + " ".join(str(e) for e in np.repeat(idx, 2)))

        # limit to 1 scan
        self.__cube.send('WGC ' + " ".join(str(e) + ' 1' for e in idx))

        # Offset to 0
        self.__cube.send('WOS ' + " ".join(str(e) + ' 0' for e in idx))

        # Maximum speed to a lot
        self.__cube.VEL([1, 2, 3], [VMAX, VMAX, VMAX])
        
        # GO
        self.__cube.send('WGO ' + " ".join(str(e) + ' 0x101' for e in idx))

        return self.Servo_Update_Time * rate * X.shape[0]

    @lockmutex
    @no_macro
    def setup_measure_rate(self, time_step):
        # Set rate
        rate = int(np.round(time_step / self.Servo_Update_Time))
        self.__cube.RTR(rate)
    
    @property
    def measure_table(self):
        target = 1
        position = 2
        voltage = 16
        return {
                1: {'axis': 1, 'option': target},
                2: {'axis': 2, 'option': target},
                3: {'axis': 3, 'option': target},
                4: {'axis': 1, 'option': position},
                5: {'axis': 2, 'option': position},
                6: {'axis': 3, 'option': position},
                7: {'axis': 4, 'option': voltage}
                }
    @lockmutex
    @no_macro
    def setup_measure(self):

        RTable = self.measure_table

        for Rkey in RTable.keys():
            self.__cube.DRC(Rkey, RTable[Rkey]['axis'], RTable[Rkey]['option'])

    @no_macro
    def wait_end_wave(self, wait_time):
        # wait
        time.sleep(wait_time)
        while(self.__cube.IsGeneratorRunning()[1]):
            time.sleep(0.1)

    @lockmutex
    @no_macro
    def get_measure(self, offset, numvalues):
        if numvalues > 2**15:
            raise RuntimeError(f"Too many values to read! {numvalues}")
        header = self.__cube.qDRR(offset=offset+1, numvalues=numvalues,
                                  tables=list(np.arange(7)+1))
        while self.__cube.bufstate is not True:
            time.sleep(0.1)
        data = self.__cube.bufdata
        
        # Check header is OK
        expected = {
            'NDATA': numvalues,
            'NAME0': 'Target Position of axis1',
            'NAME1': 'Target Position of axis2',
            'NAME2': 'Target Position of axis3',
            'NAME3': 'Current Position of axis1',
            'NAME4': 'Current Position of axis2',
            'NAME5': 'Current Position of axis3',
            'NAME6': 'Voltage of output chan4'
            }
        for key in expected.keys():
            if expected[key] != header[key]:
                raise RuntimeError(f"Header incorrect! {key}: "
                                   f"{expected[key]} != {header[key]}")
        measure = {
                'dt': header['SAMPLE_TIME'],
                'Target': self.waveFromController(np.transpose(data[:3])),
                'Current': self.waveFromController(np.transpose(data[3:6])),
                'Power': np.asarray(data[6])}
        return measure


# =============================================================================
# Z Controller
# =============================================================================


class z_controller(Stage_controller):
    # Reverse z
    def __init__(self):
        super().__init__()
        self._kCubeDCServoMotor = HW_zline(self.onConnect)
        self.posmin = -12000
        self.posmax = 0

    def connect(self):
        self._kCubeDCServoMotor._connect()

    def disconnect(self):
        self._kCubeDCServoMotor._disconnect()

    def isConnected(self):
        return self._kCubeDCServoMotor._isConnected()

    def get_position(self):
        Z = float(str(self._kCubeDCServoMotor.Position)) * 1e3
        # Reverse z
        Z = - Z
        return Z

    def ESTOP(self):
        try:
            self.stop()
        except BaseException as e:
                print(e)

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
        elif V[0] < 5:
            V[0] = 5
            print("Speed too small")
        # Reverse z
        Z = - X[0]
        self.set_velocity(V[0])
        try:
            self._move_to(Z)
        except MoveToInvalidPositionException:
            logError()
            raise MotionError(f"{Z} is out of range!")
        except MoveTimeoutException:
            logError()
            raise MotionError(f"The motion was too slow with speed {V}")

    def is_ready(self):
        return not self._kCubeDCServoMotor.IsDeviceBusy

    def set_velocity(self, V):
        V = V / 1000
        try:
            velocity_parameters = self._kCubeDCServoMotor.GetVelocityParams()
            velocity_parameters.MaxVelocity = Decimal(float(V))
            self._kCubeDCServoMotor.SetVelocityParams(velocity_parameters)
        except Thorlabs.MotionControl.DeviceManagerCLI.DeviceException as exc:
            logError()
            print("Can't set velocity {}".format(V))

    def home(self):
        try:
            # We pass in a wait timeout of zero to indicates we don't care how
            # long it takes to perform the home operation.
            self._kCubeDCServoMotor.Home(0)

        except BaseException as e:
            print(e)
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
        except BaseException as e:
            print("Unable to move to position\n", e)
            raise

    def stop(self):
        try:
            # We ask the device to throw an exception if the operation takes
            # longer than 1000ms (1s).
            self._kCubeDCServoMotor.Stop(1000)

#        except Thorlabs.MotionControl.GenericMotorCLI.MoveTimeoutException:
#            pass  # that is what stop does
        except BaseException as e:
            print("Unable to stop\n", e)
            raise

    def is_homing(self):
        return self._kCubeDCServoMotor.Status.IsHoming

    def onConnect(self):
        self._posmin = float(str(self._kCubeDCServoMotor.AdvancedMotorLimits
                                 .LengthMinimum)) * 1e3
        self._posmax = float(str(self._kCubeDCServoMotor.AdvancedMotorLimits
                                 .LengthMaximum)) * 1e3

    def is_moving(self):
        return self._kCubeDCServoMotor.Status.IsMoving


# ==============================================================================
# Helper functions
# ==============================================================================


def getPIListDevices():
    gcs = GCSDevice(HW_conf.GCS_lin_controller_name)
    return gcs.EnumerateUSB()


if __name__ == "__main__":
    pass
#    print(getPIListDevices())
    # %%
    cc = z_controller()
#    print(cc.is_ready())
