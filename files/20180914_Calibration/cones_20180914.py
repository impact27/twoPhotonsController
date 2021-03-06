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


from power_converter import PowerConverter

# Settings

offset_range = [0, -3]  # um
calibration_fn = 'calibration.csv'
motor_step = 125
cube_width = 100
script_fn = "cones_20180914.txt"

energy_density_range = [0, 3]  # mJ/um
y_lines_spacing = 5  # um

# Calibrate voltage V vs laser power P
pc = PowerConverter(calibration_fn)
motor_line = 0

safety_z = 20
off_speed = 1000

fraction = 0.95
dt = 0.5e-3  # s

wavelength = 2  # um

max_points = 262144

script = Script(off_speed=off_speed, safety_z=safety_z)

times_range_dots = np.asarray([1, 100]) * 1e-3  # ms
y_lines_spacing_dots = 10  # um
x_margin = 2.5
list_spacings_dots = np.arange(1, 6)

dots_z_cubes = [0, -0.5, -1, -2, -3]
dots_spacings = np.linspace(1, 10, 17)


def move_motor(line, column, step):
    script.move_motor([column * step, line * step, safety_z])


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


def get_lin_Psquare(speed, P_start, P_end, xstart, xend):
    line_length = np.abs(xend - xstart)
    t_max = line_length / speed
    time = np.arange(0, t_max, dt)
    X = time * speed + xstart
    Psquare = (P_end**2 - P_start**2) * time * speed / line_length + P_start**2
    return time, X, Psquare


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
# =============================================================================
# 3rd type: Christmas trees!
# =============================================================================


y_positions = np.arange(-cube_width / 2, cube_width / 2,
                        y_lines_spacing) + y_lines_spacing / 2
x_range = [-cube_width / 2 + x_margin,
           cube_width / 2 - x_margin]
N_lines = len(y_positions)
cone_lengths = np.linspace(3, 15, N_lines)

fix_speed = 37.76
power_range = [65, 40]

fix_power = 113.3
inv_speed_range = [0.001, 0.0001]

# 1st block - vary P

move_motor(motor_line, 0, motor_step)
write_margin(y_lines_spacing, x_margin)


wave = np.zeros((4, 0))
for idx in range(N_lines):
    clength = cone_lengths[idx]
    positions = [0]
    new_pos = [0]
    i = 1
    while new_pos[-1] < x_range[1]:
        positions = new_pos
        i += 1
        new_pos = np.cumsum(clength + np.linspace(1.5, 7.5, i))
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

# 2nd block - vary v

move_motor(motor_line, 1, motor_step)
write_margin(y_lines_spacing, x_margin)


wave = np.zeros((4, 0))
for idx in range(N_lines):
    clength = cone_lengths[idx]
    positions = [0]
    new_pos = [0]
    i = 1
    while new_pos[-1] < x_range[1]:
        positions = new_pos
        i += 1
        new_pos = np.cumsum(clength + np.linspace(1.5, 7.5, i))
        new_pos = np.insert(new_pos, 0, 0) + x_range[0]
    for x in positions:
        xend = x + clength
        if xend > x_range[1]:
            xend = x_range[1]
        time, X = get_lin_inv_speed(
            1 / inv_speed_range[0], 1 / inv_speed_range[1], x, xend)
        wave_line = np.zeros((4, len(time)))
        wave_line[0] = X
        wave_line[1] = y_positions[idx]
        wave_line[2] = 0
        wave_line[3] = pc.PtoV(fix_power)
        wave = add_wave_line(wave, wave_line,
                             off_speed=off_speed, dt=dt)
script.waveform(wave, dt)

get_gtext(script._lines, 'piezo', [-50, -250], 100, pc.PtoV(pc.range_P[1]), 50)

script.save(script_fn)
print(script.min_time)
