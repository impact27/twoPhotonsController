# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 14:25:19 2018

@author: Local_Admin
"""

import matplotlib.pyplot as plt
import numpy as np

fn = "motor_2times.txt"
#fn = "piezzo_without_plate_times.txt"
#fn = "piezzo_times.txt" 
#fn = "mixed_times.txt" 

with open(fn, 'r') as f:
    lines = f.readlines()
#%%
times = np.zeros(len(lines))
heights = np.zeros(len(lines))
xs = np.zeros(len(lines))
for i, l in enumerate(lines):
    t, pos = l.strip().split(',')
    t = float(t)
    X = np.fromstring(pos.strip()[1:-1], sep=" ")
    times[i] = t
    heights[i] = X[-1]
    xs[i] = X[0]

times -= times[0]   
heights -= heights[0] 
xs -= xs[0]
plt.figure()
plt.plot(heights, 'x')

plt.figure()
plt.plot(times, heights, 'x')
plt.figure()
plt.plot(times, xs, 'x')