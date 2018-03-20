# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:18:13 2017

@author: quentinpeter
"""
import numpy as np
from GText import get_gtext

powers = np.exp(np.linspace(np.log(1.95), np.log(4), 21))  # V
write_power = 468
speeds = np.array([50, 100, 200, 400, 800])  # umps
z_offsets = np.arange(0, 5.1, .5)  # um
fn = '20180226_slopes.txt'

off_speed = 1000

motor_step = 125


text_height = 100


def write_lines_piezo(lines, yPos, z_from, z_to, off_speed, power, length, speed):
    lines.append("piezo X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:d}".format(
        x=-50,
        y=yPos - 50,
        z=z_from,
        f=off_speed))

    lines.append("laser power {:f}".format(power))
    lines.append("piezo X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:d}".format(
        x=length - 50,
        y=yPos - 50,
        z=z_to,
        f=speed))
    return lines
    


def calibrate(lines, powers, speeds, z_offsets, off_speed, motor_step, motor_origin, piezo):
    lines.append("laser ON")
    
    for xpos, speed in enumerate(speeds):
        motor_X = xpos * motor_step + motor_origin[0]
        lines.append("motor X{:.2f} Y{:.2f} Z20".format(
                motor_X, motor_origin[1]))
        lines.append("focus motor 0 -41 -1")
        lines.append("piezoslope")
        # Write top line
        lines.append("piezo X-50 Y-50 Z0 F{:d}".format(off_speed))
        
        lines.append("laser power {:f}".format(write_power))
        lines.append("piezo X-50 Y50 Z0 F{:d}".format(np.min(speeds)))
        lines.append("laser power 0")
        
        
        
        for ypos, power in enumerate(powers):
            length = 100
            ypos = ypos * 100 / (len(powers) - 1)
            
            write_lines_piezo(lines, ypos, 0, -3, off_speed, power,
                                   length, speed)
         
            
            lines.append("laser power 0")
                
    return lines   
                

motor_origin = [0, 0]
piezo = True
text = 'piezo'


lines = ['focusint 0.5']
calibrate(lines, powers, speeds, z_offsets, off_speed, motor_step, motor_origin, piezo)     
get_gtext(lines, text, [-50, -200], text_height, np.max(powers), np.min(speeds)) 
         

with open(fn, 'w') as f:
    f.write('\n'.join(lines))
    
    
