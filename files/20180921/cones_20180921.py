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
from power_converter import PowerConverter
# from pint import UnitRegistry
# ureg = UnitRegistry()
# Q_ = ureg.Quantity

# Settings

calibration_fn = 'calibration.csv'
script_fn = "cones_20181001olli.txt"

Y_motor_step = 7854.84
X_motor_step = 6203.05  # , 'um')
Y_N_motor = 3
X_N_motor = 6
width_write = 1300

Z_pos = 0  # , 'um')
y_lines_spacing = 5  # , 'um') #um
safety_z = 20  # , 'um')
off_speed = 1000  # , 'um/s')
dt = 0.5e-3  # s
y_lines_spacing_dots = 10  # um
x_margin = 2.5

dots_exposure_time = 0.0662
dots_spacing = 5
dots_intensity = 80.06

fix_speed = 37.76
power_range = [65, 40]

long_spacing = 10.5
long_length = 9.95

short_spacing = 5.59
short_length = 4.26

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


def add_wave_line(wave, wave_line, *, off_speed, dt):
    assert wave.shape[1] < max_points / 4

    # Add 0 laser power at beginning and end
    wave_line = np.insert(wave_line, 0,
                          [*wave_line[:3, 0], 0], axis=1)
    wave_line = np.insert(wave_line, np.shape(wave_line)[1],
                          [*wave_line[:3, -1], 0], axis=1)

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


def write_margin(y_lines_spacing, x_margin):
    line([-cube_width / 2 + x_margin, -cube_width / 2 + y_lines_spacing / 2, 0],
         [-cube_width / 2 + x_margin, cube_width / 2 - y_lines_spacing / 2, 0],
         power=pc.range_P[1],
         speed=50)


y_positions = np.arange(-cube_width / 2, cube_width / 2,
                        y_lines_spacing) + y_lines_spacing / 2
x_range = [-cube_width / 2 + x_margin,
           cube_width / 2 - x_margin]


N_lines = len(y_positions)

Y_offsets = [0, 300, 600, 900]

# %%


def get_lin_Psquare(speed, P_start, P_end, xstart, xend):
    line_length = np.abs(xend - xstart)
    t_max = line_length / speed
    time = np.arange(0, t_max, dt)
    X = time * speed + xstart
    Psquare = (P_end**2 - P_start**2) * time * speed / line_length + P_start**2
    return time, X, Psquare



# 1st long
motor_Y_idx = 0

positions = np.arange(x_range[0], x_range[1], long_spacing)

for motor_X_idx in range(X_N_motor):
    for Y_offset in Y_offsets:
        move_motor(motor_X_idx, motor_Y_idx, Y_offset=Y_offset)
        wave = np.zeros((4, 0))
        for line_idx in range(N_lines):
            for x in positions:
                xend = x + long_length
                if xend > x_range[1]:
                    xend = x_range[1]
                time, X, Psquare = get_lin_Psquare(
                    fix_speed,
                    power_range[0], power_range[1],
                    x, xend)
                wave_line = np.zeros((4, len(time)))
                wave_line[0] = X
                wave_line[1] = y_positions[line_idx]
                wave_line[2] = Z_pos
                wave_line[3] = pc.PtoV(np.sqrt(Psquare))
                wave = add_wave_line(wave, wave_line,
                                     off_speed=off_speed, dt=dt)
        script.waveform(wave, dt)


# 2nd short
motor_Y_idx = 1

positions = np.arange(x_range[0], x_range[1], short_spacing)

for motor_X_idx in np.arange(X_N_motor)[::-1]:
    for Y_offset in Y_offsets:
        move_motor(motor_X_idx, motor_Y_idx, Y_offset=Y_offset)
        wave = np.zeros((4, 0))
        for line_idx in range(N_lines):
            for x in positions:
                xend = x + short_length
                if xend > x_range[1]:
                    xend = x_range[1]
                time, X, Psquare = get_lin_Psquare(
                    fix_speed,
                    power_range[0], power_range[1],
                    x, xend)
                wave_line = np.zeros((4, len(time)))
                wave_line[0] = X
                wave_line[1] = y_positions[line_idx]
                wave_line[2] = Z_pos
                wave_line[3] = pc.PtoV(np.sqrt(Psquare))
                wave = add_wave_line(wave, wave_line,
                                     off_speed=off_speed, dt=dt)
        script.waveform(wave, dt)


# 3rd dots


y_positions = np.arange(-cube_width / 2, cube_width / 2,
                        y_lines_spacing_dots) + y_lines_spacing_dots / 2

N_lines = len(y_positions)

dots_pos = np.arange(x_range[0], x_range[1], dots_spacing)


# 2nd line: vary power
motor_Y_idx = 2
for motor_X_idx in range(X_N_motor):
    for Y_offset in Y_offsets:
        move_motor(motor_X_idx, motor_Y_idx, Y_offset=Y_offset)
        wave = np.zeros((4, 0))
        for idx in range(N_lines):
            for x in dots_pos:
                N_tstep = int(np.round(dots_exposure_time / dt))
                wave_line = np.zeros((4, N_tstep))
                wave_line[0] = x
                wave_line[1] = y_positions[idx]
                wave_line[2] = Z_pos
                wave_line[3] = pc.PtoV(dots_intensity)
                wave = add_wave_line(wave, wave_line,
                                     off_speed=off_speed, dt=dt)
        script.waveform(wave, dt)


script.save(script_fn)
print(script.min_time)
