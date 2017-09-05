# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 18:29:57 2017

@author: quentinpeter
"""
import cv2
import numpy as np

import registrator.image as ir

class XYcorrector():
    
    def __init__(self, motor, camera):
        self._refim = None
        self.motor = motor
        self.camera = camera
        
    def align(self, wait=True, checkid=None):
        """Use camera to align current image with ref image
        """
        if self._refim is None:
            #Save new reference image
            self._refim = self.camera.get_image()
        else:
            #Move
            self.motor.move_by(self.getOffset(), wait=wait, checkid=checkid)
           
    def getOffset(self):
        """Get offset between reference and current image
        """
        if self._refim is None:
            #No ref = no offset
            return np.zeros(3)
        #Blur images to get rid of noise    
        curim = self.camera.get_image()
        refim=cv2.GaussianBlur(self._refim,(11,11),0)
        curim=cv2.GaussianBlur(curim,(11,11),0)
        #Get offset in um
        dy, dx = ir.find_shift_cc(refim, curim)
        dX = np.multiply([dx, dy, 0],self.camera.pixelSize)
        return dX
    
    
class Zcorrector():
    
    def __init__(self, motor, camera, ZRangeSize, imageCanvas):
        super().__init__()
        self.motor = motor
        self.camera = camera
        self.error = None
        self._empty_im = np.zeros_like(self.camera.get_image())
        self.ZRangeSize = ZRangeSize
        self.lockid = None
        self.ic = imageCanvas
        
    
    def get_image_range(self, zPos, condition=None):
        """get the images corresponding to the positions in zPos
        
        condition gives the stop value
        """
        imrange=np.tile(self._empty_im, (len(zPos), 1, 1))
        
        if condition is None:
            def condition(a,b): return False
            
        for im, z in zip(imrange, zPos):
            self.motor.goto_position([np.nan , np.nan, z], 
                                 wait=True, checkid=self.lockid)
            im[:]=self.camera.get_image()
            if condition(im,imrange):
                return imrange
        return imrange
     
    def startlaser(self):
        self.camera.autoShutter(False)
        self._camshutter = self.camera.shutter
        self.camera.set_shutter(self.camera.shutter_range()[0])
#         self.laser.open_shutter()
        
    def endlaser(self):
        self.camera.shutter = self._camshutter
#         self.laser.close_shutter()
       
    def plot(self, X, Y, Y2):
        self.ic.plot(X[Y<4*np.min(Y)],Y[Y<4*np.min(Y)],'.', c='C0')
        self.ic._axes.twinx().plot(X,Y2,'x',c='C1')
        self.ic.draw()
    def focus(self, Npass=3, checkid=None):
        """ Go to the best focal point for the laser
        """
        self.lockid = checkid
        def get_spot_sizes(imrange):
            return np.sum(imrange >= 
                          np.reshape(np.max(imrange,(1,2))/10,(-1,1,1)),
                          (1,2))
        
        def max_condition(im,ims):
            return np.max(im)<np.max(ims)/2
        
        self.startlaser()
        
        Z = self.motor.position[2]
        zrange = [Z-self.ZRangeSize/2, Z+self.ZRangeSize/2]
        Zs = []
        Is = []
        Ss = []
        for i in range(Npass):
            zPos=np.linspace(*zrange,21)
            imrange=self.get_image_range(zPos, max_condition)
            
            intensity = np.max(imrange, (1, 2))
            argbest = np.argmax(intensity)
        
            if argbest == 0:
                zrange = [zPos[argbest], zPos[argbest+1]]
            elif argbest == len(intensity)-1:
                zrange = [zPos[argbest-1], zPos[argbest]]
            else:
                zrange = [zPos[argbest-1], zPos[argbest+1]]
            
            if i>0:
                size = get_spot_sizes(imrange)
                Zs.extend(zPos)
                Is.extend(intensity)
                Ss.extend(size)
                self.plot(zPos, intensity, size)
                
        self.motor.goto_position([np.nan , np.nan, zPos[argbest]], 
                                 wait=True, checkid=self.lockid)

        self.endlaser()
        #save result and position
        return np.asarray([Zs, Ss, Is])