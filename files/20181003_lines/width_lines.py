# -*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import plot, figure, imshow, show
import sys
import scipy.signal

sys.path.append('../package')

from script import Script
from power_converter import PowerConverter
# from pint import UnitRegistry
# ureg = UnitRegistry()
# Q_ = ureg.Quantity

# Settings

calibration_fn = 'calibration.csv'
script_fn = "line_width_Oliver.txt"

Y_motor_step = 7854.84
X_motor_step = 6203.05  # , 'um')
Y_N_motor = 3
X_N_motor = 6

piezo_delay = 0.01 #s
dt = 5e-3  # s

Z_pos = 0  # , 'um')
y_lines_spacing = 5  # , 'um') #um
safety_z = 20  # , 'um')
off_speed = 1000  # , 'um/s')
x_margin = 2.5

fix_speed = 37.76
width_dictionnary ={ # width: power
        300: 30.46257711,
        400: 34.5735335,
        500: 38.24525065,
        700: 44.69242649,
        1000: 52.91024225,
        }

# constants
max_points = 2**18
cube_width = 100  # , 'um')
safety_slope = 1/30 # no units


# Calibrate voltage V vs laser power P
pc = PowerConverter(calibration_fn)
motor_position = np.array([0, 0])
script = Script(off_speed=off_speed, safety_z=safety_z)

def move_motor(idx_X, idx_Y, *, X_offset=0, Y_offset=0,
               X_step=X_motor_step, Y_step=Y_motor_step):
    X = idx_X * X_step + X_offset
    Y = idx_Y * Y_step + Y_offset
    distance = np.linalg.norm(motor_position - np.asarray([X, Y]))
    Z = safety_z + distance * safety_slope
    script.safety_z = Z
    script.move_motor([X, Y, Z])
    motor_position[:] = [X, Y]

def line(Xfrom, Xto, *, power, speed):
    script.write_speed = speed
    script.write_voltage = pc.PtoV(power)
    script.write_line_piezo(Xfrom, Xto)


def get_wave_line(Xfrom, Xto, *, speed, dt):
    Xfrom = np.asarray(Xfrom)
    Xto = np.asarray(Xto)
    dX = Xto - Xfrom
    distance = np.linalg.norm(dX[:3])
    dXn = dX / distance
    times = np.arange(0, distance / speed, dt)

    wave = Xfrom[:, np.newaxis] + \
        dXn[:, np.newaxis] * speed * times[np.newaxis]
    return wave


def apply_delay(wave_line, piezo_delay, dt):
    assert(np.shape(wave_line)[0] == 4)
    N_delay = int(piezo_delay/ dt)
    wave_delay = np.ones((4, N_delay)) * wave_line[:, -1][:, np.newaxis]
    wave_line = np.concatenate((wave_line, wave_delay), axis=1)
    
    wave_line[3, N_delay:] = wave_line[3, :-N_delay]
    wave_line[3, :N_delay] = 0
    
    
    # Add 0 laser power at beginning and end
    wave_line = np.insert(wave_line, 0,
                          [*wave_line[:3, 0], 0], axis=1)
    wave_line = np.insert(wave_line, np.shape(wave_line)[1],
                          [*wave_line[:3, -1], 0], axis=1)
    
    return wave_line

def add_wave_line(wave, wave_line, *, off_speed, dt):
    assert wave.shape[1] < max_points / 4

    wave_line = apply_delay(wave_line, piezo_delay, dt)

    if wave.shape[1] == 0:
        return wave_line

    wave_move = get_wave_line(
        [*wave[:3, -1], 0],
        [*wave_line[:3, 0], 0],
        speed=off_speed,
        dt=dt)

    if wave.shape[1] + wave_move.shape[1] + \
            wave_line.shape[1] < max_points / 4:
        return np.concatenate((wave, wave_move, wave_line), axis=1)

    else:
        script.waveform(wave, dt)
        return wave_line


y_positions = np.arange(-cube_width / 2, cube_width / 2,
                        y_lines_spacing) + y_lines_spacing / 2
x_range = [-cube_width / 2 + x_margin,
           cube_width / 2 - x_margin]


N_lines = len(y_positions)

Y_offsets = np.arange(5) * 300
widths = [300, 400, 500, 700, 1000]

# 1st long
for motor_Y_idx in range(Y_N_motor):
    for motor_X_idx in np.arange(X_N_motor)[::(motor_Y_idx % 2 ==0) * 2 - 1]:
        for idx_square, Y_offset in enumerate(Y_offsets):
            move_motor(motor_X_idx, motor_Y_idx, Y_offset=Y_offset)
            wave = np.zeros((4, 0))
            for line_idx in range(N_lines):
                dx = fix_speed * dt
                X = np.arange(*x_range, dx)
                
                wave_line = np.zeros((4, len(X)))
                
                P = width_dictionnary[widths[idx_square]]
                wave_line[0] = X
                wave_line[1] = y_positions[line_idx]
                wave_line[2] = Z_pos
                wave_line[3] = pc.PtoV(P)
                wave = add_wave_line(wave, wave_line,
                                     off_speed=off_speed, dt=dt)
            script.waveform(wave, dt)


script.save(script_fn)
print(script.min_time)
