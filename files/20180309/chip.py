# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:18:13 2017

@author: quentinpeter
"""
import numpy as np
from script import Script

fn = '20180309_chip.txt'

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





script = Script(focus_int=focus_int,
                off_speed=off_speed,
                write_speed=write_large['speed'],
                write_power=write_large['power'])

for x_origin in np.arange(10)*1000:
    
    origin = [x_origin, 0]
    
    script.write_power =  write_large['power'] 
    script.write_speed = write_large['speed']
    #Write legs
    z = write_large['offset']
    
    Ymotor_start = origin[1]
    for Xmotor in origin[0] + np.arange(2)*100:
        
        for Ymotor in np.arange(0, 95*15, 95) + Ymotor_start:
        
            script.move_motor([Xmotor, Ymotor, 20])
            
            for i, x in enumerate(np.arange(-25, 25, 1)):
                parity = 2*(i%2-0.5)
                script.write_lines_piezzo([x, parity*-49, z], [x, parity*49, z])
                
        Ymotor_start = Ymotor_start + 95*10
            
    #write lines
    script.write_power =  write_small['power'] 
    script.write_speed = write_small['speed']
    z = write_small['offset']
    Xmotor = origin[0] + 50
    Ymotor_start = origin[1] + 95*10
    for Ymotor in np.arange(0, 95*5, 2*95) + Ymotor_start:
        
        script.move_motor([Xmotor, Ymotor, 20])
        
        for i, y in enumerate(np.linspace(-48, 47, 20)):
            parity = 2*(i%2-0.5)
            script.write_lines_piezzo([parity*-49, y, z], [parity*49, y, z])
    

script.save(fn)

    
    
