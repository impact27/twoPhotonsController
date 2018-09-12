# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
import sys
import scipy.signal
def sawtooth(*args, **kargs):
    return 0.5 * (scipy.signal.sawtooth(*args, **kargs) + 1)

sys.path.append('../package')

from script import Script
from GText import get_gtext


from power_converter import PowerConverter

# Settings

offset_range = [0, -3] # um
calibration_fn = 'calibration.csv'
motor_step = 125
cube_width = 100
script_fn = "calibration_20180910.txt"

energy_density_range = [0, 3] #mJ/um
y_lines_spacing = 5 #um

# Calibrate voltage V vs laser power P
pc = PowerConverter(calibration_fn)
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
list_spacings_dots = np.arange(1, 6)

def move_motor(line, column, step):
    script.move_motor([column*step, line*step, safety_z])
    
def line(Xfrom, Xto, *, power, speed):
    script.write_speed = speed
    script.write_voltage = pc.PtoV(power)
    script.write_line_piezo(Xfrom, Xto)
    
def get_wave_line(Xfrom, Xto, *, speed, dt):
    Xfrom = np.asarray(Xfrom)
    Xto = np.asarray(Xto)
    dX = Xto - Xfrom
    distance = np.linalg.norm(dX)
    dXn = dX / distance
    times = np.arange(0, distance / speed, dt)
    
    wave = Xfrom[:, np.newaxis] + dXn[:, np.newaxis] * speed * times[np.newaxis]
    return wave
    
    
def dots_line(Xfrom, Xto, *, spacing, exposure_time, power, dt):
    Xfrom = np.asarray(Xfrom)
    Xto = np.asarray(Xto)
    XY_distance = np.linalg.norm(Xto[:2] - Xfrom[:2])
    ndots = int(np.floor(XY_distance / spacing)) + 1
    
    ndim = 3
    dot_pos = np.zeros((ndim, ndots))
    for idx_dim in range(ndim):
        dot_pos[idx_dim] = np.linspace(Xfrom[idx_dim], Xto[idx_dim], ndots)
    
    wave = np.append(Xfrom, 0)[:, np.newaxis]
    
    for idx_pos in range(ndots):
        # Move to position
        if idx_pos > 0:
            wave_move = get_wave_line(
                    [*dot_pos[:, idx_pos - 1], 0],
                    [*dot_pos[:, idx_pos], 0],
                    speed=off_speed,
                    dt=dt)
            wave = np.concatenate((wave, wave_move), axis=1)
        
        Nt = int(exposure_time / dt)
        wavedot = np.zeros((4, Nt + 2))
        for idx_dim in range(ndim):
            wavedot[idx_dim] = dot_pos[idx_dim, idx_pos]
        wavedot[3, 1:-1] = pc.PtoV(power)
        wave = np.concatenate((wave, wavedot), axis=1)
    return wave

def tree_z_line(Xfrom, Xto, *, Zrange, wavelength, power, speed, dt):
    Xfrom = np.asarray(Xfrom)
    Xto = np.asarray(Xto)
    
    dX = Xto - Xfrom
    distance = np.linalg.norm(dX)
    dXn = dX / distance
    times = np.arange(0, distance / speed, dt)
    
    wave = np.zeros((4, len(times) + 2))
    wave[:3, 1:-1] = Xfrom[:, np.newaxis] + dXn[:, np.newaxis] * speed * times[np.newaxis]
    
    wave[2, 1:-1] += Zrange[0] + (Zrange[1] - Zrange[0]) * sawtooth(
            speed * times/wavelength* 2 * np.pi, fraction)
    
    wave[:3, 0] = wave[:3, 1]
    wave[:3, -1] = wave[:3, -2]
    wave[3, 1:-1] = pc.PtoV(power)
    
    assert wave.shape[1] > 2

    return wave
    
    
def tree_p_line(Xfrom, Xto, *, Prange, wavelength, speed, dt):
    Xfrom = np.asarray(Xfrom)
    Xto = np.asarray(Xto)
    
    dX = Xto - Xfrom
    distance = np.linalg.norm(dX)
    dXn = dX / distance
    times = np.arange(0, distance / speed, dt)
    
    wave = np.zeros((4, len(times) + 2))
    wave[:3, 1:-1] = Xfrom[:, np.newaxis] + dXn[:, np.newaxis] * speed * times[np.newaxis]
    
    wave[:3, 0] = wave[:3, 1]
    wave[:3, -1] = wave[:3, -2]
    
    P = Prange[0] + (Prange[1] - Prange[0]) * sawtooth(
            speed * times/wavelength * 2 * np.pi, fraction)
    
    wave[3, 1:-1] = pc.PtoV(P)

    assert wave.shape[1] > 2
    return wave
    
def tree_v_line(Xfrom, Xto, *, v_range, wavelength, power, dt):
    Xfrom = np.asarray(Xfrom)
    Xto = np.asarray(Xto)
    
    dX = Xto - Xfrom
    distance = np.linalg.norm(dX)
    dXn = dX / distance
    
    # raise part
    v_slope_raise = (v_range[1] - v_range[0]) / (fraction * wavelength)
    V0_raise = v_range[0]
    
    v_slope_fall = (v_range[0] - v_range[1]) / ((1 - fraction) * wavelength)
    V0_fall = v_range[1]
    
    
    T_raise = 1 / v_slope_raise * np.log(
            v_slope_raise / V0_raise * fraction * wavelength + 1)
    T_fall = 1 / v_slope_fall * np.log(
            v_slope_fall / V0_fall * (1 - fraction) * wavelength + 1) 
    
    T_wave = T_raise + T_fall
    
    N_wave = int(distance/wavelength)
    
    T_tot = T_wave * N_wave
    
    time = np.arange(0, T_tot, dt)
    
    pos = np.zeros_like(time) * np.nan
    
    
    
    for i in range(N_wave):
        
        Ti = i * T_wave 
        Tm = Ti + T_raise
        Tf = Ti + T_wave
        Xi = i * wavelength
        Xm = Xi + fraction * wavelength
        
        mask = np.logical_and(time >= Ti, time < Tm)
        pos[mask]= V0_raise / v_slope_raise * (
                np.exp(v_slope_raise * (time[mask] - Ti)) - 1) + Xi
        
        #%
        
        mask = np.logical_and(time >= Tm, time < Tf)
        pos[mask]= V0_fall / v_slope_fall * (
                np.exp(v_slope_fall * (time[mask] - Tm)) - 1) + Xm
        
        
    wave = np.zeros((4, len(time) + 2))
    wave[:3, 1:-1] = Xfrom[:, np.newaxis] + dXn[:, np.newaxis] * pos[np.newaxis]
    
    wave[:3, 0] = wave[:3, 1]
    wave[:3, -1] = wave[:3, -2]
    
    wave[3, 1:-1] = pc.PtoV(power)
    assert wave.shape[1] > 2

    return wave

def add_wave_line(wave, wave_line, *, off_speed, dt):
    assert wave.shape[1] < max_points/4
    
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
    

def write_margin(y_lines_spacing):
    line([-cube_width/2 + y_lines_spacing/2, -cube_width/2 + y_lines_spacing/2, 0],
         [-cube_width/2 + y_lines_spacing/2, cube_width/2 - y_lines_spacing/2, 0],
         power=pc.range_P[1],
         speed=50)
# =============================================================================
# 1st type - Calibration
# =============================================================================

y_positions = np.arange(-cube_width/2, cube_width/2,
                        y_lines_spacing) + y_lines_spacing/2
x_range = [-cube_width/2 + y_lines_spacing/2, 
           cube_width/2 - y_lines_spacing/2]

energy_density = np.linspace(energy_density_range[1], 
                              energy_density_range[0], 
                              len(y_positions),
                              endpoint=False)

#1st block - vary P
move_motor(motor_line, 0, motor_step)
speed = pc.range_P[1]/np.max(energy_density)
intensity = energy_density * speed
write_margin(y_lines_spacing)
for idx in range(len(y_positions)):
    line([x_range[0], y_positions[idx], offset_range[0]],
          [x_range[1], y_positions[idx], offset_range[1]],
          power=intensity[idx],
          speed=speed)
    
#2nd block - vary V
move_motor(motor_line, 1, motor_step)
intensity = pc.range_P[1]
speed = intensity/energy_density
write_margin(y_lines_spacing)
for idx in range(len(y_positions)):
    line([x_range[0], y_positions[idx], offset_range[0]],
          [x_range[1], y_positions[idx], offset_range[1]],
          power=intensity,
          speed=speed[idx])

motor_line += 1
# =============================================================================
# 2nd type: dots
# =============================================================================

y_positions = np.arange(-cube_width/2, cube_width/2,
                        y_lines_spacing_dots) + y_lines_spacing_dots/2
x_range = [-cube_width/2 + y_lines_spacing_dots/2, 
           cube_width/2 - y_lines_spacing_dots/2]

# 1st line: Vary times for max power
time = np.exp(np.linspace(
        np.log(times_range_dots[0]), 
        np.log(times_range_dots[1]), 
        len(y_positions))) #ms
intensity = pc.range_P[1]

energy = time * intensity


for idx_spacing, spacing in enumerate(list_spacings_dots):
    move_motor(motor_line, idx_spacing, motor_step)
    write_margin(y_lines_spacing)
    wave = np.zeros((4, 0))
    for idx in range(len(y_positions)):
        wave_line = dots_line([x_range[0], y_positions[idx], offset_range[0]],
                  [x_range[1], y_positions[idx], offset_range[1]],
                  spacing=spacing,
                  exposure_time=time[idx],
                  power=intensity,
                  dt=dt)
        wave = add_wave_line(wave, wave_line,
                             off_speed=off_speed, dt=dt)
    script.waveform(wave, dt)
    
    
motor_line += 1

# 2nd line: vary power

time = times_range_dots[1]
intensity = energy / time
intensity[intensity > pc.range_P[1]] = pc.range_P[1]

for idx_spacing, spacing in enumerate(list_spacings_dots):
    move_motor(motor_line, idx_spacing, motor_step)
    write_margin(y_lines_spacing)
    wave = np.zeros((4, 0))
    for idx in range(len(y_positions)):
        wave_line = dots_line([x_range[0], y_positions[idx], offset_range[0]],
                  [x_range[1], y_positions[idx], offset_range[1]],
                  spacing=spacing,
                  exposure_time=time,
                  power=intensity[idx],
                  dt=dt)
        wave = add_wave_line(wave, wave_line,
                             off_speed=off_speed, dt=dt)
    script.waveform(wave, dt)
        
motor_line += 1

# =============================================================================
# 3rd type: Christmas trees!
# =============================================================================


# 1st block: move z
y_positions = np.arange(-cube_width/2, cube_width/2,
                        y_lines_spacing) + y_lines_spacing/2
x_range = [-cube_width/2 + y_lines_spacing/2, 
           cube_width/2 - y_lines_spacing/2]

energy_density = np.linspace(energy_density_range[1], 
                              energy_density_range[0], 
                              len(y_positions),
                              endpoint=False)

fix_speed = pc.range_P[1]/np.max(energy_density)

#1st block - vary z
move_motor(motor_line, 0, motor_step)
intensity = energy_density * fix_speed
write_margin(y_lines_spacing)
wave = np.zeros((4, 0))
for idx in range(len(y_positions)):
    wave_line = tree_z_line(
            [x_range[0], y_positions[idx], 0],
            [x_range[1], y_positions[idx], 0],
            Zrange=offset_range,
            wavelength=wavelength,
            power=intensity[idx],
            speed=fix_speed,
            dt=dt)
    wave = add_wave_line(wave, wave_line,
                             off_speed=off_speed, dt=dt)
script.waveform(wave, dt)
    
#2nd block - vary P
move_motor(motor_line, 1, motor_step)

zpos = np.linspace(
        offset_range[0],
        offset_range[1],
        len(y_positions),
        endpoint=False
        )

write_margin(y_lines_spacing)
wave = np.zeros((4, 0))
for idx in range(len(y_positions)):
    wave_line = tree_p_line(
            [x_range[0], y_positions[idx], zpos[idx]],
            [x_range[1], y_positions[idx], zpos[idx]],
            Prange=[pc.range_P[1]/2, pc.range_P[1]],
            wavelength=wavelength,
            speed=fix_speed,
            dt=dt)
    wave = add_wave_line(wave, wave_line,
                             off_speed=off_speed, dt=dt)
script.waveform(wave, dt)
#1st block - vary v
move_motor(motor_line, 2, motor_step)

write_margin(y_lines_spacing)
wave = np.zeros((4, 0))
for idx in range(len(y_positions)):
    wave_line = tree_v_line(
            [x_range[0], y_positions[idx], zpos[idx]],
            [x_range[1], y_positions[idx], zpos[idx]],
            v_range=[fix_speed/2, fix_speed*2],
            wavelength=wavelength,
            power=pc.range_P[1],
            dt=dt)
    wave = add_wave_line(wave, wave_line,
                             off_speed=off_speed, dt=dt)
script.waveform(wave, dt)

get_gtext(script._lines, 'piezo', [-50, -250], 100, pc.PtoV(pc.range_P[1]), 50) 
    
script.save(script_fn)
print(script.min_time)