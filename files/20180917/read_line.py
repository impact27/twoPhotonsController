#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 17 12:08:23 2018

@author: quentinpeter
"""

import numpy as np
from matplotlib.pyplot import plot, show, imshow, figure
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
# %%


def get_lin_inv_speed(S_start, S_end, xstart, xend):
    line_length = np.abs(xend - xstart)
    # 1/v = (1/vmax - 1/vmin)*(x-x0)/(xf-x0) + 1/vmin
    A = (1 / S_end - 1 / S_start) / line_length
    B = 1 / (S_start * A)
    # solve for v = 1 / (A*(x' + B)), x' = x - x0
    t_max = A / 2 * line_length * (line_length + 2 * B)
    time = np.arange(0, t_max, dt)
    X = np.sign(B) * np.sqrt(2 * time / A + B**2) - B + xstart
    return time, X


# %%
from scipy.interpolate import interp1d
dt = 0.5e-3
fn = 'positions.dat'
fn = 'linear.dat'
fn = 'speed_38.dat'
# fn = 'speed_38_inv.dat'

fns = ['positions.dat']#, 'linear.dat', 'speed_38.dat']
names = ['Acceleration', 'fast', 'slow']
for fn, name in zip(fns, names):

    P_max = 113.3
    P_min = 25  # mW
    S_min = 37.76  # um/s
    S_max = S_min * P_max**2 / P_min**2
    xstart = 2.5
    xend = 97.5

    data = np.loadtxt(fn, skiprows=76)
    theoritical = get_lin_inv_speed(S_min, S_max, xstart, xend)[1]
    # data = data[:len(data) // 3]
    T = np.arange(len(data)) * dt

    # %%
    figure()
    plot(T - 0.01, data[:, 0], '.', label='Measured')
    plot(T, data[:, 1], '-', label='Target')

    # plot(T, get_lin_inv_speed(S_min, S_max, xstart, xend)[1])
    plt.xlabel('Time [s]')
    plt.ylabel('Position [um]')
    plt.legend()
    plt.savefig(name + '_position.pdf')

    # %%

    measured = interp1d(data[:, 0], T)
    target = interp1d(data[:, 1], T)

    pos = np.linspace(np.max(np.min(data[:, :2], 0)), np.min(
        np.max(data[:, :2], 0)), 100)

    figure()
    plot(pos[1:-1], 1e3 * (measured(pos) - target(pos))[1:-1], '.')
    plot(pos, 0 * pos + 10)
    plt.xlabel('Position [um]')
    plt.ylabel('Delay [ms]')
    plt.savefig(name + '_delay.pdf')
    # plt.ylim((0, plt.ylim()[1]))

    # %%
    Hpos0 = 0.5 * (data[1:, 0] + data[:- 1, 0])
    Hpos1 = 0.5 * (data[1:, 1] + data[:- 1, 1])
    figure()
    plot(Hpos0, np.diff(data[:, 0]) / dt, '.', label='Measured')
    plot(Hpos1, np.diff(data[:, 1]) / dt, '-', label='Target')
    # plot(Hpos0, np.diff(savgol_filter(data[:, 0], 21, 3))/dt)

    plt.xlabel('Position [um]')
    plt.ylabel('Speed [um/s]')
    plt.legend()

    plt.savefig(name + '_speed.pdf')
    # %%
    figure()
    plot(data[1:-1, 0], 1e-3 * np.diff(savgol_filter(data[:, 0], 21, 3), 2) / dt**2,
         '.', label='Measured')
    plot(data[1:-1, 1], 1e-3 * np.diff(savgol_filter(data[:, 1], 21, 3), 2) / dt**2,
         '-', label='Target')

    plt.xlabel('Position [um]')
    plt.ylabel('Acceleration [mm/s^2]')
    plt.legend()
    # %%

    figure()
    plot(Hpos0,
         1 / (np.diff(savgol_filter(data[:, 0], 21, 3)) / dt),
         '.', label='measured')
    plot(np.linspace(xstart, xend, len(T)), np.linspace(1 / S_min, 1 / S_max, len(T)),
         label='linear 1/S')
    plt.yscale('log')
    plt.xlabel('Position [um]')
    plt.ylabel('1/Speed [s/um]')
    plt.legend()
