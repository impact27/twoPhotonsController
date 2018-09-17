# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, figure, imshow, show
import sys
import scipy.signal
def sawtooth(*args, **kargs):
    return 0.5 * (scipy.signal.sawtooth(*args, **kargs) + 1)

sys.path.append('../package')

from script import Script
from GText import get_gtext


# Settings

offset_range = [0, -3] # um
calibration_fn = 'calibration.csv'
motor_step = 125
cube_width = 100
script_fn = "line.txt"

energy_density_range = [0, 3] #mJ/um
y_lines_spacing = 5 #um

# Calibrate voltage V vs laser power P
motor_line = 0

safety_z = 20
off_speed = 1000

fraction = 0.95
dt = 0.5e-3 #s

wavelength = 2 #um

max_points = 262144

script = Script(off_speed=off_speed, safety_z=safety_z)

times_range_dots = np.asarray([1, 100]) * 1e-3 #ms
y_lines_spacing_dots = 10 #um
x_margin = 2.5


# =============================================================================
# 1st type - Calibration
# =============================================================================


x_range = [-cube_width/2 + x_margin, 
           cube_width/2 - x_margin]
line_length = x_range[1] - x_range[0]

P_max = 113.3
P_min = 25 #mW
S_min = 37.76 #um/s
S_max = S_min * P_max**2 / P_min**2


#%%

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



time, X = get_lin_inv_speed(S_min, S_max, *x_range)
wave_line = np.zeros((4, len(time)))
wave_line[0] = X
wave_line[1] = 0
wave_line[2] = 0
wave_line[3] = np.linspace(0, 5, len(X))
script.waveform(wave_line, dt)


script.save(script_fn)
print(script.min_time)

script = Script(off_speed=off_speed, safety_z=safety_z)
time = np.arange(0, line_length / S_max, dt)
wave_line = np.zeros((4, len(time)))
wave_line[0] = np.linspace(*x_range, len(time))
wave_line[1] = 0
wave_line[2] = 0
wave_line[3] = np.linspace(0, 5, len(time))
script.waveform(wave_line, dt)
script.save('cste_speed.txt')
