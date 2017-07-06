"""
Created on Mon May  1 10:11:30 2017

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


class orientation_delegate(QtCore.QObject):
    
    updatelist = QtCore.pyqtSignal(list)
    
    def __init__(self,application_delegate):
        super().__init__()
        self.positions=[]
        self.parent=application_delegate
        self.md=application_delegate.mouvment_delegate
    
    def newXYpos(self,x,y):
        if not self.md.is_onTarget():
            self.parent.error.emit('Stage is Moving!')
            return
        #TODO: Check what happens if piezzo not centered 
        Xstage=self.md.motor.get_position(raw=True)[:2]
        Xmaster=[x,y]
        image=self.parent.get_image(rm_bg=True)
        self.new_position(Xstage,Xmaster, image)
        
    def displayrow(self,row):
        im=self.get_positions()[row]['Image']
        self.parent.imageCanvas.imshow(im)
        
    def new_position(self,Xstage, Xmaster, image):
        Xstage=np.asarray(Xstage)
        Xmaster=np.asarray(Xmaster)
        image=np.asarray(image)
        self.positions.append(
                {'Xstage' : Xstage,
                 'Xmaster' : Xmaster,
                 'Image' : image})
        self.updatelist.emit(self.positions)
    
    def get_positions(self):
        return self.positions
    
    def clear_positions(self):
        self.positions=[]
        self.updatelist.emit(self.positions)
        
    def del_position(self,idx):
        del self.positions[idx]
        self.updatelist.emit(self.positions)
        
    def save_errors(self):
        fn=QtWidgets.QFileDialog.getSaveFileName(
            self.parent.imageCanvas,'TXT file',QtCore.QDir.homePath(),
            "Text (*.txt)")[0]
        ret = np.zeros((len(self.positions),2))
        for i,pos in enumerate(self.positions):
            Xm1 = pos['Xmaster']
            Xm2 = self.md.motor.XstoXm([*pos['Xstage'],0])[:2]
            ret[i] = (Xm1-Xm2)
        np.savetxt(fn, ret)
        
    
    
    
        
    
#    
#    
#import numpy as np
#import matplotlib.pyplot as plt
#
#def getBSData(theta, offset):
#
#    Xm=np.random.rand(5,2)-.5
#    
#    c,s=np.cos(theta),np.sin(theta)
#    
#    RReal=np.array([[c,-s],[s,c]])
#    
#    Xs=np.array(Xm)
#    
#    Xs=np.array([RReal@X+offset for X in Xm])
#    
#    Xs+=(np.random.rand(*np.shape(Xs))-.5)*.01
#    
#    return Xm, Xs
#
#    
#
#
##%%
#def solve(Xstage,Xmaster):
#    """ solve the rotation and translation of Xstage and Xmaster
#    
#    
#    with the least square method
#    """
#    def getResidus(theta):
#        c,s=np.cos(theta),np.sin(theta)
#        R=np.array([[c,-s],[s,c]])
#        RXm=np.array([R@X for X in Xmaster])
#        origin=1/len(Xstage)*np.sum(Xstage-RXm,axis=0)
#        residus=np.sum((RXm+origin-Xstage)**2)
#        return origin, residus
#
#    #Get best theta
#    Xs2=1/len(Xstage)*np.sum(Xstage,0)-Xstage
#    theta1=np.arctan(np.sum(Xs2*Xmaster)/np.sum(np.cross(Xs2,Xmaster)))-np.pi/2
#    
#    #Theta is defined +-pi. Must test theta+pi
#    origin1, residus1= getResidus(theta1)
#    theta2=theta1+np.pi
#    origin2, residus2 = getResidus(theta2)
#    
#    #return best result
#    if residus1<residus2:
#        print('HAHA')
#        return theta1, origin1
#    return theta2, origin2
#
#thetaReal=np.pi/8
#OReal=np.array([.2,.6],dtype=float)
#for i in range(1000):
#    Xm,Xs=getBSData(thetaReal,OReal)
#plt.figure()
#plt.plot(Xm[:,0],Xm[:,1])
#plt.plot(Xs[:,0],Xs[:,1])
#theta, origin = solve(Xs,Xm)
#print(theta-thetaReal,origin-OReal)



