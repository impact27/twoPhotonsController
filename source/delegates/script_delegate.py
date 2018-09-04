# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 10:33:07 2017

@author: quentinpeter
"""
import tifffile
import numpy as np
import re
import matplotlib
cmap = matplotlib.cm.get_cmap('viridis')
from PyQt5 import QtCore
from matplotlib import collections as mc
import sys


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
        try:
            self._parser.parse(self._filename)
        except BaseException as e:
            print(e)


class Parser():

    def __init__(self):
        super().__init__()
        self.file = None

    def parse(self, filename):
        with open(filename) as f:
            self.file = f
            fun = 0
            while fun is not None:
                line = self.file.readline()
                fun, args = self.readline(line)
                if fun is None:
                    break
                fun(*args)
                # try:
                    # fun(*args)
                # except BaseException:
                #     print('')
                #     print("Error while parsing line:")
                #     print(line)
                #     print(sys.exc_info())
                #     print('')
                #     raise
            self.file = None

    def readline(self, line):
        if line == '':
            return None, None
        line = line.strip()
        line = line.split(' ')
        command = line[0]
        args = line[1:]
        if command.lower() in ['laser', 'focus', 'camera', 'focusint', 'begin']:
            pass
        elif command.lower() in ['piezoslope', 'piezoreset']:
            args = tuple()
        elif command.lower() in ['piezo', 'motor']:
            args = self.read_move_args(args)
        else:
            raise RuntimeError(f"Unknown command {command}")

        fun = getattr(self, command)
        return fun, args

    def focusint(self, args):
        pass

    def laser(self, *args):
        if len(args) == 0:
            print("No args for laser")
        if args[0].lower() == "on":
            self.laser_state(True)
        elif args[0].lower() == "off":
            self.laser_state(False)
        elif args[0].lower() == "power":
            self.laser_power(float(args[1]))

    def read_move_args(self, args):

        args_dic = self.single_letter_arg(*args)

        pos = np.ones(3) * np.nan
        speed = np.nan
        intensity = np.nan

        if 'X' in args_dic:
            pos[0] = args_dic['X']
        if 'Y' in args_dic:
            pos[1] = args_dic['Y']
        if 'Z' in args_dic:
            pos[2] = args_dic['Z']
        if 'E' in args_dic:
            speed = args_dic['E']
        if 'F' in args_dic:
            intensity = args_dic['F']
        return pos, speed, intensity

    def camera(self, subcommand, arg):
        if subcommand.lower() == 'grab':
            self.camera_grab(arg)
        elif subcommand.lower() == 'exposure':
            self.camera_exposure(float(arg))

    def camera_grab(self, fname):
        pass

    def camera_exposure(self, exp_time):
        pass

    def focus(self, stage, start_offset, stop_offset, step):
        pass

    def motor(self, pos, speed, intensity):
        pass

    def piezo(self, pos, speed, intensity):
        pass

    def laser_state(self, state):
        pass

    def laser_power(self, power):
        pass

    def piezoslope(self):
        pass

    def piezoreset(self):
        pass

    def single_letter_arg(self, *args):
        ret = {}
        pos_re = '([A-Z])([-\.\d]+)'
        for arg in args:
            for found in re.findall(pos_re, arg):
                ret[found[0]] = float(found[1])
        return ret

    def BEGIN(self, *args):
        assert args[0].lower() == 'waveform'

        args_dic = self.single_letter_arg(*args[1:])

        time_step = args_dic['R']
        Npos = args_dic['N']
        line = self.file.readline()
        data = {}
        while line != 'END\n' and line != '':
            line = line.split(' ')
            data[line[0]] = np.asarray(line[1:], float)
            line = self.file.readline()
        if line != 'END\n':
            raise RuntimeError('Can\'t find end')
        if 'E' in data:
            indices = ['X', 'Y', 'Z', 'E']
        else:
            indices = ['X', 'Y', 'Z']
        X = np.asarray([data[idx] for idx in indices])

        assert np.shape(X)[1] == Npos
        self.run_waveform(time_step, X)

    def run_waveform(self, time_step, X):
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

        self.recording_macro = False
        
    class macro():
        def __init__(self, compatible):
            self._compatible = compatible
            
        def __call__(self, f):
            if self._compatible:
                def ret(*args):
                    args[0].start_macro()
                    f(*args)
            else:
                def ret(*args):
                    args[0].end_macro()
                    f(*args)
            return ret


    def start_macro(self):
        if not self.recording_macro:
            self.recording_macro = True
            self.piezo_delegate.macro_begin('nextsteps')

    def end_macro(self):
        if not self.recording_macro:
            return
        self.recording_macro = False
        self.piezo_delegate.macro_end()
        self.piezo_delegate.macro_start('nextsteps', wait=True)
        self.piezo_delegate.macro_delete('nextsteps')

    def parse(self, filename):
        self.lockid = self.md.lock()
        if self.lockid is None:
            raise RuntimeError("Can't lock motion")
        try:
            super().parse(filename)
            self.end_macro()
        except:
            self.laser_delegate.set_intensity(0)
            raise
        self.md.unlock()
        self.lockid = None

    @macro(False)
    def camera_grab(self, fname):
        self.camera_delegate.extShutter(True)
        im = self.camera_delegate.get_image()
        tifffile.imsave(fname, im)

    @macro(False)
    def camera_exposure(self, exp_time):
        self.camera_delegate.set_exposure_time(exp_time)

    @macro(False)
    def focus(self, stage, start_offset, stop_offset, step):
        start_offset, stop_offset, step = float(
            start_offset), float(stop_offset), float(step)
        if stage.lower() == 'piezo':
            self.focus_delegate.focus(start_offset=start_offset,
                                      stop_offset=stop_offset,
                                      step=step,
                                      stage=self.md.piezo,
                                      Nloops=2, wait=True,
                                      checkid=self.lockid)
        elif stage.lower() == 'motor':
            self.focus_delegate.focus(start_offset=start_offset,
                                      stop_offset=stop_offset,
                                      step=step,
                                      stage=self.md.motor,
                                      Nloops=1, wait=True,
                                      checkid=self.lockid)
        elif stage.lower() == 'both':
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
            raise RuntimeError(f"Don't know {stage}")

        self.focus_intensity = self.laser_delegate.get_intensity()

    @macro(False)
    def piezoslope(self):
        self.coordinates_delegate.piezo_plane(checkid=self.lockid, wait=True)

    @macro(False)
    def piezoreset(self):
        self.piezo_delegate.reset(checkid=self.lockid, wait=True)

    @macro(False)
    def focusint(self, args):
        self.focus_intensity = float(args[0])

    @macro(False)
    def motor(self, pos, speed, intensity):
        if not np.isnan(intensity):
            self.laser_power(intensity)
        self.motor_delegate.goto_position(pos, speed=speed, wait=True,
                                          checkid=self.lockid)

    @macro(True)
    def piezo(self, pos, speed, intensity):
        if not np.isnan(intensity):
            self.laser_power(intensity)
        self.piezo_delegate.goto_position(
            pos, speed=speed, wait=False,
            checkid=self.lockid, useLastPos=True)

    @macro(True)
    def laser_power(self, power):
        if power > 0:
            self.camera_delegate.extShutter(False)
        self.laser_delegate.set_intensity(power)

    @macro(False)
    def run_waveform(self, time_step, X):
        self.piezo_delegate.run_waveform(time_step, X.T)


class Draw_Parser(Parser):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.writing = False
        self.motor_position = np.zeros(3)
        self.piezo_position = np.zeros(3)
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

    def piezo(self, pos, speed, intensity):
        if not np.isnan(intensity):
            self.laser_power(intensity)
        piezo_to = self.move(self.piezo_position, pos)
        self.plotto(piezo_to + self.motor_position)
        self.piezo_position = piezo_to

    def motor(self, pos, speed, intensity):
        if not np.isnan(intensity):
            self.laser_power(intensity)
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

    def run_waveform(self, time_step, X):
        for pos in X.T:
            I = np.nan
            if len(pos) > 3:
                I = pos[3]
                pos = pos[:3]
            self.piezo(pos, 3000, I)
