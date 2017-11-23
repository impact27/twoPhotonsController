# -*- coding: utf-8 -*-
"""
Created on Mon May  1 11:17:39 2017

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
import re
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure, plot, imshow


class gcode_reader:
    def __init__(self):
        self.G_re = 'G(\d+)((?: [EFXYZ][-\.\d]+)*)'
        self.arg_re = '([EFXYZ])([-\.\d]+)'

    def readFile(self, filename):
        with open(filename, 'r') as f:
            gtxt = f.read()
        self.readGcommands(gtxt)

    def readGcommands(self, gtxt):
        Gcommands = re.findall(self.G_re, gtxt)
        for command in Gcommands:
            if command[0] == '92':
                # Change intensity without moving
                self.stop()

            elif command[0] == '1':
                # Move straight
                Xnew, Ynew, Znew = np.zeros(3) * np.nan
                for arg in re.findall(self.arg_re, command[1]):
                    if arg[0] == 'E':
                        self.setIntensity(float(arg[1]))
                    elif arg[0] == 'F':
                        self.setSpeed(float(arg[1]))
                    elif arg[0] == 'X':
                        Xnew = float(arg[1])
                    elif arg[0] == 'Y':
                        Ynew = float(arg[1])
                    elif arg[0] == 'Z':
                        Znew = float(arg[1])
                # Go to new position with speed F and intensity E
                self.moveTo(Xnew, Ynew, Znew)

    def setIntensity(self, E):
        pass

    def moveTo(self, X, Y, Z):
        pass

    def setSpeed(self, F):
        pass

    def stop(self):
        pass


#%%
class gcode_checker(gcode_reader):
    def __init__(self, intensityRange, posRange, speedRange):
        super().__init__()
        self.isvalid = True
        self.ERange = intensityRange
        self.XYZRange = posRange
        self.FRange = speedRange

    def gcode_inrange(self, gcode):
        self.readGcommands(gcode)
        return self.isvalid

    def setIntensity(self, E):
        if E < self.ERange[0] or E > self.ERange[-1]:
            self.isvalid = False

    def moveTo(self, X, Y, Z):
        if X < self.XYZRange[0, 0] or X > self.XYZRange[0, -1]:
            self.isvalid = False
        if Y < self.XYZRange[1, 0] or Y > self.XYZRange[1, -1]:
            self.isvalid = False
        if Z < self.XYZRange[2, 0] or Z > self.XYZRange[2, -1]:
            self.isvalid = False

    def setSpeed(self, F):
        if F < self.FRange[0] or F > self.FRange[-1]:
            self.isvalid = False

    def stop(self):
        self.setIntensity(0)


class gcode_draw(gcode_reader):
    def __init__(self):
        super().__init__()
        self.X = 0
        self.Y = 0
        self.Z = 0
        self.E = 0
        self.F = 0
        self.written = []

    def setIntensity(self, E):
        self.E = E

    def moveTo(self, X, Y, Z):
        # Wait for the stage to stop
        np.array((X, Y, Z))[np.isnan((X, Y, Z))] = np.array(
                (self.X, self.Y, self.Z))[np.isnan((X, Y, Z))]

        if self.E == 0:
            self.written.append(np.zeros(3) * np.nan)
        self.written.append((X, Y, Z))

        self.X, self.Y, self.Z = X, Y, Z

    def setSpeed(self, F):
        self.F = F

    def getDrawing(self):
        return np.asarray(self.written)

    def stop(self):
        self.setIntensity(0)
