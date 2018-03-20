# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 10:33:07 2017

@author: quentinpeter
"""
import tifffile
import numpy as np
import re
import matplotlib
import sys
cmap = matplotlib.cm.get_cmap('viridis')
from PyQt5 import QtCore
from matplotlib import collections  as mc


class Script_delegate():
    def __init__(self, app_delegate):
        super().__init__()
        self.app_delegate = app_delegate
        self.init_threads()

    def init_threads(self):
        self._execute_thread = Parse_thread(Execute_Parser(self.app_delegate))

        self._draw_thread = Parse_thread(
            Draw_Parser(self.app_delegate.canvas_delegate))

    def execute(self, filename):
        self._execute_thread.set_filename(filename)
        self._execute_thread.start()

    def draw(self, filename):
        self._draw_thread.set_filename(filename)
        self._draw_thread.start()

    def ESTOP(self):
        self._execute_thread.terminate()
        self._draw_thread.terminate()
        self.init_threads()


class Parse_thread(QtCore.QThread):
    def __init__(self, parser):
        super().__init__()
        self._filename = ''
        self._parser = parser

    def set_filename(self, filename):
        self._filename = filename

    def run(self):
        #        self._parser.parse(self._filename)
        try:
            self._parser.parse(self._filename)
        except BaseException:
            pass


class Parser():

    def __init__(self):
        super().__init__()

    def parse(self, filename):
        with open(filename) as f:
            for line in f.readlines():
                try:
                    self.readline(line)
                except BaseException:
                    print('')
                    print("Error while parsing line:")
                    print(line)
                    print(sys.exc_info())
                    print('')
                    raise

    def readline(self, line):
        line = line.strip()
        line = line.split(' ')
        command = line[0]
        arg = line[1:]
        if command.lower() in ['laser', 'focus', 'camera', 'focusint']:
            getattr(self, command)(arg)
        elif command.lower() in ['piezoslope', 'piezoreset']:
            getattr(self, command)()
        elif command.lower() in ['piezo', 'motor']:
            getattr(self, command)(*self.read_move_args(arg))

    def focusint(self, args):
        pass

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
        pos = np.ones(3) * np.nan
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

    def piezo(self, pos, speed):
        pass

    def laser_state(self, state):
        pass

    def laser_power(self, power):
        pass

    def piezoslope(self):
        pass
    
    def piezoreset(self):
        pass


class Execute_Parser(Parser):
    def __init__(self, app_delegate):
        super().__init__()
        self.camera_delegate = app_delegate.camera_delegate
        self.md = app_delegate.movement_delegate
        self.piezo_delegate = app_delegate.movement_delegate.piezo
        self.motor_delegate = app_delegate.movement_delegate.motor
        self.laser_delegate = app_delegate.laser_delegate
        self.focus_delegate = app_delegate.focus_delegate
        self.coordinates_delegate = app_delegate.coordinates_delegate
        self.lockid = None

    def parse(self, filename):
        self.lockid = self.md.lock()
        if self.lockid is None:
            raise RuntimeError("Can't lock motion")
        super().parse(filename)
        self.md.unlock()
        self.lockid = None

    def camera_grab(self, fname):
        self.camera_delegate.extShutter(True)
        im = self.camera_delegate.get_image()
        tifffile.imsave(fname, im)

    def camera_exposure(self, exp_time):
        self.camera_delegate.set_exposure_time(exp_time)

    def focus(self, args):
        piezo, start_offset, stop_offset, step = args
        start_offset, stop_offset, step = float(
            start_offset), float(stop_offset), float(step)
        if piezo.lower() == 'piezo':
            self.focus_delegate.focus(start_offset=start_offset,
                                      stop_offset=stop_offset,
                                      step=step,
                                      stage=self.md.piezo,
                                      Nloops=2, wait=True,
                                      checkid=self.lockid)
        elif piezo.lower() == 'motor':
            self.focus_delegate.focus(start_offset=start_offset,
                                      stop_offset=stop_offset,
                                      step=step,
                                      stage=self.md.motor,
                                      Nloops=1, wait=True,
                                      checkid=self.lockid)
        elif piezo.lower() == 'both':
            self.focus_delegate.focus(start_offset=start_offset,
                                      stop_offset=stop_offset, 
                                      step=step,
                                      stage=self.md.motor,
                                      Nloops=1, wait=True,
                                      checkid=self.lockid)
            self.focus_delegate.focus(start_offset=-2,
                                      stop_offset=2,
                                      step=1,
                                      stage=self.md.piezo,
                                      Nloops=2, wait=True,
                                      checkid=self.lockid)
        else:
            self.md.unlock()
            raise RuntimeError(f"Don't know {piezo}")

        self.focus_intensity = self.laser_delegate.get_intensity()

    def piezoslope(self):
        self.coordinates_delegate.piezo_plane(checkid=self.lockid, wait=True)
        
    def piezoreset(self):
        self.piezo_delegate.reset(checkid=self.lockid, wait=True)
        
    def focusint(self, args):
        self.focus_intensity = float(args[0])

    def motor(self, pos, speed):
        self.motor_delegate.goto_position(pos, speed=speed, wait=True,
                                          checkid=self.lockid)

    def piezo(self, pos, speed):
        self.piezo_delegate.goto_position(pos, speed=speed, wait=True,
                                           checkid=self.lockid)

    def laser_state(self, state):
        if state:
            self.camera_delegate.extShutter(False)
        self.laser_delegate.switch(state)

    def laser_power(self, power):
        if power > 0:
            self.camera_delegate.extShutter(False)
        self.laser_delegate.set_intensity(power)


class Draw_Parser(Parser):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.writing = False
        self.motor_position = np.zeros(3) * np.nan
        self.piezo_position = np.zeros(3) * np.nan
        self.color = cmap(0)
        self.colors = []
        self.lines = []

    def parse(self, filename):
        self.canvas.clear()
        try:
            super().parse(filename)
        except BaseException as e:
            print(e)
            raise
        lc = mc.LineCollection(self.lines, colors=self.colors, linewidths=2)
        self.canvas._axes.add_collection(lc)
        self.canvas._axes.axis('equal')

        self.canvas.draw()
        self.colors = []
        self.lines = []

    def plotto(self, pos):
        if self.writing:
            start = self.motor_position + self.piezo_position
            
            self.lines.append([start[:2], pos[:2]])
            self.colors.append(self.color)

    def piezo(self, pos, speed):
        piezo_to = self.move(self.piezo_position, pos)
        self.plotto(piezo_to + self.motor_position)
        self.piezo_position = piezo_to

    def motor(self, pos, speed):
        motor_to = self.move(self.motor_position, pos)
        self.plotto(motor_to + self.piezo_position)
        self.motor_position = motor_to
        

    def move(self, start_position, pos):
        pos[np.isnan(pos)] = start_position[np.isnan(pos)]
        return pos

    def laser_state(self, state):
        self.writing = state

    def laser_power(self, power):
        self.color = cmap(power / 10)
        
    def piezoreset(self):
        self.piezo_position = np.zeros(3)
