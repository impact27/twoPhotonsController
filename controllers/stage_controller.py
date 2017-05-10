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
        V=(X-Xfrom)
        V=V/np.linalg.norm(V)*self.normV
        
        self.MOVVEL(X,V)
        
        if wait:
            waittime=np.linalg.norm(X-Xfrom)/self.normV
            time.sleep(waittime)
            while not self.is_onTarget():
                time.sleep(.01)
    
    def get_position(self):
        pass
    
    def ESTOP(self):
        pass
    
    def is_moving(self):
        pass
    
    def is_onTarget(self):
        pass
    
    def get_pos_range(self, axis):
        pass
    
    def get_vel_range(self, axis):
        pass
    
    def MOVVEL(self,X,V):
        pass


#==============================================================================
# Linear stages controller
#==============================================================================

XStageName='PI C-863 Mercury SN 0165500278'
YStageName='PI C-863 Mercury SN 0165500227'

class linear_controller(stage_controller):
    def __init__(self):
        super().__init__()
        #devices = gcs.EnumerateUSB()
        self.lineX = GCSDevice('C-863.11')
        self.lineY = GCSDevice('C-863.11')
        
        self.lineX.ConnectUSB(XStageName)
        assert(self.lineX.qCST()['1']=='M-404.2DG')
        print('Connected',self.lineX.qIDN())
        
        self.lineY.ConnectUSB(YStageName)
        assert(self.lineY.qCST()['1']=='M-404.2DG')
        print('Connected',self.lineY.qIDN())
        
        self.Ref()

    def __del__(self):
        self.lineX.CloseConnection()
        self.lineY.CloseConnection()
    
    def Ref(self):
        self.lineX.SVO(1,True)
        self.lineX.FRF(1)
        self.lineY.SVO(1,True)
        self.lineY.FRF(1)
        while self.isMoving():
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
        self.lineX.StopAll()
        self.lineY.StopAll()
        
    def is_moving(self):
        return self.lineX.IsMoving()['1'] and self.lineY.IsMoving()['1']
    
    def is_onTarget(self):
        return self.lineX.qONT()['1'] and self.lineY.qONT()['1']        
        
#==============================================================================
# Cube Controller
#==============================================================================
    
cubeName='PI E-727 Controller SN 0116021530'
class cube_controller(stage_controller):
    def __init__(self):
        super().__init__()
        self.cube = GCSDevice('E-727')
        self.cube.ConnectUSB(cubeName)
        assert(self.cube.qCST()['1']=='P-611.3S')
        print('Connected',self.cube.qIDN())
        self.cube.SVO([1,2,3],[True,True,True])
        
    def __del__(self):
        self.cube.CloseConnection()
                
    def MOVVEL(self,X,V):
        self.cube.VEL([1,2,3],list(np.abs(V)))
        self.cube.MOV([1,2,3],list(X))
    
    def get_position(self):
        return np.asarray(list(self.cube.qPOS([1,2,3]).values()),dtype=float)
    
    def ESTOP(self):
        self.cube.StopAll()
        
    def is_moving(self):
        return np.any(self.cube.IsMoving([1,2,3]).values())
    
    def is_onTarget(self):
        return np.all(self.cube.qONT([1,2,3]).values())
    
    
#==============================================================================
# Helper functions
#==============================================================================
def getListDevices():
    gcs= GCSDevice('C-863.11')
    return gcs.EnumerateUSB()