# -*- coding: utf-8 -*-
"""
Created on Wed Apr 12 15:31:31 2017

@author: quentinpeter
"""
#import StageController
import numpy as np

##Get two corners
#controller=StageController.stageController()
#
#print(controller.getPos())


Nx=10
Ny=3
dx=100
dy=100
firstOrigin=[0,0]
mark1Pos=[0,0]
mark2Pos=[1000,300]
 
mark1RealPos=[20,30]
mark2RealPos=[1020,330]
 
 
 
offset=np.subtract(mark1RealPos,mark1Pos)
angle=(np.arctan2(*np.subtract(mark2Pos,mark1Pos))
         -np.arctan2(*np.subtract(mark2RealPos,mark1RealPos)))
 





for xOrigin in range(0,Nx*dx,dx):
    for yOrigin in range(0,Ny*dy,dy):
        ReadGFile()
        
from gcode import GController 

class DrawCController(GController, angle, origin):
    def __init__(self):
        super().__init__()
        self.rotMatrix = numpy.array([[np.cos(angle), -np.sin(angle)], 
                         [np.sin(angle),  np.cos(angle)]])
        self.origin=origin
        
        self.controller=None#StageController.stageController()
        
    def setIntensity(self,E):
        #TODO: get access to intensity 
        if E>0:
            pass
        else:
            pass
        
    def realCoord(X,Y):
        return np.add(np.dot(self.rotMatrix,[X,Y]),self.offset)
    
    def ZOrigin(X,Y):
        return 0

    def moveTo(self,X,Y,Z):
        
        RX,RY=realCoord(X,Y)
        RZ=Z+ZOrigin(X,Y)
        
        #Correct Z speed
        #move Z
        saveMove(RX,Ry)
        
    def setSpeed(self,F):
        self.controller.V=V
