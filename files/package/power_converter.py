#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 16:55:36 2018

@author: quentinpeter
"""
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d


class PowerConverter():
    
    def __init__(self, fn):
        curve = np.loadtxt(fn, delimiter=',')

        P = curve[:, 1]
        V = curve[:, 0]
        
        P = P[np.argsort(V)]
        V = V[np.argsort(V)]
        
        #Add 0 to have it in range
        V = np.insert(V, 0, 0)
        P = np.insert(P, 0, 0)
        
        self.range_P = [np.min(P), np.max(P)]
        self.range_V = [np.min(V), np.max(V)]
        
        end_idx = np.argmax(P) + 1

        self.VtoP = interp1d(V, P)
        self.PtoV = interp1d(P[:end_idx], V[:end_idx])
   
if __name__ == '__main__':
    pc = PowerConverter()
    fn = 'calibration.csv'
    pc.set_calibration(fn)
    
    curve = np.loadtxt(fn, delimiter=',')

    P = curve[:, 1]
    V = curve[:, 0]
    
    v = np.linspace(*pc.range_V, 100)
    p = np.linspace(*pc.range_P, 100)
    
    plt.figure()
    plt.plot(V, P, 'x')
    plt.plot(v, pc.VtoP(v))
    plt.plot(pc.PtoV(p), p)

#%%