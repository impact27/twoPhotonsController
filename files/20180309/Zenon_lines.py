# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:18:13 2017

@author: quentinpeter
"""
import numpy as np
from script import Script

fn = '20180309_zenon.txt'

write_settings = {
        'power': 2.6943,
        'speed': 400,
        'offset': -0.95}

off_speed = 1500
focus_int = 0.5





script = Script(focus_int=focus_int,
                off_speed=off_speed,
                write_speed=write_settings['speed'],
                write_power=write_settings['power'])

z = write_settings['offset']
script.move_motor([0, 0, 0])
for y in np.arange(-10, 11, 5):
    script.write_lines_piezzo([-25, y, z], [25, y, z])
    

script.save(fn)

    
    
