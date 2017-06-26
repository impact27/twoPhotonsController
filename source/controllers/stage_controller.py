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

#==============================================================================
# Stage controller
#==============================================================================
class stage_controller():
    
    def __init__(self, normV=1):
        self.normV=normV
        
    def reconnect(self):
        pass
        
    def set_normV(self, normV):
        self.normV=normV
        
    def get_normV(self):
        return self.normV
        
    def goto_position(self, X, Xfrom=None, wait=False):
        X=np.asarray(X)
        if Xfrom is None:
            Xfrom=self.get_position()    
        else:
            Xfrom=np.asarray(Xfrom)
            
        if np.all(X == Xfrom):
            return
        #Get correct speed for each axis   
        Xdist=(X-Xfrom)
        Xtime=np.linalg.norm(Xdist)/self.normV
        V=Xdist/Xtime
        self.MOVVEL(X,V)
        if wait:
            time.sleep(Xtime)
            while not self.is_onTarget():
                time.sleep(.01)
    
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
        self.lineX.FRF(1)
        self.lineY.FRF(1)
        while not self.get_state():
            time.sleep(.1)
                
    def MOVVEL(self,X,V):
        self.lineX.VEL(1,np.abs(V[0]))
        self.lineY.VEL(1,np.abs(V[1]))
        self.lineX.MOV(1,X[0])
        self.lineY.MOV(1,X[1])
        
    
    def get_position(self):
        return np.asarray([self.lineX.qPOS()['1'],
                           self.lineY.qPOS()['1']],dtype=float)
    
    def ESTOP(self):
        try:
            self.lineX.StopAll()
        except:
            pass
        
        try:
            self.lineY.StopAll()
        except:
            pass
                
    
    def is_onTarget(self):
        return self.lineX.qONT()['1'] and self.lineY.qONT()['1'] 

    def get_pos_range(self, axis):
        return np.array([0,50.])
    
    def get_vel_range(self, axis):
        return np.array([0,1.5])      
    
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
        self.center = np.array([50, 50, 25])
        
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
        self.cube.MOV([1,2,3],list(X+self.center))
    
    def get_position(self):
        return (np.asarray(list(self.cube.qPOS([1,2,3]).values()),dtype=float)
                -self.center)
    
    def ESTOP(self):
        try:
            self.cube.StopAll()
        except:
            pass
    
    def is_onTarget(self):
        return np.all(self.cube.qONT([1,2,3]).values())
    
    def get_pos_range(self, axis):
        if axis<2:
            return np.array([-50, 50])
        else:
            return np.array([-25, 75])
    
    def get_vel_range(self, axis):
        return np.array([0, 4000])
    
    def get_state(self):
        return self.cube.IsControllerReady()
    
#==============================================================================
# Helper functions
#==============================================================================
def getListDevices():
    gcs= GCSDevice('C-863.11')
    return gcs.EnumerateUSB()

if __name__ == "__main__":
    print(getListDevices())