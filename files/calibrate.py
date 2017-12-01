# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:18:13 2017

@author: quentinpeter
"""
import numpy as np

powers = np.array([2.14, 2.76, 3.43, 4.38])#mW
speeds = np.arange(20, 201, 20)#umps
z_offsets = np.arange(-3, 4, 1)#um
off_speed = 1000

motor_step = 125
motor_origin = [25000, 15000]

lines = []
lines.append("laser ON")
for xpos, power in enumerate(powers):
    line_space = 5 + power / np.max(powers) * 5
    lines.append("motor X{:.2f}".format(xpos*motor_step + motor_origin [0]))
    
    for ypos, speed in enumerate(speeds):
        line_length = 30 + speed / np.max(speeds) * 50
        lines.append("motor Y{:.2f}".format(ypos*motor_step + motor_origin [1]))
        lines.append("piezzo X50 Y50 F{:d}".format(off_speed))
        lines.append("focus motor -20 21 1")
        lines.append("focus piezzo -2 3 1")
        
        for n, z_offset in enumerate(z_offsets):
            lines.append("piezzo X-50 Y{:.2f} Z{:.2f} F{:d}".format(
                    n * line_space -50,
                    z_offset,
                    off_speed))
            
            lines.append("laser power {:f}".format(power))
            lines.append("piezzo X{:.2f} Y{:.2f} F{:d}".format(
                    line_length + n/len(z_offsets)*20 -50,
                    n * line_space - 50,
                    speed))        
            lines.append("laser power 0")

with open('instructions.txt','w') as f:
    f.write('\n'.join(lines))
    
    
        

        
        
        