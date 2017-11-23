# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 10:33:07 2017

@author: quentinpeter
"""
import tifffile
import numpy as np
import re
import matplotlib
cmap=matplotlib.cm.get_cmap('viridis')
from PyQt5 import QtCore

class Script_delegate():
    def __init__(self, app_delegate):
        super().__init__()

        self._execute_thread = Parse_thread(Execute_Parser(app_delegate))
        
        self._draw_thread = Parse_thread(
                Draw_Parser(app_delegate.canvas_delegate._canvas))
    
    def execute(self, filename):
        self._execute_thread.set_filename(filename)
        self._execute_thread.start()
        
    
    def draw(self, filename):
        self._draw_thread.set_filename(filename)
        self._draw_thread.start()
        
    def ESTOP(self):
        self._execute_thread.terminate()
        self._execute_thread.terminate()
        
class Parse_thread(QtCore.QThread):
    def __init__(self, parser):
        super().__init__()
        self._filename = ''
        self._parser = parser
        
    def set_filename(self, filename):
        self._filename = filename
        
    def run(self):
        try:
            self._parser.parse(self._filename)
        except:
            print("Error while parsing")

class Parser():
    
    def __init__(self):
        super().__init__()
        
    def parse(self, filename):
        with open(filename) as f:
            for line in f.readlines():
                self.readline(line)
        
    def readline(self, line):
        line = line.strip()
        line = line.split(' ')
        command = line[0]
        arg = line[1:]
        if command.lower() in ['laser', 'focus', 'camera']:
            getattr(self, command)(arg)
        elif command.lower() in ['piezzo', 'motor']:
            getattr(self, command)(*self.read_move_args(arg))
            
    def laser(self, args):
        if len(args) == 0:
            print("No args for laser")
        if args[0].lower() == "on":
            self.laser_state(True)
        elif args[0].lower() == "off":
            self.laser_state(False)
        elif args[0].lower() == "power":
            self.laser_power(float(args[1]))
            
    def read_move_args(self, args):
        pos_re = '([XYZF])([-\.\d]+)'
        pos = np.ones(3)*np.nan
        speed = np.nan
        for arg in args:
            for found in re.findall(pos_re, arg):
                if found[0] == 'X':
                    pos[0] = float(found[1])
                elif found[0] == 'Y':
                    pos[1] = float(found[1])
                elif found[0] == 'Z':
                    pos[2] = float(found[1])
                elif found[0] == 'F':
                    speed = float(found[1])
        return pos, speed
    
    def camera(self, args):
        if len(args) != 2:
            raise RuntimeError(f"{args} not understood")
        subcommand, arg = args
        
        if subcommand.lower() == 'grab':
            self.camera_grab(arg)
        elif subcommand.lower() == 'exposure':
            self.camera_exposure(float(arg))
    
    def camera_grab(self, fname):
        pass
    
    def camera_exposure(self, exp_time):
        pass
    
    def focus(self, args):
        pass
    
    def motor(self, pos, speed):
        pass
        
    def piezzo(self, pos, speed):
        pass
    
    def laser_state(self, state):
        pass
        
    def laser_power(self, power):
        pass
    
    
        

            
class Execute_Parser(Parser):
    def __init__(self, app_delegate):
        super().__init__()
        self.camera_delegate = app_delegate.camera_delegate
        self.md = app_delegate.mouvment_delegate
        self.piezzo_delegate = app_delegate.mouvment_delegate.piezzo
        self.motor_delegate = app_delegate.mouvment_delegate.motor
        self.laser_delegate = app_delegate.laser_delegate
        self.focus_delegate = app_delegate.focus_delegate
        self.lockid = None
     
    def parse(self, filename):
        self.lockid = self.md.lock()
        if self.lockid is None:
            raise RuntimeError("Can't lock motion")
        super().parse(filename)
        self.md.unlock()
        self.lockid = None
                
    def camera_grab(self, fname):
        im = self.camera_delegate.get_image()
        tifffile.imsave(fname, im)
    
    def camera_exposure(self, exp_time):
        self.camera_delegate.set_exposure_time(exp_time)
    
    def focus(self, args):
        piezzo, back, forth, step = args
        back, forth, step = float(back), float(forth), float(step)
        if piezzo.lower() == 'piezzo':
            self.focus_delegate.focus(back, forth, step, 
                                      Nloops=2, piezzo=True, wait=True,
                                      checkid=self.lockid)
        elif piezzo.lower() == 'motor':
            self.focus_delegate.focus(back, forth, step, 
                                      Nloops=1, piezzo=False, wait=True,
                                      checkid=self.lockid)
        elif piezzo.lower() == 'both':
            self.focus_delegate.focus(back, forth, step, 
                                      Nloops=1, piezzo=False, wait=True,
                                      checkid=self.lockid)
            self.focus_delegate.focus(-2, 2, 1, 
                                      Nloops=2, piezzo=True, wait=True,
                                      checkid=self.lockid)
        else:
            raise RuntimeError(f"Don't know {piezzo}")
            
        
    
    def motor(self, pos, speed):
        self.motor_delegate.goto_position(pos, speed=speed, wait=True,
                                          checkid=self.lockid)
        
    def piezzo(self, pos, speed):
        self.piezzo_delegate.goto_position(pos, speed=speed, wait=True,
                                          checkid=self.lockid)
    
    def laser_state(self, state):
        self.laser_delegate.switch(state)
        
    def laser_power(self, power):
        self.laser_delegate.set_intensity(power)

class Draw_Parser(Parser):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.writing = False
        self.motor_position = np.zeros(3)
        self.piezzo_position = np.zeros(3)
        
    def parse(self, filename):
        self.canvas.clear()
        super().parse(filename)
        self.canvas.draw()
    
    def plotto(self, pos):
        if self.writing:
            start = self.motor_position + self.piezzo_position
            self.canvas.plot([pos[0], start[0]], 
                             [pos[1], start[1]],
                             c=self.color,
                             axis='equal', draw=False)
            
    def piezzo(self, pos, speed):
        piezzo_to = self.move(self.piezzo_position, pos)
        self.plotto(piezzo_to + self.motor_position)
        self.piezzo_position = piezzo_to
    
    def motor(self, pos, speed):
        motor_to = self.move(self.motor_position, pos)
        self.plotto(motor_to + self.piezzo_position)
        self.motor_position = motor_to
    
    def move(self, start_position, pos):
        pos[np.isnan(pos)] = start_position[np.isnan(pos)]
        return pos
    
    def laser_state(self, state):
        self.writing = state
    
    def laser_power(self, power):
        self.color = cmap(power/100)