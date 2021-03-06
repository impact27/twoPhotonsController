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
import time
import os

from errors import FocusError, ParseError, MotionError, ScriptError, logError

class Script_delegate(QtCore.QObject):
    pause_status = QtCore.pyqtSignal(bool)

    def __init__(self, app_delegate):
        super().__init__()
        self.app_delegate = app_delegate
        self.init_threads()

    def init_threads(self):
        self._execute_thread = Parse_thread(
                Execute_Parser(self.app_delegate),
                self.app_delegate.error)
        self._execute_thread._parser.pause_status.connect(self.pause_status)
        self._draw_thread = Parse_thread(
            Draw_Parser(self.app_delegate.canvas_delegate),
            self.app_delegate.error)

    def execute(self, filename):
        if self._execute_thread.isRunning():
            self.app_delegate.error.emit("Script already running!")
            return
        self._execute_thread.set_filename(filename)
        self._execute_thread.start()

    def execute_pause_resume(self):
        return self._execute_thread._parser.pause_resume()

    def execute_stop(self):
        self._execute_thread._parser.stop()

    def draw(self, filename):
        self._draw_thread.set_filename(filename)
        self._draw_thread.start()

    def ESTOP(self):
        self._execute_thread.terminate()
        self._draw_thread.terminate()
        self.init_threads()


class Parse_thread(QtCore.QThread):
    def __init__(self, parser, error):
        super().__init__()
        self._filename = ''
        self._parser = parser
        self.error = error

    def set_filename(self, filename):
        self._filename = filename

    def run(self):
        try:
            self._parser.parse(self._filename)
        except FileNotFoundError:
            print("Can't open", self._filename)
            self.error.emit(f"Can't find {self._filename}")
        except (ScriptError, ParseError) as e:
            logError()
            self.error.emit(f"Error: {e}")
        except BaseException as e:
            print("Parse failed")
            print(e)
            raise


class Parser(QtCore.QObject):

    def __init__(self):
        super().__init__()
        self.file = None
        # To add a next line
        self._next_line = None
        self._prev_line = None
        self._running = False
        self._wavedata = None

    def isRunning(self):
        return self._running

    def yield_line(self):
        fun = 0
        self.line_nbr = 0
        while fun is not None:
            fun, args = self.readline()
            if fun is None:
                return
            else:
                yield fun, args
                self.line_nbr += 1

    def parse(self, filename):
        with open(filename) as f:
            self.file = f
            self._running = True
            for (fun, args) in self.yield_line():
                self.parse_line(fun, args)
            self.file = None
            self._running = False

    def parse_line(self, fun, args):
        try:
            fun(*args)
        except BaseException as e:
            print("\nError while parsing line:")
            print(self.line_nbr, ':', fun.__name__, *args)
            print(e, '/n')
            raise

    def readline(self):
        if self._next_line is not None:
            ret = self._next_line
            self._next_line = None
            return ret
        line = self.file.readline()
        if line == '':
            return None, None
        line = line.strip()
        line = line.split(' ')
        command = line[0]
        args = line[1:]
        if command.lower() in ['laser', 'focus', 'savemeasure',
                               'camera', 'focusint', 'begin']:
            pass
        elif command.lower() in ['piezoslope', 'piezoreset']:
            args = tuple()
        elif command.lower() in ['piezo', 'motor']:
            args = self.read_move_args(args)
        else:
            raise ParseError(f"Unknown command {command}")

        fun = getattr(self, command)
        self._prev_line = fun, args
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
        if 'F' in args_dic:
            speed = args_dic['F']
        if 'E' in args_dic:
            intensity = args_dic['E']
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
        pos_re = r'([A-Z])([-\.\d]+)'
        for arg in args:
            for found in re.findall(pos_re, arg):
                ret[found[0]] = float(found[1])
        return ret

    def BEGIN(self, *args):
        if args[0].lower() != 'waveform':
            raise ParseError("Can't understand args for BEGIN {args}")

        args_dic = self.single_letter_arg(*args[1:])

        time_step = args_dic['R']
        Npos = args_dic['N']
        measure_time_step = None
        if 'M' in args_dic.keys():
            measure_time_step = args_dic['M']

        if self._wavedata is not None:
            data = self._wavedata
        else:
            line = self.file.readline()
            data = {}
            while line != 'END\n' and line != 'END' and line != '':
                line = line.split(' ')
                data[line[0]] = np.asarray(line[1:], float)
                line = self.file.readline()
            if line != 'END\n' and line != 'END':
                raise ParseError("Can't find end + {line}")
            self._wavedata = data
        if 'E' in data:
            indices = ['X', 'Y', 'Z', 'E']
        else:
            indices = ['X', 'Y', 'Z']
        X = np.asarray([data[idx] for idx in indices])

        if np.shape(X)[1] != Npos:
            raise ParseError(
                    f"Mismatch in waveform! {np.shape(X)[1]} != {Npos}")
        self.run_waveform(time_step, X, measure_time_step=measure_time_step)
        self._wavedata = None

    def run_waveform(self, time_step, X, measure_time_step):
        pass

    def savemeasure(self, filename, numvalues, *tables):
        pass


class Execute_Parser(Parser):
    pause_status = QtCore.pyqtSignal(bool)

    def __init__(self, app_delegate):
        super().__init__()
        self.camera_delegate = app_delegate.camera_delegate
        self.md = app_delegate.movement_delegate
        self.piezo_delegate = app_delegate.movement_delegate.piezo
        self.motor_delegate = app_delegate.movement_delegate.motor
        self.laser_delegate = app_delegate.laser_delegate
        self.focus_delegate = app_delegate.focus_delegate
        self.coordinates_delegate = app_delegate.coordinates_delegate
        self.error_window = app_delegate.error
        self.lockid = None
        self._paused = False

        self.recording_macro = False

    class macro():
        def __init__(self, compatible):
            self._compatible = compatible

        def __call__(self, f):
            if self._compatible:
                def ret(cls, *args, **kargs):
                    cls.start_macro()
                    f(cls, *args, **kargs)
            else:
                def ret(cls, *args, **kargs):
                    cls.end_macro()
                    f(cls, *args, **kargs)
            return ret

    def start_macro(self):
        if not self.recording_macro:
            self.recording_macro = True
            if self.piezo_delegate.macro_exists('nextsteps'):
                self.piezo_delegate.macro_delete('nextsteps')
            self.piezo_delegate.macro_begin('nextsteps')

    def end_macro(self):
        if not self.recording_macro:
            return
        self.recording_macro = False
        self.piezo_delegate.macro_end()
        self.piezo_delegate.macro_start('nextsteps', wait=True)

    def parse(self, filename):
        if not self.md.motor.originMoved:
            raise ScriptError("The origin needs to be defined to run a script")
        self._paused = False
        self.pause_status.emit(self._paused)
        self.lockid = self.md.lock()
        if self.lockid is None:
            raise MotionError("Can't lock motion")
        try:
            super().parse(filename)
            self.end_macro()
        except BaseException:
            print("Parse failed, setting V to 0")
            self.laser_delegate.set_intensity(0)
            raise
        finally:
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
            kwargs_list = [{
                'start_offset': start_offset,
                'stop_offset': stop_offset,
                'step': step,
                'stage': self.md.piezo,
                'Nloops': 2,
                'wait': True,
                'checkid': self.lockid
            }]
        elif stage.lower() == 'motor':
            kwargs_list = [{
                'start_offset': start_offset,
                'stop_offset': stop_offset,
                'step': step,
                'stage': self.md.motor,
                'Nloops': 1,
                'wait': True,
                'checkid': self.lockid
            }]
        elif stage.lower() == 'both':
            kwargs_list = [{
                'start_offset': start_offset,
                'stop_offset': stop_offset,
                'step': step,
                'stage': self.md.motor,
                'Nloops': 1,
                'wait': True,
                'checkid': self.lockid
            }, {
                'start_offset': -2,
                'stop_offset': 2,
                'step': 1,
                'stage': self.md.piezo,
                'Nloops': 2,
                'wait': True,
                'checkid': self.lockid
            }]
        else:
            self.md.unlock()
            self.lockid = None
            raise ParseError(f"Don't know {stage}")

        for kwargs in kwargs_list:
            self.focus_delegate.focus(**kwargs)
            data, z_best, error = self.focus_delegate.get_result()
            if error is not None:
                self.handle_error(error)

    @macro(False)
    def piezoslope(self):
        self.coordinates_delegate.piezo_plane(
                checkid=self.lockid, wait=True)

    @macro(False)
    def piezoreset(self):
        self.piezo_delegate.reset(checkid=self.lockid, wait=True)

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
    def run_waveform(self, time_step, X, measure_time_step):
        self.camera_delegate.extShutter(False)
        self.piezo_delegate.run_waveform(time_step, X.T,
                                         measure_time_step=measure_time_step)

    def pause_resume(self, msg='Pause', pause=None):
        if not self.isRunning():
            return False

        if pause is None:
            pause = not self._paused

        if not pause and self._paused:
            # Resume
            self.lockid = self.md.lock()
            if self.lockid is None:
                raise MotionError("Can't lock motion")
            self._paused = False
        elif pause and not self._paused:
            # Pause
            self._paused = True
            self.md.unlock()
            self.lockid = None
        self.pause_status.emit(self._paused)
        return self._paused

    def stop(self):
        if self._prev_line is None or self._prev_line[0] is None:
            return
        self._next_line = None, None
        self._paused = False
        self.pause_status.emit(self._paused)

    def isPaused(self):
        return self._paused

    def readline(self):
        while self._paused:
            time.sleep(1)
        return super().readline()

    def parse_line(self, fun, args):
        try:
            fun(*args)
        except BaseException as e:
            logError()
            self.handle_error(e)

    def handle_error(self, error):
        # Repeat previous line
        self._next_line = self._prev_line
        self.md.unlock()
        self.pause_resume(msg="Focus issue - Paused", pause=True)
        self.error_window.emit(
               f"Error while parsing line {self.line_nbr}:\r\n"
               f"{self._prev_line[0].__name__} {self._prev_line[1]}\r\n"
               f"{error}")

    @macro(False)
    def savemeasure(self, filename, numvalues):
        measure = self.piezo_delegate.get_measure(0, int(numvalues))
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'bw') as f:
            np.save(f, np.concatenate(
                    (measure['Target'],
                     measure['Current'],
                     measure['Power'][:, np.newaxis]), axis=1))


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
            print("Parse failed, can't draw")
            print(e)
            raise
        lc = mc.LineCollection(self.lines, colors=self.colors, linewidths=2)
        self.canvas._axes.add_collection(lc)
        self.canvas._axes.axis('equal')

        self.canvas.draw.emit()
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
        if power == 0:
            self.writing = True
        elif power > 0:
            self.writing = True
        self.color = cmap(power / 4)

    def piezoreset(self):
        self.piezo_position = np.zeros(3)

    def run_waveform(self, time_step, X, measure_time_step):
        step = int(0.1 / time_step)
        for idx in [*np.arange(X.shape[1] // step) * step, X.shape[1] - 1]:
            pos = X[:, idx]
            I = np.nan
            if len(pos) > 3:
                I = pos[3]
                pos = pos[:3]
            self.piezo(pos, 3000, I)
