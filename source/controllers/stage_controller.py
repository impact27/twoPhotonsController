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
import thorlabs_apt as apt
import time
import numpy as np
from PyQt5 import QtCore

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
    
    def get_state(self):
        pass

#==============================================================================
# Linear stages controller
#==============================================================================

XStageName='PI C-863 Mercury SN 0165500278'
YStageName='PI C-863 Mercury SN 0165500227'

class linear_controller(stage_controller):
    def __init__(self):
        super().__init__()
        self.lineX = None
        self.lineY = None
        self.Xthread = linethread(XStageName, lambda s: self.set_stage(s, 'X'))
        self.Ythread = linethread(YStageName, lambda s: self.set_stage(s, 'Y'))
        self.reconnect()

    def set_stage(self, stage, axis):
        if axis == 'X':
            self.lineX = stage
        if axis == 'Y':
            self.lineY = stage
            
    @property
    def connected(self):
        return (self.lineX is not None) and (self.lineY is not None)
    
    def reconnect(self):
        if self.lineX is not None:
            self.lineX.CloseConnection()
            del self.lineX
            self.lineX = None
            
        if self.lineY is not None:
            self.lineY.CloseConnection()
            del self.lineY
            self.lineY = None
            
        self.Xthread.start() 
        self.Ythread.start() 
    
    def __del__(self):
        self.lineX.CloseConnection()
        self.lineY.CloseConnection()
        
    def waitState(self, timeout=30):
        startt = time.time()
        while not self.get_state():
            time.sleep(.1)
            if time.time() - startt > timeout:
                raise RuntimeError("Linear Stage not responding")
                
    def MOVVEL(self,X,V):
        X, V = np.array([X, V])/1000
        self.lineX.VEL(1,np.abs(V[0]))
        self.lineY.VEL(1,np.abs(V[1]))
        self.lineX.MOV(1,X[0])
        self.lineY.MOV(1,X[1])
        
    
    def get_position(self):
        return np.asarray([self.lineX.qPOS()['1'],
                           self.lineY.qPOS()['1']],dtype=float)*1000
    
    def ESTOP(self):
        try:
            self.lineX.HLT()
        except:
            pass
        
        try:
            self.lineY.HLT()
        except:
            pass
                
    
    def is_onTarget(self):
        return self.lineX.qONT()['1'] and self.lineY.qONT()['1'] 

    def get_pos_range(self, axis):
        return np.array([0,50.])*1000
    
    def get_vel_range(self, axis):
        return np.array([0,1.5])*1000  
    
    def get_state(self):
        if self.lineX is None or self.lineY is None:
            return False
        return self.lineX.IsControllerReady() and self.lineY.IsControllerReady()
 
class linethread(QtCore.QThread):
    def __init__(self, StageName, callback):
        super().__init__()
        self.StageName = StageName
        self.callback = callback
        
    def run(self):
        stage = GCSDevice('C-863.11')
        stage.ConnectUSB(self.StageName)
        assert(stage.qCST()['1']=='M-404.2DG')
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
    
    def get_state(self):
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
        assert(stage.qCST()['1']=='P-611.3S')
        print('Connected',stage.qIDN())
        stage.SVO([1,2,3],[True,True,True])
        stage.ATZ([1, 2, 3], [0, 0, 0])
        self.callback(stage)
 
zmotorSN = 27502020
class z_controller(stage_controller):
    def __init__(self):
        super().__init__()
        self.motor = None
        self.thread = Zthread(zmotorSN, self.set_stage)
        self.reconnect()
    
    def set_stage(self, stage):
        self.motor = stage
        
    def reconnect(self):
        if self.motor is not None:
            del self.motor
            self.motor = None
        self.thread.run()   
    
    def get_position(self):
        return self.motor.position*1000
    
    def ESTOP(self):
        self.motor.stop_profiled()
    
    def is_onTarget(self):
        return not self.motor.is_in_motion
    
    def get_pos_range(self, axis):
        return np.array(self.motor.get_stage_axis_info()[:2])*1000
    
    def get_vel_range(self, axis):
        return np.asarray([0, self.motor.velocity_upper_limit()])*1000
    
    def MOVVEL(self, X, V):
        if V > 0:
            X, V = np.array([X, V])/1000
            self.motor.set_velocity_parameters(0, self.motor.acceleration, V)
            self.motor.move_to(X)
    
    def get_state(self):
        return self.motor is not None
  
class Zthread(QtCore.QThread):
    def __init__(self, SN, callback):
        super().__init__()
        self.SN = SN
        self.callback = callback
    
    def run(self):
        stage = apt.Motor(zmotorSN)
        print("Zstage Connected")
        stage.set_velocity_parameters(0, stage.acceleration, 1)
        if not stage.has_homing_been_completed:
            print("Reference move")
            stage.move_home(True)
        self.callback(stage)

#==============================================================================
# Helper functions
#==============================================================================
def getPIListDevices():
    gcs= GCSDevice('C-863.11')
    return gcs.EnumerateUSB()

def getAPTListDevices():
    return apt.list_available_devices()

if __name__ == "__main__":
    print(getPIListDevices())
    print(getAPTListDevices())