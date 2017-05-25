# -*- coding: utf-8 -*-
"""
Created on Mon May  1 17:09:31 2017

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

import numpy as np
from PyQt5 import QtCore
import copy

class tilt_delegate(QtCore.QObject):
    
    updatelist = QtCore.pyqtSignal(list)
    
    def __init__(self, parent):
        super().__init__()
        self.todo_positions=[]
        self.validated_positions=[]
        self.parent=parent
        
        self.thread=positions_thread()
        self.thread.finished.connect(self.threadFinished)
        
    
    def get_positions(self):
        return self.todo_positions, self.validated_positions
    
    def clear_positions(self):
        if  self.todo_positions==[]:
            self.validated_positions=[]
        else:
            self.todo_positions=[]
        self.update()
    
    def solve(self):
        """a*X + b*Y = Z
        """
        if len(self.validated_positions) == 1:
            pos = self.validated_positions[0]
            return np.array([0, 0, pos['Z']])
            
        if len(self.validated_positions)<3:
            self.parent.error.emit('Not enough validated positions')
            return np.zeros(3)*np.nan
        X=np.asarray([pos['X'][0] for pos in self.validated_positions])
        Y=np.asarray([pos['X'][1] for pos in self.validated_positions])
        Z=np.asarray([pos['Z'] for pos in self.validated_positions])
        
        M=np.asarray([[np.sum(X),   np.sum(Y),   len(X)],
                      [np.sum(X*X), np.sum(X*Y), np.sum(X)],
                      [np.sum(X*Y), np.sum(Y*Y), np.sum(Y)]])
        
        b=np.asarray([[np.sum(Z)],
                      [np.sum(X*Z)], 
                      [np.sum(Y*Z)]])
        
        coeffs=np.linalg.inv(M)@b
        return np.squeeze(coeffs)
    
    def validate_positions(self):
        #turn on laser
        ld=self.parent.laser_delegate
#        ld.set_intensity(ld.get_range()[-1])
        #Decrease cam exposure
        cd = self.parent.camera_delegate
        cd.set_shutter(cd.shutter_range()[0])
        #Start thread
        self.thread.setArgs(self.todo_positions,self.parent)
        self.todo_positions=[]
        self.thread.start()
        
    def threadFinished(self):
        if self.thread.error is not None:
            self.parent.error.emit(self.thread.error)
            
        self.validated_positions.extend(self.thread.positions_done)
        self.update()
        self.parent.correct_tilt()
        self.parent.newPosition.emit()
        
        
    def add_position(self, x,y):
        self.todo_positions.append([x, y])
        self.update()
        
    def load_file(self, fn):
        X=np.loadtxt(fn)
        for p in X:
            self.todo_positions.append(p)
        self.update()
            
    def update(self):
        total_list =  copy.deepcopy(self.validated_positions)
        #Display results as master coordinates
        for d in total_list:
            d['X']=self.parent.mouvment_delegate.XsToXm(d['X'])
        #Add todo
        for pos in self.todo_positions:
            total_list.append({
                    'X' : np.asarray(pos),
                    'Z' : np.nan,
                    'Image' : None})
        
        
        self.updatelist.emit(total_list)
        
    def deleteIdx(self, total_idx):
        lenvp=len(self.validated_positions)
        if total_idx<lenvp:
            del self.validated_positions[total_idx]
        else:
            del self.todo_positions[total_idx-lenvp]
        self.update()
            
    def display_row(self, idx):
        lenvp=len(self.validated_positions)
        if idx<lenvp:
            posdir = self.validated_positions[idx]
            im=posdir['Image']
            self.parent.imageCanvas.imshow(im)
            
    def plotCurveRow(self, idx):
        lenvp=len(self.validated_positions)
        if idx<lenvp:
            posdir = self.validated_positions[idx]
            X,Y=posdir['sizeCurve']
            self.parent.clearFig()
            self.parent.imageCanvas.plot(X,Y,'.')
            
    
    
class positions_thread(QtCore.QThread):
    def __init__(self):
        super().__init__()
        self.lastz=0
        self.error=None
        
    def setArgs(self, plist, parent):
        self.position_todo = plist
        self.parent = parent
        self.md=self.parent.mouvment_delegate
        self.get_image=self.parent.get_image
        im=self.get_image()
        self.imshape=np.shape(im)
        self.imdtype=im.dtype
        self.zrange=self.md.get_cube_PosRange(2)
        
        
    def goto_z(self,z):
        self.md.goto_cube_position([0,0,z], XsFrom=[0,0,self.lastz],
                                   rawPos=True, wait=True, checkid=self.lockid)
        self.lastz=z
    
    def get_image_range(self,zPos, condition=None):
        imrange=np.zeros((len(zPos),*self.imshape),
                         dtype=self.imdtype)
        if condition is None:
            def condition(a,b): return False
        for imr,z in zip(imrange,zPos):
            self.goto_z(z)
            im=self.get_image()
            imr[:]=im
            if condition(im,imrange):
                return imrange
        return imrange
        
    def new_z(self):
        def get_spot_sizes(imrange):
            return np.sum(imrange >= 
                          np.reshape(np.max(imrange,(1,2))/10,(-1,1,1)),
                          (1,2))
        
        def max_condition(im,ims):
            return np.max(im)<np.max(ims)-20
        
        #Coarse
        zPos=np.linspace(*self.zrange,21)
        imrange=self.get_image_range(zPos, max_condition)
        
        np.save('_coarse_z', zPos)
        np.save('_coarse_im', imrange)
        
        #Medium
        size = get_spot_sizes(imrange)
        argmin = np.argmin(size)
        if argmin == 0:
            argmin=1
        elif argmin == len(size)-1:
            argmin = len(size)-2
        zmin=zPos[argmin-1]
        zmax=zPos[argmin+1]
            
        zPos=np.linspace(zmin,zmax,21)
        imrange=self.get_image_range(zPos, max_condition)
        
        np.save('_medium_z', zPos)
        np.save('_medium_im', imrange)
        
#        #Fine
#        size = get_spot_sizes(imrange)
#        zlim=zPos[np.argsort(size)[:2]]
#        zPos=np.linspace(*zlim,51)
#        imrange=self.get_image_range(zPos)
#        
#        np.save('fine_z', zPos)
#        np.save('fine_im', imrange)
        
        # Get best
        size = get_spot_sizes(imrange)
        argmin=np.argmin(size)

        #save result and position
        return zPos[argmin], imrange[argmin], [zPos, size]
        
    def run(self):
        self.lockid=self.md.lock()
        
        if self.lockid is None:
            self.error = "Unable to lock the mouvment"
            return
        
        self.positions_done=[]
        Xslast= self.md.get_XY_position(rawCoordinates=True)
        for Xm in self.position_todo:
            #Go to position
            Xs=self.md.goto_XY_position(Xm, XsFrom=Xslast,
                                   wait=True,checkid=self.lockid)
            
            #Perform Z Scan
            zMax, im, sizeCurve = self.new_z()
            self.positions_done.append({
                    'X' : Xs,
                    'Z' : zMax,
                    'Image' : im,
                    'sizeCurve' : sizeCurve})
            Xslast=Xs
        self.md.unlock()

            
            
    
#if __name__ == "__main__":
#    X=np.random.rand(50)-.5
#    Y=np.random.rand(50)-.5
#    testcoeff=np.asarray([1e-3,4e-3, 10])
#    
#    Z=testcoeff[0]*X+testcoeff[1]*Y+testcoeff[2]
#    Z+=(np.random.rand(*np.shape(Z))-.5)*1e-3
#    
#    
#    def solve(X,Y,Z):
#        M=np.asarray([[np.sum(X),   np.sum(Y),   len(X)],
#                      [np.sum(X*X), np.sum(X*Y), np.sum(X)],
#                      [np.sum(X*Y), np.sum(Y*Y), np.sum(Y)]])
#        
#        b=np.asarray([[np.sum(Z)],
#                      [np.sum(X*Z)], 
#                      [np.sum(Y*Z)]])
#        
#        coeffs=np.linalg.inv(M)@b
#        return np.squeeze(coeffs)
#    
#    a,b,c=solve(X,Y,Z)
#    Zfit=a*X+b*Y+c
#    
#    #%%
#    import matplotlib.pyplot as plt
#    from mpl_toolkits.mplot3d import Axes3D
#    fig = plt.figure()
#    ax = fig.add_subplot(111, projection='3d')
#    
#    ax.plot(X,Y,Z,'-x')
#    ax.plot(X,Y,Zfit,'-x')
#    
#    print(testcoeff-[a,b,c])