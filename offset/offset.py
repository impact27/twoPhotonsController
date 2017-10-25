# -*- coding: utf-8 -*-
"""
Created on Mon May 29 18:36:42 2017

@author: quentinpeter
"""
#%%

import registrator.image as ir
import registrator.channel as cr
from tifffile import imread
from matplotlib.pyplot import figure, imshow, plot
import cv2
import matplotlib.pyplot as plt
from scipy.signal import correlate2d
import numpy as np
from numpy.fft import fft2, fftshift

fns = ['data/cross.tif',
       'data/cross0.tif',
       'data/cross10x.tif',
       'data/cross10y.tif']

for i in range(1, 4):

    im = imread('data/cross.tif')
    im2 = imread(fns[i])
    bg = imread('data/crossbg.tif')

    im = 1. * im - bg
    im2 = 1. * im2 - bg

    im = cv2.GaussianBlur(im, (11, 11), 0)
    im2 = cv2.GaussianBlur(im2, (11, 11), 0)

    dy, dx = ir.find_shift_cc(im, im2)
    print(dy, dx)

    extent = (0, im.shape[1], 0, im.shape[0])

    figure()
    imshow(im, extent=extent)

    extent = (dx, im.shape[1] + dx, -dy, im.shape[0] - dy)
    imshow(im2, alpha=.5, extent=extent)


#%%
figure()
imshow(im)
plt.savefig('Subtracted.pdf')
figure()
imshow(imread('data/cross.tif'))
plt.savefig('Raw.pdf')
