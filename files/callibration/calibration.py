# -*- coding: utf-8 -*-
import numpy as np
from twophscript.canvas import Piezo_Canvas, Motor_Canvas
from twophscript.scriptfile import ScriptFile


# Settings
cube_width = 100

calibration_fn = 'PV_curve.csv'
script_fn = "calibration_20180914.txt"

safety_z = 20
off_speed = 1000
dt = 0.5e-3  # s
measure_dt = 1e-3
motor_step = 125
x_margin = 2.5
minZmargin = 10
safety_slope = 1/100


x_range = [-cube_width / 2 + x_margin,
           cube_width / 2 - x_margin]

file = ScriptFile()

# Functions


def uniform_spacing(spacing):
    return np.arange(-cube_width / 2, cube_width / 2, spacing) + spacing / 2


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


def Canvas():
    canvas = Piezo_Canvas(calibration_fn, off_speed, dt,
                          x_margin, minZmargin, safety_slope, measure_dt)

    Xto = [-cube_width / 2 + x_margin,
           -cube_width / 2 + x_margin,
           0]
    Xfrom = [-cube_width / 2 + x_margin,
             cube_width / 2 - x_margin,
             0]
    canvas.add_line(Xfrom, Xto, speed=50, power=100)
    return canvas


# =============================================================================
# 1st type - Calibration
# =============================================================================
y_lines_spacing = 5  # um
y_positions = uniform_spacing(y_lines_spacing)
N_lines = len(y_positions)

P_max = 100  # mW
P_min = 30  # mW
S_min = 40   # um/s
S_max = S_min * P_max**2 / P_min**2
P_lines = np.sqrt(np.linspace(P_min**2, P_max**2, N_lines))
S_lines = 1 / np.linspace(1 / S_max, 1 / S_min, N_lines)
P_fix = P_max
S_fix = S_min

Zspeed = 150
offset_range = [1, -2]  # um
Z_lines = np.linspace(offset_range[0], offset_range[1], N_lines)

motor_X = 0
motor_Y = 0


# 1st - P**2 vs 1/S, z=0

canvas_P2vsSm1 = Canvas()
for idx in range(N_lines):
    speed = S_lines[idx]
    time, X, Psquare = get_lin_Psquare(speed, P_max, P_min, *x_range)

    wave_line = np.zeros((4, len(time)))
    wave_line[0] = X
    wave_line[1] = y_positions[idx]
    wave_line[2] = 0
    wave_line[3] = np.sqrt(Psquare)

    canvas_P2vsSm1.add_wave(wave_line)
    if idx % 4 == 0:
        canvas_P2vsSm1.save_wave('calibration/P2vsSm1')

canvas_P2vsSm1.write_at(file, [motor_X, motor_Y])
motor_X += motor_step


# 2nd - 1/S vs P**2, z=0

canvas_Sm1vsP2 = Canvas()
for idx in range(N_lines):
    time, X = get_lin_inv_speed(S_min, S_max, *x_range)

    wave_line = np.zeros((4, len(time)))
    wave_line[0] = X
    wave_line[1] = y_positions[idx]
    wave_line[2] = 0
    wave_line[3] = P_lines[idx]

    canvas_Sm1vsP2.add_wave(wave_line)
    if idx % 4 == 0:
        canvas_Sm1vsP2.save_wave('calibration/Sm1vsP2')

canvas_Sm1vsP2.write_at(file, [motor_X, motor_Y])
motor_X += motor_step


# 3rd - P**2 vs z, s = S_min

canvas_P2vsZ = Canvas()
time, X, Psquare = get_lin_Psquare(Zspeed, P_max, P_min, *x_range)
for idx in range(N_lines):

    wave_line = np.zeros((4, len(time)))
    wave_line[0] = X
    wave_line[1] = y_positions[idx]
    wave_line[2] = Z_lines[idx]
    wave_line[3] = np.sqrt(Psquare)

    canvas_P2vsZ.add_wave(wave_line)
    if idx % 4 == 0:
        canvas_P2vsZ.save_wave('calibration/P2vsZ')

canvas_Sm1vsP2.write_at(file, [motor_X, motor_Y])


# =============================================================================
# 2nd type: dots
# =============================================================================

motor_Y += motor_step
motor_X = 0

y_lines_spacing_dots = 10  # um
y_positions = uniform_spacing(y_lines_spacing_dots)
N_lines = len(y_positions)

# for times, reuse speeds with typical length = 2um
dots_exp_times = 2 / S_lines[1::2]
dots_intensity = P_lines[1::2]
assert len(dots_intensity) == N_lines
fix_dots_exp_times = np.max(dots_exp_times)
fix_dots_intensity = np.max(dots_intensity)

dots_spacings = np.linspace(1, 10, 17)
dots_pos = x_range[1] - np.insert(np.cumsum(dots_spacings), 0, 0)

# 1st: Vary times for max power
canvas_timedots = Canvas()
for line_idx in range(N_lines):
    for x in dots_pos:
        N_tstep = int(np.round(dots_exp_times[line_idx] / dt))
        wave_line = np.zeros((4, N_tstep))
        wave_line[0] = x
        wave_line[1] = y_positions[line_idx]
        wave_line[2] = 0
        wave_line[3] = fix_dots_intensity
        canvas_timedots.add_wave(wave_line)
    if idx % 2 == 0:
        canvas_timedots.save_wave('calibration/timedots')

canvas_timedots.write_at(file, [motor_X, motor_Y])
motor_X += motor_step

# 2nd line: vary power
canvas_powerdots = Canvas()
for line_idx in range(N_lines):
    for x in dots_pos:
        N_tstep = int(np.round(fix_dots_exp_times / dt))
        wave_line = np.zeros((4, N_tstep))
        wave_line[0] = x
        wave_line[1] = y_positions[line_idx]
        wave_line[2] = 0
        wave_line[3] = dots_intensity[line_idx]
        canvas_powerdots.add_wave(wave_line)
    if idx % 2 == 0:
        canvas_powerdots.save_wave('calibration/timedots')

canvas_powerdots.write_at(file, [motor_X, motor_Y])
motor_X += motor_step


# =============================================================================
# 3rd type: Funnels!
# =============================================================================

motor_Y += motor_step
motor_X = 0

y_lines_spacing = 5  # um
y_positions = uniform_spacing(y_lines_spacing)
N_lines = len(y_positions)


cone_lengths = np.linspace(2.5, 12, N_lines)
fix_speed = 40
power_range = [65, 40]
space_range = [-1, 2]


def getfunnelpos(clength):
    positions = [0]
    new_pos = [0]
    i = 1
    while new_pos[-1] < x_range[1]:
        positions = new_pos
        i += 1
        new_pos = np.cumsum(cone_lengths[line_idx]
                            + np.linspace(*space_range, i))
        new_pos = np.insert(new_pos, 0, 0) + x_range[0]
    return positions


def gel_lin_Psquare(speed, P_start, P_end, X, xstart, length):
    Psquare = (P_end**2 - P_start**2) * (X - xstart) / length + P_start**2
    return Psquare


line_length = np.diff(x_range)[0]
t_max = line_length / fix_speed
time = np.arange(0, t_max, dt)
X = time * speed + x_range[0]
power_rangers = [[65, 40], [65, 20], [100, 35]]
for power_range in power_rangers:
    # vary P
    canvas_funnel = Canvas()
    for line_idx in range(N_lines):
        wave_line = np.zeros((4, len(time)))
        wave_line[0] = X
        wave_line[1] = y_positions[line_idx]
        wave_line[2] = 0
        clength = cone_lengths[line_idx]
        positions = getfunnelpos(clength)

        for x in positions:
            wave_line[3, X > x] = np.sqrt(gel_lin_Psquare(
                    fix_speed, power_range[0], power_range[1],
                    X[X > x], x, clength))
        canvas_funnel.add_wave(wave_line.copy())
        if idx % 2 == 0:
            canvas_funnel.save_wave('calibration/funnel')
    canvas_funnel.write_at(file, [motor_X, motor_Y])
    motor_X += motor_step


file.save(script_fn)

print(file.min_time)
