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
        self.reconnect()
        time.sleep(1)
        self.Ref()
        
    def reconnect(self):
        if self.lineX is not None:
            self.lineX.CloseConnection()
            del self.lineX
            
        if self.lineY is not None:
            self.lineY.CloseConnection()
            del self.lineY
            
        self.lineX = GCSDevice('C-863.11')
        self.lineY = GCSDevice('C-863.11')
        
        self.lineX.ConnectUSB(XStageName)
        assert(self.lineX.qCST()['1']=='M-404.2DG')
        print('Connected',self.lineX.qIDN())
        self.lineX.SVO(1,True)
        
        self.lineY.ConnectUSB(YStageName)
        assert(self.lineY.qCST()['1']=='M-404.2DG')
        print('Connected',self.lineY.qIDN())
        self.lineY.SVO(1,True)        

    def __del__(self):
        self.lineX.CloseConnection()
        self.lineY.CloseConnection()
    
    def Ref(self):
        if not self.lineX.qFRF(1):
            self.lineX.FRF(1)
        if not self.lineY.qFRF(1):
            self.lineY.FRF(1)
        
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
        return self.lineX.IsControllerReady() and self.lineY.IsControllerReady()
        
#==============================================================================
# Cube Controller
#==============================================================================
    
cubeName='PI E-727 Controller SN 0116021530'
class cube_controller(stage_controller):
    def __init__(self):
        super().__init__()
        self.cube = None
        self.reconnect()
        
    def autoZero(self):
        self.cube.ATZ([1, 2, 3], [0, 0, 0])
     
    def reconnect(self):
        if self.cube is not None:
            self.cube.CloseConnection()
            del self.cube
            
        self.cube = GCSDevice('E-727')
        self.cube.ConnectUSB(cubeName)
        assert(self.cube.qCST()['1']=='P-611.3S')
        print('Connected',self.cube.qIDN())
        self.cube.SVO([1,2,3],[True,True,True])
        
        self.autoZero()
        
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
        return self.cube.IsControllerReady()
 
zmotorSN = 27502020
class z_controller(stage_controller):
    def __init__(self):
        super().__init__()
        self.reconnect()
    
    def reconnect(self):
        self.motor = apt.Motor(zmotorSN)
<<<<<<< HEAD
        self.motor.set_velocity_parameters(0, self.motor.acceleration, 1)
        self.motor.move_home(True)
=======
        if not self.motor.has_homing_been_completed():
            self.motor.move_home(True)
>>>>>>> bd9cfef5fee9a4555645476cdf61d487ac42a333
    
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
        return True
    
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