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
import time
import numpy as np

#==============================================================================
# Stage controller
#==============================================================================
class stage_controller():
    
    def __init__(self, normV=1):
        self.normV=normV
        
    def reconnect(self):
        print("Connected stage")
        
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


class fake_controller(stage_controller):
    def __init__(self):
        super().__init__()
        
    def MOVVEL(self,X,V):
        self.position=self.get_position()
        self.V=V
        self.startTime=time.time()
        self.target=X
    
    def get_position(self):
        if self.is_onTarget():
            return self.target.copy()
        return self.position+self.V*(time.time()-self.startTime)
    
    def ESTOP(self):
        self.target=self.get_position()
        self.position=self.target
        
    def is_moving(self):
        return (time.time()-self.startTime
                < np.linalg.norm((self.target-self.position))/self.normV)
    
    def is_onTarget(self):
        return not self.is_moving()   
    
    def set_normV(self, normV):
        self.position=self.get_position()
        self.startTime=time.time()
        if np.linalg.norm(self.V)>0:
            self.V=self.V/np.linalg.norm(self.V)*self.normV
        self.normV=normV
        
#==============================================================================
# Linear stages controller
#==============================================================================


class linear_controller(fake_controller):
    def __init__(self):
        super().__init__()
        self.position=np.array([25,25])
        self.V=np.array([0,0])
        self.target=np.array([25,25])
        self.startTime=0
        
    def get_pos_range(self, axis): 
        return np.array([0,50])
    
    def get_vel_range(self, axis): 
        return np.array([0,1.5])
        
#==============================================================================
# Cube Controller
#==============================================================================
    
class cube_controller(fake_controller):
    def __init__(self):
        super().__init__()
        self.position=np.array([0,0,0])
        self.V=np.array([0,0,0])
        self.target=np.array([0,0,0])
        self.startTime=0         
    
    def get_pos_range(self, axis): 
        return np.array([0,100])
    
    def get_vel_range(self, axis): 
        return np.array([0,4000])
    
    