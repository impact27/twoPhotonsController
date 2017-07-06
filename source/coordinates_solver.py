# -*- coding: utf-8 -*-
"""
Created on Wed Jul  5 11:24:12 2017

@author: quentinpeter
"""
import numpy as np
from scipy import optimize

class Zsolver():
    
    def solve(self, Xstage):
        """a*X + b*Y + c = Z
        """
        Xstage = np.asarray(Xstage)
        
        N = len(Xstage)
        if N==0:
            return np.zeros(3)

        elif N<3:
            return np.array([0, 0, np.mean(Xstage[:,2],0)])
            
        X, Y, Z = Xstage.T
        
        M=np.asarray([[np.sum(X),   np.sum(Y),   len(X)],
                      [np.sum(X*X), np.sum(X*Y), np.sum(X)],
                      [np.sum(X*Y), np.sum(Y*Y), np.sum(Y)]])
        
        b=np.asarray([[np.sum(Z)],
                      [np.sum(X*Z)], 
                      [np.sum(Y*Z)]])
        
        coeffs=np.linalg.inv(M)@b
        return np.squeeze(coeffs)             
                
class XYsolver():
    
    def solve(self, XYstage, XYmaster):
        """ solve the rotation and translation of XYstage and XYmaster
        
        
        with the least square method
        returns the best guess for theta, origin
        
        M@XYs = R@XYm + O
        With M = [[1, sin], [0, cos]]
        R rotation matrix
        O offset
        """
        
        N=len(XYstage)
#         XYstage=np.array([pos['XYstage'] for pos in self.positions])
#         XYmaster=np.array([pos['XYmaster'] for pos in self.positions])
        if N==0:
            return 0, 0, [0, 0]
        elif N==1:
            return self.solve1(XYstage, XYmaster)
        elif N==2:
            return self.solve2(XYstage, XYmaster)
        else:
            return self.solve3(XYstage, XYmaster)
        
    
    def solve1(self, XYstage, XYmaster):
        return 0, 0, np.squeeze(XYstage-XYmaster)
    
    def solve2(self, XYstage, XYmaster):
        
        def getResidus(theta):
            R=self.get_rotation_matrix(theta)
            RXm=np.array([R@X for X in XYmaster])
            origin=1/len(XYstage)*np.sum(XYstage-RXm,axis=0)
            residus=np.sum((RXm+origin-XYstage)**2)
            return origin, residus
    
        #Get best theta
        XYs2=1/len(XYstage)*np.sum(XYstage,0)-XYstage
        
        dividend = np.sum(XYs2*XYmaster)
        divisor = np.sum(np.cross(XYs2,XYmaster))
        
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
            return 0, theta1, origin1
        return 0, theta2, origin2
    
    def solve3(self, XYs, XYm):
        XYs2=XYs-1/len(XYs)*np.sum(XYs,0)
        XYm2=XYm-1/len(XYm)*np.sum(XYm,0)
        
        YsXs2 = np.sum(XYs[:, 1]*XYs2[:, 0])
        YsXm2 = np.sum(XYs[:, 1]*XYm2[:, 0])
        YsYm2 = np.sum(XYs[:, 1]*XYm2[:, 1])
        XmXs2 = np.sum(XYm[:, 0]*XYs2[:, 0])
        YmXs2 = np.sum(XYm[:, 1]*XYs2[:, 0])
        XmYs2 = np.sum(XYm[:, 0]*XYs2[:, 1])
        YmYs2 = np.sum(XYm[:, 1]*XYs2[:, 1])
        
        
        
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
                
        
        sol = optimize.root(fun, [0, 0], jac=jac, method='hybr', 
                            args=(YsXs2, YsXm2, YsYm2, XmXs2, YmXs2, XmYs2, YmYs2))
        theta, phi = sol.x
        
        Mphi = np.asarray([[1, np.sin(phi)],
                         [0, np.cos(phi)]])
        Rtheta = np.asarray([[np.cos(theta), -np.sin(theta)],
                              [np.sin(theta), np.cos(theta)]])
                
        Origin = 1/len(XYs)*np.sum(np.asarray([Mphi@XY for XY in XYs]) 
                                - np.asarray([Rtheta@XY for XY in XYm]),0)
        
        return phi, theta, Origin
    
    def get_rotation_matrix(self,theta):
        c,s=np.cos(theta),np.sin(theta)
        R=np.array([[c,-s],[s,c]])
        return R