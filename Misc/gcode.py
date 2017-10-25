# -*- coding: utf-8 -*-

import numpy as np
import re
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure, plot, imshow


class GController:
    def __init__(self):
        self.G_re = 'G(\d+)((?: [EFXYZ][-\.\d]+)*)'
        self.arg_re = '([EFXYZ])([-\.\d]+)'

    def readGcommands(self, gtxt):
        Gcommands = re.findall(self.G_re, gtxt)
        for command in Gcommands:
            if command[0] == '92':
                # Change intensity without moving
                for arg in re.findall(self.arg_re, command[1]):
                    if arg[0] == 'E':
                        self.setIntensity(float(arg[1]))

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


#%%
class DrawCController(GController):
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


filename = 'cross.gcode'

with open(filename, 'r') as f:
    gtxt = f.read()

controller = DrawCController()

controller.readGcommands(gtxt)

path = np.asarray(controller.written)
figure()
plot(path[:, 0], path[:, 1])
