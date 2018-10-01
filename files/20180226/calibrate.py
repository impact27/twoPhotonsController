# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:18:13 2017

@author: quentinpeter
"""
import numpy as np
from GText import get_gtext

power = 1.7
speeds = np.array([100, 200, 400, 800])  # umps
z_offsets = np.arange(0, -3, -.02)  # um
fn = '20180226_fine_offset.txt'
off_speed = 1000
text_power = 4.5

motor_step = 125
text_height = 100
line_space = 5


def write_lines_piezo(lines, yPos, z_offset, off_speed, power, length, speed):
    lines.append("piezo X{x:.2f} Y{y:.2f} Z{z:.3f} F{f:d}".format(
        x=-50,
        y=yPos - 50,
        z=z_offset,
        f=off_speed))

    lines.append("laser power {:f}".format(power))
    lines.append("piezo X{x:.2f} Y{y:.2f} F{f:d}".format(
        x=length - 7 - 50,
        y=yPos - 50,
        f=speed))
    lines.append("piezo X{x:.2f} Y{y:.2f} F{f:d}".format(
        x=length - 2 - 50,
        y=yPos - 50,
        f=speed))
    lines.append("piezo X{x:.2f} Y{y:.2f} F{f:d}".format(
        x=length - 50,
        y=yPos - 50,
        f=speed))
    lines.append("laser power 0")
    return lines


def write_lines_motor(lines, motor_X, motor_Y, yPos, z_offset, off_speed, power,
                      length, speed):
    lines.append("motor X{x:.2f} Y{y:.2f} Z{z:.2f} F{f:d}".format(
        x=motor_X - 50,
        y=motor_Y + yPos - 50,
        z=z_offset,
        f=off_speed))

    lines.append("laser power {:f}".format(power))
    lines.append("motor X{x:.2f} Y{y:.2f} F{f:d}".format(
        x=motor_X + length - 7 - 50,
        y=motor_Y + yPos - 50,
        f=speed))
    lines.append("motor X{x:.2f} Y{y:.2f} F{f:d}".format(
        x=motor_X + length - 2 - 50,
        y=motor_Y + yPos - 50,
        f=speed))
    lines.append("motor X{x:.2f} Y{y:.2f} F{f:d}".format(
        x=motor_X + length - 50,
        y=motor_Y + yPos - 50,
        f=speed))
    lines.append("laser power 0")
    return lines


def calibrate(lines, power, speeds, z_offsets, off_speed,
              motor_step, motor_origin, piezo):
    lines.append("laser ON")
    for xpos, speed in enumerate(speeds):
        motor_X = xpos * motor_step + motor_origin[0]

        for ypos, z_offset in enumerate(z_offsets):
            motor_Y = ypos * line_space + motor_origin[1]
            length = 100
            if ypos == 0:
                lines.append("motor X{X:.2f} Y{Y:.2f} Z20 F{speed:f}".format(
                    X=motor_X, Y=motor_Y, speed=off_speed))
                lines.append("piezo X50 Y50 Z0 F{:d}".format(off_speed))
                lines.append("focus motor 0 -41 -1")
            lines.append("motor X{X:.2f} Y{Y:.2f} Z0 F{speed:f}".format(
                X=motor_X, Y=motor_Y, speed=off_speed))
            lines.append("focus piezo 2 -2.1 -1")

            if piezo:
                write_lines_piezo(lines, 0, z_offset, off_speed, power,
                                  length, speed)
            else:
                write_lines_motor(lines, motor_X, motor_Y, 0, z_offset,
                                  off_speed, power, length, speed)

    return lines


motor_origin = [0, 0]
piezo = True
text = 'piezo'


lines = ['focusint 0.5']
calibrate(
    lines,
    power,
    speeds,
    z_offsets,
    off_speed,
    motor_step,
    motor_origin,
    piezo)
get_gtext(lines, text, [-50, -200], text_height, text_power, 100)

#motor_origin = [600, 0]
#piezo = False
#text = 'motor'
#
#calibrate(lines, power, speeds, z_offsets, off_speed, motor_step, motor_origin, piezo)
#get_gtext(lines, text, [450, -200], text_height, text_power, 100)


with open(fn, 'w') as f:
    f.write('\n'.join(lines))
