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
from scipy.ndimage.morphology import binary_dilation as dilate

class tilt_delegate(QtCore.QObject):
    
    updatelist = QtCore.pyqtSignal(list)
    
    def __init__(self, parent):
        super().__init__()
        self.todo_positions=[]
        self.validated_positions=[]
        self.parent=parent
        
        self.zrange=[0,100]        
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
        print('Validating')
        self.thread.setArgs(self.todo_positions,self.parent)
        self.todo_positions=[]
        self.thread.start()
        
    def threadFinished(self):
        if self.thread.error is not None:
            self.parent.error.emit(self.thread.error)
            
        self.validated_positions.extend(self.thread.positions_done)
        self.update()
        self.parent.correct_tilt()
        
    def add_position(self, x,y):
        self.todo_positions.append([x, y])
        self.update()
        
    def load_file(self, fn):
        X=np.loadtxt(fn)
        for p in X:
            self.todo_positions.append(p)
        self.update()
            
    def update(self):
        total_list =  self.validated_positions.copy()
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
            self.parent.imageCanvas.setimage(im)
            
    
    
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
        self.imshape=np.shape(self.get_image())
        self.zrange=self.md.get_cube_PosRange(2)
        
        
    def goto_z(self,z):
        print('Going to Z', z)
        self.md.goto_cube_position([0,0,z], XsFrom=[0,0,self.lastz],
                                   rawPos=True, wait=True, checkid=self.lockid)
        self.lastz=z
    
    def get_image_range(self,zPos):
        imrange=np.zeros((len(zPos),*self.imshape))
        for imr,z in zip(imrange,zPos):
            self.goto_z(z)
            imr[:]=self.get_image()
            if np.max(imr)<.9*np.max(imrange):
                return imrange
        return imrange
        
    def new_z(self):
        #get 10 images
        zPos=np.linspace(*self.zrange,10)
        imrange=self.get_image_range(zPos)
        
        #Get best positions
        size = np.sum(imrange>(np.min(imrange,(1,2))+np.max(imrange,(1,2)))/4)
        argmin = np.argmin(size)
        zPos=np.linspace(zPos[argmin-1],zPos[argmin+1],20)
        imrange=self.get_image_range(zPos)
        
        #Get best position
        Y=np.sum(imrange>(np.min(imrange,(1,2))+np.max(imrange,(1,2)))/4)
        X=zPos
        coeff_parabola=np.polyfit(X,Y,2)
        zMax=-coeff_parabola[1]/(coeff_parabola[0]*2)
        for im,z in zip(imrange, zPos):
            np.save('XY:{} Z:{}'.format(
                    self.md.get_XY_position(rawCoordinates=True),z),im)
        #Go to this position and save
        self.goto_z(zMax)
        return zMax
        
    def run(self):
        try:
            print('Running thread')
            self.lockid=self.md.lock()
            
            if self.lockid is None:
                self.error = "Unable to lock the mouvment"
                return
            
            self.positions_done=[]
            Xslast= self.md.get_XY_position(rawCoordinates=True)
            for Xm in self.position_todo:
                print('Going to position', Xm)
                #Go to position
                Xs=self.md.goto_XY_position(Xm, XsFrom=Xslast,
                                       wait=True,checkid=self.lockid)
                #Perform Z Scan
                zMax=self.new_z()
                im=self.get_image()
                self.positions_done.append({
                        'X' : Xs,
                        'Z' : zMax,
                        'Image' : im})
                Xslast=Xs
            self.md.unlock()
        except:
            import sys
            print(sys.exc_info())
            
            
    
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