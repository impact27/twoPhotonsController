# -*- coding: utf-8 -*-
"""
Created on Tue Jan  9 10:57:04 2018

@author: quentinpeter
"""
letters_dict = {
    'e':[[1, 0, 0],
        [0, 0, 1],
        [0, 2, 1],
        [1, 2, 1],
        [0, 1, 0],
        [.5, 1, 1]],
    'i':[[.5, 0, 0],
        [.5, 2, 1]],
    'm':[[0, 0, 0],
        [0, 2, 1],
        [0.5, 1.5, 1],
        [1, 2, 1],
        [1, 0, 1]],
    'o':[[0, 0, 0],
        [1, 0, 1],
        [1, 2, 1],
        [0, 2, 1],
        [0, 0, 0]],
    'p':[[0, 0, 0],
        [0, 2, 1],
        [1, 2, 1],
        [1, 1, 1],
        [0, 1, 1]],
    'r':[[0, 0, 0],
        [0, 2, 1],
        [1, 2, 1],
        [1, 1, 1],
        [0, 1, 1],
        [.5, 1, 0],
        [1, 0, 1]],
    't':[[.5, 0, 0],
        [.5, 2, 1],
        [0, 2, 0],
        [1, 2, 1]],
    'z':[[0, 2, 0],
        [1, 2, 1],
        [0, 0, 1],
        [1, 0, 1]],
        }



def get_gtext(lines, text, origin, height, power, speed):
    offset = origin.copy()
    current_power = 0
    
    lines.append("laser power 0")
    for char in text.lower():
        lines.append("piezzo X0 Y0 F{:d}".format(1000))
        lines.append("focus motor -20 21 1")
        lines.append("focus piezzo -2 3 1")
        letter = letters_dict[char]
        for position in letter:
            if position[2]!=current_power:
                current_power = position[2]
                lines.append("laser power {:f}".format(power*current_power))
            if current_power == 0:
                cur_speed = 1000
            else:
                cur_speed = speed
            lines.append("motor X{:.2f} Y{:.2f} F{:d}".format(
                    position[0]*height/2 + offset[0],
                    position[1]*height/2 + offset[1],
                    cur_speed))
        offset[0] += height*3/4
    return lines
            