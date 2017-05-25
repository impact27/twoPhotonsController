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
from PyQt5 import QtCore

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
        Xstage=self.md.get_XY_position(rawCoordinates=True)
        Xmaster=[x,y]
        image=self.parent.camera_delegate.get_image()
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
    
    def get_rotation_matrix(self,theta):
        c,s=np.cos(theta),np.sin(theta)
        R=np.array([[c,-s],[s,c]])
        return R
        
    def solve(self):
        """ solve the rotation and translation of Xstage and Xmaster
        
        
        with the least square method
        returns the best guess for theta, origin
        """
        
        Xstage=np.array([pos['Xstage'] for pos in self.positions])
        Xmaster=np.array([pos['Xmaster'] for pos in self.positions])
        if len(self.positions)==0:
            return np.nan, [np.nan, np.nan]
        elif len(self.positions)==1:
            return 0, 0, np.squeeze(Xstage-Xmaster)
        elif len(self.positions)==2:
            return (0, *self.solve2(Xstage, Xmaster))
        else:
            return self.solve3(Xstage, Xmaster)
        
    
    
    def solve2(self, Xstage, Xmaster):
        
        def getResidus(theta):
            R=self.get_rotation_matrix(theta)
            RXm=np.array([R@X for X in Xmaster])
            origin=1/len(Xstage)*np.sum(Xstage-RXm,axis=0)
            residus=np.sum((RXm+origin-Xstage)**2)
            return origin, residus
    
        #Get best theta
        Xs2=1/len(Xstage)*np.sum(Xstage,0)-Xstage
        
        dividend = np.sum(Xs2*Xmaster)
        divisor = np.sum(np.cross(Xs2,Xmaster))
        
        if divisor==0:
            theta1=0
        else:
            theta1 = (np.arctan(dividend/divisor)
                      -np.pi/2)
        
        #Theta is defined +-pi. Must test theta+pi
        origin1, residus1= getResidus(theta1)
        theta2=theta1+np.pi
        origin2, residus2 = getResidus(theta2)
        
        #return best result
        if residus1<residus2:
            return theta1, origin1
        return theta2, origin2
    
    def solve3(self, Xs, Xm):
        Xs2=Xs-1/len(Xs)*np.sum(Xs,0)
        Xm2=Xm-1/len(Xm)*np.sum(Xm,0)
        
        YsXs2 = np.sum(Xs[:, 1]*Xs2[:, 0])
        YsXm2 = np.sum(Xs[:, 1]*Xm2[:, 0])
        YsYm2 = np.sum(Xs[:, 1]*Xm2[:, 1])
        XmXs2 = np.sum(Xm[:, 0]*Xs2[:, 0])
        YmXs2 = np.sum(Xm[:, 1]*Xs2[:, 0])
        XmYs2 = np.sum(Xm[:, 0]*Xs2[:, 1])
        YmYs2 = np.sum(Xm[:, 1]*Xs2[:, 1])
        
        
        
        def fun(x, YsXs2, YsXm2, YsYm2, XmXs2, YmXs2, XmYs2, YmYs2):
            theta, phi = x
            return [  np.cos(phi)*YsXs2 
                    - np.cos(theta+phi)*YsXm2 
                    + np.sin(theta+phi)*YsYm2,
                      np.cos(theta+phi)*XmYs2
                    - np.sin(theta+phi)*YmYs2
                    - np.sin(theta)*XmXs2
                    - np.cos(theta)*YmXs2]
            
        def jac(x, YsXs2, YsXm2, YsYm2, XmXs2, YmXs2, XmYs2, YmYs2):
            theta, phi = x
            return [[  np.sin(theta+phi)*YsXm2 
                     + np.cos(theta+phi)*YsYm2,
                     - np.sin(phi)*YsXs2 
                     + np.sin(theta+phi)*YsXm2 
                     + np.cos(theta+phi)*YsYm2],
                   [ - np.sin(theta+phi)*XmYs2
                     - np.cos(theta+phi)*YmYs2
                     - np.cos(theta)*XmXs2
                     + np.sin(theta)*YmXs2,
                     - np.sin(theta+phi)*XmYs2
                     - np.cos(theta+phi)*YmYs2]]
                
        from scipy import optimize
        sol = optimize.root(fun, [0, 0], jac=jac, method='hybr', 
                            args=(YsXs2, YsXm2, YsYm2, XmXs2, YmXs2, XmYs2, YmYs2))
        theta, phi = sol.x
        
        Mphi = np.asarray([[1, np.sin(phi)],
                         [0, np.cos(phi)]])
        Rtheta = np.asarray([[np.cos(theta), -np.sin(theta)],
                              [np.sin(theta), np.cos(theta)]])
                
        Origin = 1/len(Xs)*np.sum(np.asarray([Mphi@X for X in Xs]) 
                                - np.asarray([Rtheta@X for X in Xm]),0)
        
        return phi, theta, Origin
        
    
    
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



