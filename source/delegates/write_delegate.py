# -*- coding: utf-8 -*-
"""
Created on Sun May  7 14:23:39 2017

@author: quentinpeter

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import numpy as np
import sys
from PyQt5 import QtCore
from serial.serialutil import SerialTimeoutException

from .gcode import gcode_reader, gcode_checker, gcode_draw


class write_delegate(QtCore.QObject):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_thread()

    def init_thread(self):
        self.thread = write_thread(self.parent)
        self.thread.finished.connect(self.endwrite)

    def write(self, gfilename, settings):
        with open(gfilename, 'r') as f:
            gcommands = f.read()
        intensityRange = self.parent.laser_delegate.get_range()
        posRange = np.asarray([
            self.parent.movement_delegate.piezzo.get_positionRange(0),
            self.parent.movement_delegate.piezzo.get_positionRange(1),
            self.parent.movement_delegate.piezzo.get_positionRange(2)
        ])
        speedRange = self.parent.movement_delegate.piezzo.get_velocityRange(0)

        checker = gcode_checker(intensityRange, posRange, speedRange)

        if not checker.gcode_inrange(gcommands):
            self.parent.error.emit("GCode values out of range")
            return

        self.thread.set_args(gcommands, settings)
        self.thread.start()

    def endwrite(self):
        self.parent.movement_delegate.updatePosition.emit()

    def ESTOP(self):
        self.thread.terminate()
        self.init_thread()

    def draw(self, gpath, settings):

        greader = gcode_draw()
        greader.readFile(gpath)

        gwritten = greader.getDrawing()

        xori, yori = settings['XY origin']
        Nx, Ny = settings['[X, Y] number of steps']
        dx, dy = settings['[X, Y] steps size']

        if Nx == 1:
            dx = 1
        if Ny == 1:
            dy = 1
        for x in np.arange(xori, xori + Nx * dx, dx):
            for y in np.arange(yori, yori + Ny * dy, dy):
                self.parent.canvas_delegate.plot(
                    gwritten[:, 0] + x, gwritten[:, 1] + y, axis='equal')


class write_thread(QtCore.QThread):
    def __init__(self, parent):
        super().__init__()
        self.md = parent.movement_delegate
        self.ld = parent.laser_delegate
        self.error = None
        self.args = None
        self.lockid = None
        self.gcommands = None
        self.parent = parent
        self.focus_delegate = parent.focus_delegate

    def set_args(self, gcommands, settings):
        self.settings = settings
        self.gcommands = gcommands

    def run(self):
        try:
            self.lockid = self.md.lock()

            def goto(X):
                self.md.motor.goto_position(X, wait=True, checkid=self.lockid)

            if self.lockid is None:
                self.error = "Unable to lock the movement"
                return

            xori, yori = self.settings['XY origin']
            Nx, Ny = self.settings['[X, Y] number of steps']
            dx, dy = self.settings['[X, Y] steps size']
            focus_offset = self.settings['focus offset']
            focus_range = self.settings['focus range']
            focus_step = self.settings['focus step']
            move_dist = self.settings['movment retraction']

            if Nx == 1:
                dx = 1
            if Ny == 1:
                dy = 1

             # Focus with z stage
            self.focus_delegate.focus(-focus_range / 2, focus_range / 2, focus_step,
                                      stage=self.md.motor,
                                      intensity=None,
                                      Nloops=1,
                                      wait=True,
                                      checkid=self.lockid)

            intensity = self.ld.get_intensity()

            for par, y in enumerate(np.arange(yori, yori + Ny * dy, dy)):
                # Want to draw s
                parity = 2 * ((par + 1) % 2) - 1
                for x in np.arange(xori, xori + Nx * dx, dx)[::parity]:
                    # Retract
                    goto([np.nan,
                          np.nan,
                          move_dist])
                    self.md.piezzo.reset()
                    # Move to pos
                    goto([x + focus_offset[0],
                          y + focus_offset[1],
                          move_dist])

                    # approach
                    goto([x + focus_offset[0],
                          y + focus_offset[1],
                          focus_range / 2])
                    # Focus with z stage
                    self.focus_delegate.focus(0, -focus_range, focus_step,
                                              stage=self.md.motor,
                                              intensity=intensity,
                                              Nloops=1,
                                              wait=True,
                                              checkid=self.lockid)

                    # Move to pos
                    goto([x, y, 0])

                    # Focus with piezzo
                    self.focus_delegate.focus(-5, 5, 1,
                                              stage=self.md.piezzo,
                                              intensity=intensity,
                                              Nloops=2,
                                              wait=True,
                                              checkid=self.lockid)

                    # Write
                    self.writeGCode()

        except SerialTimeoutException:
            self.parent.error('Timeout')
        except BaseException:
            print("Unknown exception during write")
            print(sys.exc_info()[0])
            raise

        self.md.unlock()

    def writeGCode(self):
        self.parent.camera_delegate.extShutter(False)
        defaultCubeSpeed = self.md.piezzo.get_velocity()
        writer = gwriter(self.md.piezzo, self.ld, self.lockid)
        writer.readGcommands(self.gcommands)
        self.ld.set_intensity(0)
        self.md.piezzo.set_velocity(defaultCubeSpeed, checkid=self.lockid)
        self.parent.camera_delegate.extShutter(True)


class gwriter(gcode_reader):

    def __init__(self, motor, ld, lockid):
        super().__init__()
        self.motor = motor
        self.ld = ld
        self.ld.set_intensity(0)
        self.lockid = lockid
        self.Xmlast = np.zeros(3)

    def __del__(self):
        self.ld.set_intensity(0)
        self.ld.switch(False)

    def setIntensity(self, E):
        self.ld.set_intensity(E)

    def moveTo(self, X, Y, Z):
        Xmto = np.asarray([X, Y, Z])
        Xmto[np.isnan(Xmto)] = self.Xmlast[np.isnan(Xmto)]
        self.motor.goto_position(Xmto, wait=True, checkid=self.lockid)
        self.Xmlast = Xmto

    def setSpeed(self, F):
        self.motor.set_velocity(F, checkid=self.lockid)

    def stop(self):
        self.ld.switch(False)
