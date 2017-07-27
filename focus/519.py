# -*- coding: utf-8 -*-
"""
Created on Mon May 22 11:19:47 2017

@author: quentinpeter
"""

import numpy as np
from matplotlib.pyplot import figure, plot, imshow
import matplotlib.pyplot as plt
from glob import glob
import re
#%%
def get_spot_sizes(imrange):
    return np.sum(imrange >= 
                  np.reshape(np.max(imrange,(1,2))/50,(-1,1,1)),
                  (1,2))
    
def get_spot_sizes(imrange):
    return np.sum(imrange >= 25,
                  (1,2))
#%%

fnim = 'data20170519/10V/coarse_im.npy'
fnz = 'data20170519/10V/coarse_z.npy'

ims = np.load(fnim)[:-6]
Z = np.load(fnz)[:-6]
sizes = get_spot_sizes(ims)
#%
#figure()
#plot(Z,np.max(ims,(1,2)))
figure()
plot(Z,sizes,'x')
plt.xlabel('Z [$\mu$m]')
plt.ylabel('Size [px]')
plt.savefig('Coarse.pdf')

#%%

fnim = 'data20170519/10V/medium_im.npy'
fnz = 'data20170519/10V/medium_z.npy'

ims = np.load(fnim)
Z = np.load(fnz)
sizes = get_spot_sizes(ims)
#%
#figure()
#plot(Z,np.max(ims,(1,2)))
figure()
plot(Z,sizes,'x')
plt.xlabel('Z [$\mu$m]')
plt.ylabel('Size [px]')
plt.savefig('Medium.pdf')
#%%
masks = ims >= np.reshape(np.max(ims,(1,2))/10,(-1,1,1))

#%%
figure()
plot(Z,
     np.sum(ims>8,(1,2)),'x')

##%%
#for im in ims:
#    figure()
#    imshow(im[1300:1450,1700:1850],vmax=125)