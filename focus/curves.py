# -*- coding: utf-8 -*-
"""
Created on Tue May 16 09:33:52 2017

@author: quentinpeter
"""

import numpy as np
from glob import glob
from matplotlib.pyplot import figure, plot, imshow
import matplotlib.pyplot as plt

#%%
fns = 'data/*.npy'
for fn in glob(fns):
    figure()
    plot(*np.load(fn), 'x')
