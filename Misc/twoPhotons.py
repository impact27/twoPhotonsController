# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 13:01:05 2017

@author: quentinpeter
"""
import matplotlib.image as mpimg
from matplotlib.pyplot import figure, imshow, plot
import matplotlib as mpl
import numpy as np
from numpy.fft import fft2, fftshift, ifft2
from glob import glob
import matplotlib.pyplot as plt
import registrator.image as ir
import registrator.channel as cr
cmap = mpl.cm.get_cmap('inferno')
import re
from PIL import Image
'''
Images have same mean intensity
    -cut on the side
    -overexposed

Max + localization increase

Maybe shape can give info on orientation
'''
#%%
fns = 'Images/50_50/*.bmp'
reg = 'Images\/50_50\/(\d+)\.bmp'
fns = np.array(glob(fns))
X = np.array([int(re.search(reg, fn)[1]) for fn in fns])
fns = fns[np.argsort(X)]
X = X[np.argsort(X)]

# fns=fns[np.abs(X-50)<11]
# X=X[np.abs(X-50)<11]

ims = [mpimg.imread(n) for n in fns]
ims = np.asarray(ims)
ims = ims[:, :, :, 0]

#%%
maxim = np.max(ims, (1, 2))
idx = np.where(maxim > .9 * np.max(maxim))[0]
argbest = idx[np.sum(ims[idx] > .9 * np.max(ims[idx]), (1, 2)).argmin()]
imshow(ims[argbest])

#%%
Y = np.sum(ims[idx] > .9 * np.max(ims[idx]), (1, 2))
Xs = X[idx]

coeffs = np.polyfit(Xs, Y, 2)
F = np.poly1d(coeffs)
X2 = np.linspace(np.min(Xs), np.max(Xs))

mymax = -coeffs[1] / (2 * coeffs[0])
figure()
plot(Xs, Y, 'x')
plot(X2, F(X2), 'x')
plot([mymax, mymax], [400, 1400])

#%%
res = []
for im in ims:
    mask = im > (np.min(im) + np.max(im)) / 4
    figure()
    imshow(mask)
    res.append(np.sum(mask))
figure()
plot(X, res)
