# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:18:13 2017

@author: quentinpeter
"""
import numpy as np

fn = '20180302_chip.txt'

write_offset = 1.8
write_power = 4
write_speed_piezzo = 400
write_speed = 1000
off_speed = 1500
offsets = np.linspace(-1.7, -2.2, 51)

def write_lines_piezzo(lines, yPos, z_from, z_to, off_speed, power, length, speed):
    lines.append("piezzo X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:d}".format(
        x=-50,
        y=yPos - 50,
        z=z_from,
        f=off_speed))

    lines.append("laser power {:f}".format(power))
    lines.append("piezzo X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:d}".format(
        x=length - 50,
        y=yPos - 50,
        z=z_to,
        f=speed))
    lines.append("laser power 0")
    return lines



lines = ['focusint 0.5']
lines.append("motor X{x:.3f} Y{y:.3f} Z{z:.3f} F{s:.3f}".format(
                x=0, y=0, z=0, s=off_speed))
lines.append("piezzo X{x:.3f} Y{y:.3f} Z{z:.3f} F{s:.3f}".format(
                x=0, y=0, z=0, s=off_speed))
lines.append("laser power {:f}".format(write_power))
lines.append("motor F{s:.3f}".format(s=write_speed))
lines.append("laser ON")
#Write first leg
for x in range(50):
    if x%2 == 0:
        y=1000
    else:
        y=0
    lines.append("motor Y{y:.3f}".format(y=y))
    lines.append("motor X{x:.3f}".format(x=x))
lines.append("laser power 0")


lines.append("motor X{x:.3f} Y{y:.3f} Z{z:.3f} F{s:.3f}".format(
                x=75, y=800, z=0, s=off_speed))
lines.append("piezzoslope")

for i, offset in enumerate(offsets):
    ypos = i / (len(offsets) - 1) * 100
    write_lines_piezzo(lines, ypos, offset, offset, off_speed, write_power, 100, write_speed_piezzo)



lines.append("motor X{x:.3f} Y{y:.3f} Z{z:.3f} F{s:.3f}".format(
                x=75, y=950, z=0, s=off_speed))
lines.append("piezzoslope")
for i, offset in enumerate(offsets):
    ypos = i / (len(offsets) - 1) * 100
    write_lines_piezzo(lines, ypos, offset, offset, off_speed, write_power, 100, write_speed_piezzo)

lines.append("motor X{x:.3f} Y{y:.3f} Z{z:.3f} F{s:.3f}".format(
                x=100, y=750, z=0, s=off_speed))
lines.append("motor F{s:.3f}".format(s=write_speed))
lines.append("laser power {:f}".format(write_power))
for x in range(100, 150):
    if x%2 == 0:
        y=1750
    else:
        y=750
    lines.append("motor Y{y:.3f}".format(y=y))
    lines.append("motor X{x:.3f}".format(x=x))
lines.append("laser power 0")
 
    
    
with open(fn, 'w') as f:
    f.write('\n'.join(lines))
    
    
