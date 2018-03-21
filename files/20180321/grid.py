# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:18:13 2017

@author: quentinpeter
"""
import numpy as np
import sys
sys.path.append('../package')
from script import Script

fn = '20180321_grid.txt'

write_large = {
        'power': 4,
        'speed': 400,
        'offset': -.8}
write_small = {
        'power': 2.6943,
        'speed': 400,
        'offset': -0.95}

off_speed = 1500
focus_int = 0.5

length = 10000



script = Script(focus_int=focus_int,
                off_speed=off_speed,
                write_speed=write_small['speed'],
                write_power=write_small['power'])

z = write_small['offset']
script.move_motor([0, 0, 0])
for i, x in enumerate(np.arange(0, 10001, 100)):
    p = i%2
    script.write_line_motor([x, p*length, z], [x, (1-p)*length, z])

script.write_power =  write_large['power'] 
script.write_speed = write_large['speed']
z = write_large['offset']

for i, y in enumerate(np.arange(0, 10001, 100)):
    p = i%2
    script.write_line_motor([p*length, y, z], [(1-p)*length, y, z])


script.save(fn)

    
    
