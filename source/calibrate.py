# -*- coding: utf-8 -*-
"""
Created on Thu Nov  2 15:18:13 2017

@author: quentinpeter
"""
import numpy as np
import re
from matplotlib.pyplot import figure, plot
import matplotlib.pyplot as plt
import matplotlib
cmap=matplotlib.cm.get_cmap('viridis')

class Parser():
    
    def __init__(self):
        self.writing = False
        self.motor_position = np.zeros(3)
        self.piezzo_position = np.zeros(3)
        figure()
        plt.axis("equal")
        
    def pprint(self, line):
        print(line)
        line = line.split(' ')
        command = line[0]
        arg = line[1:]
        getattr(self, command)(arg)
        
    def laser(self, args):
        if len(args) == 0:
            print("No args for laser")
        if args[0].upper() == "ON":
            self.writing = True
        elif args[0].upper() == "OFF":
            self.writing = False
        elif args[0] == "power":
            self.color = cmap(float(args[1])/100)
            
    def focus(self, args):
        pass
    
    def motor(self, args):
        motor_to = self.move(self.motor_position, args)
        self.plotto(motor_to + self.piezzo_position)
        self.motor_position = motor_to
        
    def piezzo(self, args):
        piezzo_to = self.move(self.piezzo_position, args)
        self.plotto(piezzo_to + self.motor_position)
        self.piezzo_position = piezzo_to
        
    def move(self, start_position, args):
        pos_re = '([XYZ])([-\.\d]+)'
        pos = np.ones(3)*np.nan
        for arg in args:
            for found in re.findall(pos_re, arg):
                if found[0] == 'X':
                    pos[0] = float(found[1])
                elif found[0] == 'Y':
                    pos[1] = float(found[1])
                elif found[0] == 'Z':
                    pos[2] = float(found[1])
        
        pos[np.isnan(pos)] = start_position[np.isnan(pos)]
        
        return pos
        
    def plotto(self, pos):
        if self.writing:
            start = self.motor_position + self.piezzo_position
            plot([pos[0], start[0]], 
                 [pos[1], start[1]],
                 c=self.color)
        
        
        
parser = Parser()

powers = np.arange(40, 101, 10)#mW
speeds = np.arange(20, 201, 20)#umph
z_offsets = np.arange(-3, 0.1, .5)#um

motor_step = 125
motor_origin = [0, 0]

for xpos, power in enumerate(powers):
    line_space = 5 + power / np.max(powers) * 5
    parser.pprint("laser power {:d}".format(power))
    parser.pprint("motor X{:.2f}".format(xpos*motor_step + motor_origin [0]))
    
    for ypos, speed in enumerate(speeds):
        line_length = 30 + speed / np.max(speeds) * 50
        parser.pprint("motor Y{:.2f}".format(ypos*motor_step + motor_origin [1]))
        parser.pprint("piezzo X50 Y50")
        parser.pprint("focus piezzo -20 20")
        
        for n, z_offset in enumerate(z_offsets):
            parser.pprint("piezzo X0 Y{:.2f} Z{:.2f}".format(n * line_space, z_offset))
            parser.pprint("laser ON")
            parser.pprint("piezzo X{:.2f} Y{:.2f}".format(line_length + n/len(z_offsets)*20, n * line_space))
            parser.pprint("laser OFF")
        
        
        
        