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
import time
import numpy as np
from PyQt5 import QtCore
from functools import partial
import clr
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

#==============================================================================
# Stage controller
#==============================================================================
class stage_controller():
    
    def __init__(self):
        pass
    
    def reconnect(self):
        pass
    
    def get_position(self):
        pass
    
    def ESTOP(self):
        pass
    
    def is_onTarget(self):
        pass
    
    def get_pos_range(self, axis):
        pass
    
    def get_vel_range(self, axis):
        pass
    
    def MOVVEL(self,X,V):
        pass
    
    def is_ready(self):
        pass

#==============================================================================
# Linear stages controller
#==============================================================================

XStageName='PI C-863 Mercury SN 0165500278'
YStageName='PI C-863 Mercury SN 0165500227'

class linear_controller(stage_controller):
    def __init__(self):
        super().__init__()
        self.lines = [None, None]
        self.threads = [linethread(sn, partial(self.set_stage, i)) 
                        for i, sn in enumerate([XStageName, YStageName])]
        self.reconnect()

    def set_stage(self, axis, stage):
        self.lines[axis] = stage
            
    @property
    def connected(self):
        return np.all([l is not None for l in self.lines])
    
    def reconnect(self):
        for i in range(2):
            if self.lines[i] is not None:
                self.lines[i].CloseConnection()
                self.lines[i] = None
        [t.start() for t in self.threads]
    
    def __del__(self):
        [l.CloseConnection() for l in self.lines]
        
    def waitState(self, timeout=30):
        startt = time.time()
        while not self.is_ready():
            time.sleep(.1)
            if time.time() - startt > timeout:
                raise RuntimeError("Linear Stage not responding")
                
    def MOVVEL(self,X,V):
        X, V = np.array([X, V])/1000
        for x, v, l in zip(X, V, self.lines):
            if v>0:
                l.VEL(1, v)
                l.MOV(1, x)
    
    def get_position(self):
        return np.asarray([l.qPOS()['1'] for l in self.lines],
                dtype=float)*1000
    
    def ESTOP(self):
        for l in self.lines:
            try:
               l.HLT()
            except:
                pass
    
    def is_onTarget(self):
        return np.all([l.qONT()['1'] for l in self.lines]) 

    def get_pos_range(self, axis):
        return np.array([0,50.])*1000
    
    def get_vel_range(self, axis):
        return np.array([0,1.5])*1000  
    
    def is_ready(self):
        if np.any([l is None for l in self.lines]):
            return False
        return np.all([l.IsControllerReady() for l in self.lines])
    
class linethread(QtCore.QThread):
    def __init__(self, StageName, callback):
        super().__init__()
        self.StageName = StageName
        self.callback = callback
        
    def run(self):
        stage = GCSDevice('C-863.11')
        stage.ConnectUSB(self.StageName)
        if stage.qCST()['1'] != 'M-404.2DG':
            print(stage.qCST()['1'])
            raise RuntimeError("Incorrect stage connected")
        print('Connected',stage.qIDN())
        stage.SVO(1,True)
        #time.sleep(1)
        if not stage.qFRF()['1']:
            print("Reference move")
            stage.FRF(1)
        self.callback(stage)
#==============================================================================
# Cube Controller
#==============================================================================
    
cubeName='PI E-727 Controller SN 0116021530'
class cube_controller(stage_controller):
    def __init__(self):
        super().__init__()
        self.cube = None
        self.thread = cubethread(cubeName, self.set_stage)
        self.reconnect()
        
    def set_stage(self, stage):
        self.cube = stage
        
    def reconnect(self):
        if self.cube is not None:
            self.cube.CloseConnection()
            del self.cube
            self.cube = None
        self.thread.start()
        
    def __del__(self):
        self.cube.CloseConnection()
                
    def MOVVEL(self,X,V):
        self.cube.VEL([1,2,3],list(np.abs(V)))
        self.cube.MOV([1,2,3],list(X))
    
    def get_position(self):
        return (np.asarray(list(self.cube.qPOS([1,2,3]).values()),dtype=float))
    
    def ESTOP(self):
        try:
            self.cube.HLT()
        except:
            pass
    
    def is_onTarget(self):
        return np.all(self.cube.qONT([1,2,3]).values())
    
    def get_pos_range(self, axis):
        return np.array([0, 100])
    
    def get_vel_range(self, axis):
        return np.array([0, 4000])
    
    def is_ready(self):
        if self.cube is None:
            return False
        return self.cube.IsControllerReady()
    
class cubethread(QtCore.QThread):
    def __init__(self, StageName, callback):
        super().__init__()
        self.StageName = StageName
        self.callback = callback
        
    def run(self):
        stage = GCSDevice('E-727')
        stage.ConnectUSB(self.StageName)
        if stage.qCST()['1'] != 'P-611.3S':
            print(stage.qCST()['1'])
            raise RuntimeError("Incorrect stage connected")
        print('Connected',stage.qIDN())
        stage.SVO([1,2,3],[True,True,True])
        stage.ATZ([1, 2, 3], [0, 0, 0])
        self.callback(stage)
 


kserial = '27502020'
class z_controller(stage_controller):
    def __init__(self, serial=kserial):
        super().__init__()
        self._kCubeDCServoMotor = None
        self.thread = Zthread(serial, self.set_stage)
        if serial is not None:
            self.connect(serial )
       
    def reconnect(self):
        if self._kCubeDCServoMotor is not None:
            self.disconnect()
        self.connect()
        
    def get_position(self):
        return float(str(self._kCubeDCServoMotor.Position))*1e3
    
    def ESTOP(self):
        self.stop()
    
    def is_onTarget(self):
        return (abs(float(str(self._kCubeDCServoMotor.Position)) 
                - float(str(self._kCubeDCServoMotor.TargetPosition)))
                < 1e-6) and not self._kCubeDCServoMotor.IsDeviceBusy
    
    def get_pos_range(self, axis):
        return [float(str(self._kCubeDCServoMotor.AdvancedMotorLimits
                                  .LengthMinimum))*1e3,
                float(str(self._kCubeDCServoMotor.AdvancedMotorLimits
                                  .LengthMaximum))*1e3]
    
    def get_vel_range(self, axis):
        return [
            0, 
            1000*self._kCubeDCServoMotor.AdvancedMotorLimits.VelocityMaximum]
    
    def MOVVEL(self,X,V):
        if V[0] > 0:
            self.set_velocity(V[0])
            self.move_to(X[0])
    
    def is_ready(self):
        return not self._kCubeDCServoMotor.IsDeviceBusy
    
    def set_velocity(self, V):
        V = V / 1000
        velocity_parameters = self._kCubeDCServoMotor.GetVelocityParams()
        velocity_parameters.MaxVelocity = Decimal(float(V))
        self._kCubeDCServoMotor.SetVelocityParams(velocity_parameters)

    def connect(self, serialNumber=kserial):
        
        if self._kCubeDCServoMotor is not None:
            print("Cube already connected")
            return
        
        self.thread.run()
    
    def disconnect(self):
        if self._kCubeDCServoMotor is None:
            print("Cube not connected")
            return
        try:
            # Shuts down this device and frees any resources it is using.
            self._kCubeDCServoMotor.ShutDown();

            self._kCubeDCServoMotor = None;
        except:
            print("Can't disconnect")
            raise
            
    def home(self):
        try:
            # We pass in a wait timeout of zero to indicates we don't care how
            # long it takes to perform the home operation.
            self._kCubeDCServoMotor.Home(0);
        
        except:
            print("Unable to return device to home position\n")
            raise
        
    def move_to(self, pos, timeout=0):
        try:
            pos = pos / 1000
            # Move the device to position 0. We specify 0 as the wait timeout
            # as we don't care how long it takes.
            self._kCubeDCServoMotor.MoveTo(Decimal(float(pos)), timeout);
        
        except:
            print("Unable to move to position\n")
            raise

    def stop(self):
        try:
            # We ask the device to throw an exception if the operation takes
            # longer than 1000ms (1s).
            self._kCubeDCServoMotor.Stop(1000);
        
        except:
            print("Unable to stop\n")
            raise
    def is_homing(self):
        return self._kCubeDCServoMotor.Status.IsHoming
    
    def set_stage(self, stage):
        self._kCubeDCServoMotor = stage 
  
class Zthread(QtCore.QThread):
    def __init__(self, SN, callback):
        super().__init__()
        self.SN = SN
        self.callback = callback
    
    def run(self):
        # Instructs the DeviceManager to build and maintain the list of
        # devices connected.
        DeviceManagerCLI.BuildDeviceList();

        kCubeDCServoMotor = KCubeDCServo.CreateKCubeDCServo(self.SN);

        # Establish a connection with the device.
        kCubeDCServoMotor.Connect(self.SN);

        # Wait for the device settings to initialize. We ask the device to
        # throw an exception if this takes more than 5000ms (5s) to complete.
        kCubeDCServoMotor.WaitForSettingsInitialized(5000);

        # Initialize the DeviceUnitConverter object required for real world
        # unit parameters.
        kCubeDCServoMotor.GetMotorConfiguration(self.SN);

        # This starts polling the device at intervals of 250ms (0.25s).
        kCubeDCServoMotor.StartPolling(20);

        # We are now able to enable the device for commands.
        kCubeDCServoMotor.EnableDevice();
        
        assert(kCubeDCServoMotor.IsActuatorDefined)
        
        print("Zstage Connected")
        
        velocity_parameters = kCubeDCServoMotor.GetVelocityParams()
        velocity_parameters.MaxVelocity = Decimal(1)
        kCubeDCServoMotor.SetVelocityParams(velocity_parameters)
        
        if not kCubeDCServoMotor.Status.IsHomed:
            kCubeDCServoMotor.Home(0)
    
        kCubeDCServoMotor.MoveTo(Decimal(6),0)
        self.callback(kCubeDCServoMotor)

#==============================================================================
# Helper functions
#==============================================================================
def getPIListDevices():
    gcs= GCSDevice('C-863.11')
    return gcs.EnumerateUSB()

if __name__ == "__main__":
    print(getPIListDevices())