# -*- coding: utf-8 -*-
"""
Created on Fri Oct  6 10:31:49 2017

@author: Local_Admin
"""

import clr
import sys
from System import Decimal
from time import sleep


# constants
sys.path.append(r"C:\Program Files\Thorlabs\Kinesis")

# add .net reference and import so python can see .net
clr.AddReference("Thorlabs.MotionControl.Controls")
import Thorlabs.MotionControl.Controls

# print(Thorlabs.MotionControl.Controls.__doc__)

# Add references so Python can see .Net
clr.AddReference("Thorlabs.MotionControl.DeviceManagerCLI")
clr.AddReference("Thorlabs.MotionControl.KCube.DCServoCLI")
from Thorlabs.MotionControl.DeviceManagerCLI import DeviceManagerCLI
from Thorlabs.MotionControl.KCube.DCServoCLI import KCubeDCServo

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
    
    def get_state(self):
        pass

kserial = '27502020'
class kCube():
    def __init__(self, serial=kserial):
        super().__init__()
        self._kCubeDCServoMotor = None
        if serial is not None:
            self.connect(serial )
       
    def reconnect(self):
        if self._kCubeDCServoMotor is not None:
            self.disconnect()
        self.connect()
        
    def get_position(self):
        return float(str(self._kCubeDCServoMotor.Position))
    
    def ESTOP(self):
        self.stop()
    
    def is_onTarget(self):
        return (abs(float(str(self._kCubeDCServoMotor.Position)) 
                - float(str(self._kCubeDCServoMotor.TargetPosition)))
                < 1e-6)
    
    def get_pos_range(self, axis):
#        cube._kCubeDCServoMotor.MotorPositionLimits.MinValue
#        cube._kCubeDCServoMotor.MotorPositionLimits.MaxValue
        return [float(str(self._kCubeDCServoMotor.AdvancedMotorLimits
                                  .LengthMinimum)),
                float(str(self._kCubeDCServoMotor.AdvancedMotorLimits
                                  .LengthMaximum))]
    
    def get_vel_range(self, axis):
        return [0, cube._kCubeDCServoMotor.AdvancedMotorLimits.VelocityMaximum]
    
    def MOVVEL(self,X,V):
        self.set_velocity(V)
        self.move_to(X)
    
    def get_state(self):
        return cube._kCubeDCServoMotor.IsDeviceBusy
    
    def set_velocity(self, V):
        velocity_parameters = self._kCubeDCServoMotor.GetVelocityParams()
        velocity_parameters.MaxVelocity = Decimal(V)
        self._kCubeDCServoMotor.SetVelocityParams(velocity_parameters)
#    
#    Initializing 
#    IsDeviceBusy

#    
    def connect(self, serialNumber=kserial):
        
        if self._kCubeDCServoMotor is not None:
            print("Cube already connected")
            return
        try:
            # Instructs the DeviceManager to build and maintain the list of
            # devices connected.
            DeviceManagerCLI.BuildDeviceList();
    
            self._kCubeDCServoMotor = KCubeDCServo.CreateKCubeDCServo(serialNumber);
    
            # Establish a connection with the device.
            self._kCubeDCServoMotor.Connect(serialNumber);
    
            # Wait for the device settings to initialize. We ask the device to
            # throw an exception if this takes more than 5000ms (5s) to complete.
            self._kCubeDCServoMotor.WaitForSettingsInitialized(5000);

            # Initialize the DeviceUnitConverter object required for real world
            # unit parameters.
            self._kCubeDCServoMotor.GetMotorConfiguration(serialNumber);

            # This starts polling the device at intervals of 250ms (0.25s).
            self._kCubeDCServoMotor.StartPolling(20);
    
            # We are now able to enable the device for commands.
            self._kCubeDCServoMotor.EnableDevice();
            
            assert(self._kCubeDCServoMotor.IsActuatorDefined)
        except:
            print("Can't connect")
            raise
    
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
            # Move the device to position 0. We specify 0 as the wait timeout
            # as we don't care how long it takes.
            self._kCubeDCServoMotor.MoveTo(Decimal(pos), timeout);
        
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

if __name__ == "__main__":
    
    cube = kCube()
    if not cube._kCubeDCServoMotor.Status.IsHomed:
        cube.home()
        sleep(1)
        while cube.is_homing():
            sleep(.1)
    #%%
    print(float(str(cube._kCubeDCServoMotor.TargetPosition)), cube.get_position())
    cube.move_to(0)
    sleep(.02)
    print(float(str(cube._kCubeDCServoMotor.TargetPosition)), cube.get_position())
    print(float(str(cube._kCubeDCServoMotor.TargetPosition)), cube.get_position())
    sleep(.1)
    print(float(str(cube._kCubeDCServoMotor.TargetPosition)), cube.get_position())
#    while not cube.is_onTarget():
#        print(cube._kCubeDCServoMotor.Status.IsMoving, cube.get_position())
    
    
