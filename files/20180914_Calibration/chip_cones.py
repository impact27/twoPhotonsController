#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 14 15:11:14 2018

@author: quentinpeter
"""
from script import Script
from power_converter import PowerConverter
import numpy as np
calibration_fn = 'calibration.csv'
# Calibrate voltage V vs laser power P
pc = PowerConverter(calibration_fn)

safety_z = 20
off_speed = 1000
script = Script(off_speed=off_speed, safety_z=safety_z)


dt = 0.5e-3 #s
max_points = 262144

x_margin = 2.5
cube_width = 100
x_range = [-cube_width/2 + x_margin, 
           cube_width/2 - x_margin]


N_lines = 10
cone_length = 6
cone_spacing = 1.5
fix_speed = 37.76
power_range = [65, 40]

wave = np.zeros((4, 0))
for idx in range(N_lines):
    positions = [0]
    new_pos = [0]
    i=1
    while new_pos[-1] < x_range[1]:
        positions = new_pos
        i += 1
        new_pos = np.cumsum(cone_lengths[0] + np.linspace(1.5, 7.5, i))
        new_pos = np.insert(new_pos, 0, 0) + x_range[0]
    for x in positions:
        xend = x + clength
        if xend > x_range[1]:
            xend = x_range[1]
        time, X, Psquare = get_lin_Psquare(
                fix_speed,
                power_range[0], power_range[1],
                x, xend)
        wave_line = np.zeros((4, len(time)))
        wave_line[0] = X
        wave_line[1] = y_positions[idx]
        wave_line[2] = 0
        wave_line[3] = pc.PtoV(np.sqrt(Psquare))
        wave = add_wave_line(wave, wave_line,
                             off_speed=off_speed, dt=dt)
script.waveform(wave, dt)