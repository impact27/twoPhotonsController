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
from PyQt5 import QtCore, QtWidgets
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
            X,Y,Y2=posdir['sizeCurve']
            self.parent.clearFig()
            self.parent.imageCanvas.plot(X[Y<4*np.min(Y)],Y[Y<4*np.min(Y)],'.')
            self.parent.imageCanvas._axes.twinx().plot(X,Y2,'x',c='C1')
            self.parent.imageCanvas.draw()
            
            
    def save_errors(self):
        fn=QtWidgets.QFileDialog.getSaveFileName(
            self.parent.imageCanvas,'TXT file',QtCore.QDir.homePath(),
            "Text (*.txt)")[0]
        ret = np.zeros((len(self.validated_positions)))
        for i,pos in enumerate(self.validated_positions):
            Xs = pos['X']
            z = pos['Z']
            z2 = self.parent.mouvment_delegate._getZOrigin(Xs)
            ret[i] = z-z2
        np.savetxt(fn, ret)
            
    

    

            
            
    
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