# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:18:13 2017

@author: quentinpeter
"""
import numpy as np

powers = np.array([2.14, 2.76, 3.43, 4.38])  # mW
speeds = np.arange(20, 201, 20)  # umps
z_offsets = np.arange(-1.8, 2, .2)  # um
off_speed = 1000

motor_step = 125
motor_origin = [0, 0]

lines = []
lines.append("laser ON")
for xpos, power in enumerate(powers):
    line_space = (1 + power / np.max(powers)) / 2 * 100 / len(z_offsets)
    lines.append("motor X{:.2f}".format(xpos * motor_step + motor_origin[0]))

    for ypos, speed in enumerate(speeds):
        line_length = (2 + speed / np.max(speeds)) / 3 * 100
        lines.append(
            "motor Y{:.2f}".format(
                ypos *
                motor_step +
                motor_origin[1]))
        lines.append("piezzo X50 Y50 F{:d}".format(off_speed))
        lines.append("focus motor -20 21 1")
        lines.append("focus piezzo -2 3 1")

        # Write top line
        lines.append("piezzo X-50 Y{:.2f} Z0 F{:d}".format(
            len(z_offsets) * line_space - 50, off_speed))
        lines.append("laser power {:f}".format(np.max(powers)))
        lines.append("piezzo X-50 Y-50 Z0 F{:d}".format(np.min(speeds)))
        lines.append("piezzo X50 Y-50 Z0 F{:d}".format(np.min(speeds)))
        lines.append("laser power 0")

        for n, z_offset in enumerate(z_offsets):
            lines.append("piezzo X-50 Y{:.2f} Z{:.3f} F{:d}".format(
                (n + 1) * line_space - 50,
                z_offset,
                off_speed))

            lines.append("laser power {:f}".format(power))
            lines.append("piezzo X{:.2f} Y{:.2f} F{:d}".format(
                line_length + n / len(z_offsets) * 20 - 70,
                (n + 1) * line_space - 50,
                speed))
            lines.append("laser power 0")

with open('instructions.txt', 'w') as f:
    f.write('\n'.join(lines))
