# -*- coding: utf-8 -*-
"""
Created on Mon May  1 11:17:56 2017

@author: quentinpeter
"""
from matplotlib.image import imread
from glob import glob
import random
import numpy as np
import re

class camera_controller():
    def __init__(self):
        pass
        
    def get_image(self, z=None):
        fns='Misc/Images/50_50/*.bmp'
        reg='Misc/Images\/50_50\/(\d+)\.bmp'
        fns=glob(fns)
        if fns != []:
            fns=np.array(fns)
            X=np.array([int(re.search(reg,fn)[1]) for fn in fns])
            fns=fns[np.argsort(X)]
            X=X[np.argsort(X)]
            
            if z is not None:
                idx= np.argmin((z-X)**2)
                fn=fns[idx]
            else:
                fn=random.choice(fns)
            im=imread(fn)[:,:,0]
            return im
        else:
            print(fns)
            return np.random.rand(50,50)