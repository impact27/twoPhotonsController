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

y_lines_spacing = 10 #um

script_fn = 'cone_array.txt'

y_positions = np.arange(-cube_width/2, cube_width/2,
                        y_lines_spacing) + y_lines_spacing/2

def get_lin_Psquare(speed, P_start, P_end, xstart, xend):
    line_length = np.abs(xend - xstart)
    t_max = line_length / speed
    time = np.arange(0, t_max, dt)
    X = time * speed + xstart
    Psquare = (P_end**2 - P_start**2) * time * speed / line_length + P_start**2
    return time, X, Psquare

def get_wave_line(Xfrom, Xto, *, speed, dt):
    Xfrom = np.asarray(Xfrom)
    Xto = np.asarray(Xto)
    dX = Xto - Xfrom
    distance = np.linalg.norm(dX[:3])
    dXn = dX / distance
    times = np.arange(0, distance / speed, dt)
    
    wave = Xfrom[:, np.newaxis] + dXn[:, np.newaxis] * speed * times[np.newaxis]
    return wave

def add_wave_line(wave, wave_line, *, off_speed, dt):
    assert wave.shape[1] < max_points/4
    
    # Add 0 laser power at beginning and end
    wave_line = np.insert(wave_line, 0, 
                          [*wave_line[:3, 0], 0], axis=1)
    wave_line = np.insert(wave_line, np.shape(wave_line)[1], 
                          [*wave_line[:3, -1], 0], axis=1)
    
    if wave.shape[1]==0:
        return wave_line
    
    wave_move = get_wave_line(
            [*wave[:3, -1], 0],
            [*wave_line[:3, 0], 0], 
            speed=off_speed,
            dt=dt)
    
    if wave.shape[1] + wave_move.shape[1] + wave_line.shape[1] < max_points/4:
        return np.concatenate((wave, wave_move, wave_line), axis=1)
    
    else:
        script.waveform(wave, dt)
        return wave_line

wave = np.zeros((4, 0))
for idx in range(N_lines):
    positions = [0]
    new_pos = [0]
    i=1
    while new_pos[-1] < x_range[1]:
        positions = new_pos
        i += 1
        new_pos = np.cumsum(cone_length + np.linspace(1.5, 7.5, i))
        new_pos = np.insert(new_pos, 0, 0) + x_range[0]
    for x in positions:
        xend = x + cone_length
        if xend > x_range[1]:
            xend = x_range[1]
        time, X, Psquare = get_lin_Psquare(
                fix_speed,
                power_range[0], power_range[1],
                x, xend)
        wave_line = np.zeros((4, len(time)))
        wave_line[0] = y_positions[idx]
        wave_line[1] = X
        wave_line[2] = 0
        wave_line[3] = pc.PtoV(np.sqrt(Psquare))
        wave = add_wave_line(wave, wave_line,
                             off_speed=off_speed, dt=dt)
script.waveform(wave, dt)

script.save(script_fn)
print(script.min_time)