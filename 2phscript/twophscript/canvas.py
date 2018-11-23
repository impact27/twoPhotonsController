#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 19 13:39:24 2018

@author: quentinpeter
"""
import numpy as np
from .power_converter import PowerConverter

PIEZO_DELAY = 10e-3  # s
PIEZO_MAX_POINTS = 2**18
PIEZO_RANGE = 50
PIEZO_MOTOR_FOCUS = [49, 49, 0]


class Canvas():
    def __init__(self, calibration_fn, off_speed, minZmargin, safety_slope):
        super().__init__()
        self.commands = []
        self.off_speed = off_speed
        self.pc = PowerConverter(calibration_fn)
        self.minZmargin = minZmargin
        self.safety_slope = safety_slope

    def Zmargin(self, distance):
        return self.minZmargin + distance * self.safety_slope

    def add_line(self, Xfrom, Xto, *, speed, power):
        self.commands.append({
                'cmd': 'line',
                'Xfrom': Xfrom,
                'Xto': Xto,
                'speed': speed,
                'power': power
                })

    def _write_line(self, file, stage, Xfrom, Xto, speed, intensity):

        file.laser_voltage(0)
        file.goto(stage, Xfrom, self.off_speed)
        file.laser_voltage(self.pc.PtoV(intensity))
        file.goto(stage, Xto, speed)
        file.laser_voltage(0)

    def write_at(self, file, XY):
        XY = np.asarray(XY)
        if XY.ndim == 1:
            XY.shape = (1, *XY.shape)

        for pos in XY:
            self.prepare_write(file, pos)
            self.write_commands(file)
            self.end_write(file, pos)

    def prepare_write(self, file, pos):
        raise NotImplementedError()

    def write_commands(self, file):
        for command in self.commands:
            self.write_command(file, command)

    def write_command(self, file, command):
        if command['cmd'] == 'line':
            self._write_line(
                file,
                'piezo',
                command['Xfrom'],
                command['Xto'],
                command['speed'],
                command['power'])
        else:
            raise NotImplementedError(f"What is {command['cmd']}?")

    def end_write(self, file, pos):
        raise NotImplementedError()

    def longmoveMotor(self, file, pos):
        XYfrom = file.position['motor']
        if XYfrom is None:
            XYfrom = pos
        elif np.all([*pos, 0] == XYfrom):
            return
        else:
            XYfrom = XYfrom[:2]
        safety_z = self.Zmargin(np.linalg.norm(pos - XYfrom))
        file.piezo_reset()
        file.goto('motor', [*pos, safety_z], self.off_speed)
        file.goto('piezo', PIEZO_MOTOR_FOCUS, self.off_speed)
        file.focus('motor', 0, -2 * safety_z, -1)


class Piezo_Canvas(Canvas):
    """
    Write with piezo
    """

    def __init__(self, calibration_fn, off_speed, dt,
                 XYmargin, minZmargin, safety_slope, measure_dt=None):
        super().__init__(calibration_fn, off_speed, minZmargin, safety_slope)
        self.dt = dt
        self.measure_dt = measure_dt
        self.XYmargin = XYmargin

        self.max_points = PIEZO_MAX_POINTS
        self.piezo_delay = PIEZO_DELAY
        self.max_range = PIEZO_RANGE  # um
        self.filecount = {}

    def prepare_write(self, file, pos):
        self.longmoveMotor(file, pos)
        file.piezo_slope()

    def write_command(self, file, command):
        if command['cmd'] == 'wave':
            file.piezo_waveform(command['wave'], self.dt,
                                measure_time_step=self.measure_dt)
        elif command['cmd'] == 'save_wave':
            # As we can call this function on the same file several time,
            # add a suffix
            if file not in self.filecount.keys():
                self.filecount[file] = 0
            file.save_measure(
                    command['filename'] + '_'
                        f'{self.filecount[file]}.npy',
                    command['numvalues'])
            self.filecount[file] += 1
        else:
            super().write_command(file, command)

    def end_write(self, file, pos):
        pass
        # file.piezo_reset()

    @property
    def _cur_wave(self):
        """
        Get the current wave or an empty wave if we are None
        """
        if len(self.commands) == 0 or self.commands[-1]['cmd'] != 'wave':
            return None
        else:
            return self.commands[-1]['wave']

    @_cur_wave.setter
    def _cur_wave(self, wave):
        """
        Change the current wave or create a new one if there are None
        """
        if len(self.commands) == 0 or self.commands[-1]['cmd'] != 'wave':
            self.commands.append({
                    'cmd': 'wave',
                    'wave': wave})
        else:
            self.commands[-1]['wave'] = wave

    def _new_wave(self):
        """
        Create a new current wave
        """
        self.commands.append({
                    'cmd': 'wave',
                    'wave': np.zeros((4, 0))})

    def add_wave(self, wave):
        """
        Adds a wave to the canvas
        """
        # Check points are in the range
        if not np.all(np.abs(wave[:3]) <= self.max_range - self.XYmargin):
            raise RuntimeError('A point is outside of the defined range.')

        # translate power into voltage
        wave[3] = self.pc.PtoV(wave[3])

        # Apply delay
        wave = self._apply_delay(wave, self.piezo_delay)

        # check we don't have too many points
        if wave.size > self.max_points:
            raise RuntimeError('Too many points for controller. Decrease dt.')

        # if no wave yet, save and stop
        if self._cur_wave is None:
            self._cur_wave = wave
            return

        # move to beginning of wave
        move_wave = self.move_wave(
            [*self._cur_wave[:3, -1], 0],
            [*wave[:3, 0], 0])
        # wait for movment to truly be stopped
        move_wave = self._apply_delay(move_wave, 10*self.piezo_delay)

        # if can combine with existing wave, do it
        if (self._cur_wave.shape[1] + move_wave.shape[1] + wave.shape[1]
                < self.max_points / 4):
            self._cur_wave = np.concatenate(
                    (self._cur_wave, move_wave, wave), axis=1)
        else:
            self._new_wave()
            self._cur_wave = wave

    def move_wave(self, Xfrom, Xto):
        """
        Get straight line with laser off
        """
        Xfrom = np.asarray(Xfrom)
        Xto = np.asarray(Xto)
        dX = Xto - Xfrom
        distance = np.linalg.norm(dX[:3])
        dXnorm = dX / distance

        times = np.arange(0, distance / self.off_speed, self.dt)

        wave = Xfrom[:, np.newaxis] + \
            dXnorm[:, np.newaxis] * self.off_speed * times[np.newaxis]
        return wave

    def _apply_delay(self, wave_line, piezo_delay):
        """
        Apply the delay to synchronise the movment and the laser
        """

        if not np.shape(wave_line)[0] == 4:
            raise NotImplementedError("Can only apply delay with 4xN waves")

        N_delay = int(np.round(piezo_delay / self.dt))

        # Adds N_delay points at the end
        wave_delay = np.ones((4, N_delay)) * wave_line[:, -1][:, np.newaxis]
        wave_line = np.concatenate((wave_line, wave_delay), axis=1)

        # Shifts top line to apply delay
        wave_line[3, N_delay:] = wave_line[3, :-N_delay]
        wave_line[3, :N_delay] = 0

        # Add 0 laser power at beginning and end
        wave_line = np.insert(wave_line, 0,
                              [*wave_line[:3, 0], 0], axis=1)
        wave_line = np.insert(wave_line, np.shape(wave_line)[1],
                              [*wave_line[:3, -1], 0], axis=1)

        return wave_line

    def save_wave(self, filename, numvalues=None):
        if self._cur_wave is None:
            raise RuntimeError("No wave to save!")
        if numvalues is None:
            numvalues = self._cur_wave.shape[1] * self.dt / self.measure_dt
        self.commands.append({
                    'cmd': 'save_wave',
                    'filename': filename,
                    'numvalues': int(numvalues)
                    })


class Motor_Canvas(Canvas):
    def __init__(self, calibration_fn, off_speed, minZmargin, safety_slope):
        super().__init__(calibration_fn, off_speed, minZmargin, safety_slope)
        self.offset = np.zeros(3)

    def prepare_write(self, file, pos):
        self.longmoveMotor(file, pos)
        # file.motor_slope()
        # file.move_origin([*XYto, 0])
        self.offset[:2] = pos
        self.XYpos_int = np.zeros(2)

    def end_write(self, file, pos):
        # file.move_origin([*(-pos), 0])
        self.offset[:2] = 0

    def add_canvas(self, canvas, pos):
        self.commands.append({
                    'cmd': 'canvas',
                    'canvas': canvas,
                    'position': pos})

    def write_command(self, file, command):
        if command['cmd'] == 'line':
            self._write_line(
                file,
                'piezo',
                command['Xfrom'] + self.offset,
                command['Xto'] + self.offset,
                command['speed'],
                command['power'])
            self.XYpos_int = command['Xto']
        elif command['cmd'] == 'canvas':
            XYto_ext = command['position'] + self.offset[:2]
            self.longmoveMotor(file, XYto_ext)
            command['canvas'].write_at(file, XYto_ext)
            self.XYpos_int = command['position']
        else:
            super().write_command(file, command)
