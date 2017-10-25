# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
XStageName = 'PI C-863 Mercury SN 0165500278'
YStageName = 'PI C-863 Mercury SN 0165500227'
cubeName = 'PI E-727 Controller SN 0116021530'
from pipython import GCSDevice
import time
import numpy as np


def getListDevices():
    gcs = GCSDevice('C-863.11')
    return gcs.EnumerateUSB()


class stageController():
    def __init__(self):
        #devices = gcs.EnumerateUSB()
        self.lineX = GCSDevice('C-863.11')
        self.lineY = GCSDevice('C-863.11')

        self.lineX.ConnectUSB(XStageName)
        assert(self.lineX.qCST()['1'] == 'M-404.2DG')
        print('Connected', self.lineX.qIDN())

        self.lineY.ConnectUSB(YStageName)
        assert(self.lineY.qCST()['1'] == 'M-404.2DG')
        print('Connected', self.lineY.qIDN())

        self.V = 1

        self.Ref()

    def __del__(self):
        self.lineX.CloseConnection()
        self.lineY.CloseConnection()

    def Ref(self):
        self.lineX.SVO(1, True)
        self.lineX.FRF(1)
        self.lineY.SVO(1, True)
        self.lineY.FRF(1)
        while self.isMoving():
            time.sleep(.1)

    def isMoving(self):
        return self.lineX.IsMoving()['1'] and self.lineY.IsMoving()['1']

    def isOnTarget(self):
        return self.lineX.qONT()['1'] and self.lineY.qONT()['1']

    def ESTOP(self):
        self.lineX.StopAll()
        self.lineY.StopAll()

    def Move(self, X, Xfrom=None, waitTarget=False):
        # Get correct speed for each axis
        assert X[1] < 49, 'Collision!'
        if Xfrom is None:
            Xfrom = self.getPos()
        V = np.abs((X - Xfrom))
        V = V / np.linalg.norm(V) * self.V
        self.lineX.VEL(1, np.abs(V[0]))
        self.lineY.VEL(1, np.abs(V[1]))

        # Move to pos
        self.lineX.MOV(1, X[0])
        self.lineY.MOV(1, X[1])

        if waitTarget:
            while not self.isOnTarget():
                pass

    def getPos(self):
        return np.asarray([self.lineX.qPOS()['1'],
                           self.lineY.qPOS()['1']], dtype=float)


class cubeController():
    def __init__(self):
        self.cube = GCSDevice('E-727')
        self.cube.ConnectUSB(cubeName)
        assert(self.cube.qCST()['1'] == 'P-611.3S')
        print('Connected', self.cube.qIDN())
        self.cube.SVO([1, 2, 3], [True, True, True])

        self.V = 2000.

    def __del__(self):
        self.cube.CloseConnection()

    def ESTOP(self):
        self.cube.StopAll()

    def Move(self, X, Xfrom=None, waitTarget=False):
        if Xfrom is None:
            Xfrom = self.getPos()
        V = (X - Xfrom)
        V = V / np.linalg.norm(V) * self.V
        self.cube.VEL([1, 2, 3], list(np.abs(V)))
        self.cube.MOV([1, 2, 3], list(X))
        if waitTarget:
            while not self.isOnTarget():
                pass

    def getPos(self):
        return np.asarray(
            list(self.cube.qPOS([1, 2, 3]).values()), dtype=float)

    def isOnTarget(self):
        return np.all(self.cube.qONT([1, 2, 3]).values())


# class cubeController():
#    def __init__(self):
#
#        self.ex=np.array([1,0,0])
#        self.ey=np.array([0,1,0])
#        self.ez=np.array([0,0,1])
#        self.O=np.array([0,0,0])
#        self.V=2000.
#

#    def Move(self,X,Y,Z):
#        self.linTrueMOV(X*self.ex+Y*self.ey+Z*self.ez+self.O)

#
#    def changePlane(self, X):
#
#        #Init matrices
#        M=np.empty((3,3),dtype=float)
#        b=np.empty((3,) ,dtype=float)
#
#        #Fill matrices according to least square problem formulation
#        Vals=[X[:,0]**0,X[:,0],X[:,1]]
#        for i,xi in enumerate(Vals):
#            for j,xj in enumerate(Vals):
#                M[i,j]=xi@xj
#            b[i]=X[:,2]@xi
#
#        #Solve problem
#        C=np.linalg.solve(M, b)
#
#        #Get origin and basis vectors
#        self.O=np.array([0,0,C[0]])
#        A=np.array([1,0,C[1]])
#        B=np.array([0,1,C[2]])
#        Ex=np.array([1,0,0])
#        self.ez=np.cross(A,B)
#        self.ey=np.cross(self.ez,Ex)
#        self.ex=np.cross(self.ey,self.ez)
#        #Normalise
#        for e in [self.ex,self.ey,self.ez]:
#            e/=np.linalg.norm(e)


#%%
sc = stageController()
sc.Move([10, 10])
#%%
cc = cubeController()
cc.Move([50, 50, 50])

#%%
