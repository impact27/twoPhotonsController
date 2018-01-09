# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:18:13 2017

@author: quentinpeter
"""
import numpy as np
from GText import get_gtext

powers = np.array([2.76, 3.43])  # mW
speeds = np.array([20, 50, 100, 200])  # umps
z_offsets = np.arange(0, 5.1, .5)  # um
off_speed = 1000

motor_step = 125


text_height = 100


def write_lines_piezzo(lines, yPos, z_offset, off_speed, power, length, speed):
    lines.append("piezzo X{:.2f} Y{:.2f} Z{:.3f} F{:d}".format(
        -50,
        yPos - 50,
        z_offset,
        off_speed))

    lines.append("laser power {:f}".format(power))
    lines.append("piezzo X{:.2f} Y{:.2f} F{:d}".format(
        length - 50,
        yPos - 50,
        speed))
    lines.append("laser power 0")
    return lines
    
def write_lines_motor(lines, motor_X, motor_Y, yPos, z_offset, off_speed, power, 
                      length, speed):  
    lines.append("motor X{:.2f} Y{:.2f} F{:d}".format(
        motor_X - 50,
        motor_Y + yPos - 50,
        off_speed))

    lines.append("laser power {:f}".format(power))
    lines.append("motor X{:.2f} Y{:.2f} F{:d}".format(
        motor_X + length - 50,
        motor_Y + yPos - 50,
        speed))
    return lines

def calibrate(lines, powers, speeds, z_offsets, off_speed, motor_step, motor_origin, piezzo):
    lines.append("laser ON")
    for xpos, power in enumerate(powers):
        motor_X = xpos * motor_step + motor_origin[0]
        line_space = (1 + power / np.max(powers)) / 2 * 100 / len(z_offsets)
    
        for ypos, speed in enumerate(speeds):
            motor_Y = ypos * motor_step + motor_origin[1]
            line_length = (2 + speed / np.max(speeds)) / 3 * 100
            lines.append("motor X{:.2f} Y{:.2f}".format(motor_X, motor_Y))
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
                length = line_length + n / len(z_offsets) * 20 - 20
                yPos = (n + 1) * line_space
            
                if piezzo:
                    write_lines_piezzo(lines, yPos, z_offset, off_speed, power,
                                       length, speed)
                else:
                    write_lines_motor(lines, motor_X, motor_Y, yPos, z_offset, 
                                      off_speed, power, length, speed)
             
                
                lines.append("laser power 0")
                
    return lines   
                

motor_origin = [0, 0]
piezzo = True
text = 'piezzo'
fn = '20180109_cal.txt'

lines = []
calibrate(lines, powers, speeds, z_offsets, off_speed, motor_step, motor_origin, piezzo)     
get_gtext(lines, text, [-50, -200], text_height, np.max(powers), np.min(speeds)) 

motor_origin = [500, 0]
piezzo = False
text = 'motor'

calibrate(lines, powers, speeds, z_offsets, off_speed, motor_step, motor_origin, piezzo)     
get_gtext(lines, text, [450, -200], text_height, np.max(powers), np.min(speeds)) 


         

with open(fn, 'w') as f:
    f.write('\n'.join(lines))
    
    
