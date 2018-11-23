# -*- coding: utf-8 -*-
"""
Created on Fri Mar  9 12:18:02 2018

@author: quentinpeter
"""
import numpy as np


class ScriptFile():

    def __init__(self):
        self._lines = []
        self._lines.append("laser power 0")
        self._lines.append("laser ON")

        # Keep track of the time and position
        self.min_time = 0
        self.position = {'motor': None,
                         'piezo': None}

    def add_time_to(self, stage, pos, speed):
        """
        Check time needed to move to position
        """
        pos = np.asarray(pos)
        if self.position[stage] is None:
            self.position[stage] = pos
            return
        length = np.linalg.norm(pos - self.position[stage])
        self.min_time += length / speed
        self.position[stage] = pos

    def laser_voltage(self, V):
        "Set laset voltage"
        self._lines.append("laser power {:.3f}".format(float(V)))

    def goto(self, stage, X, speed):
        "Go to position"
        self._lines.append(
                "{stage} X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:.3f}".format(
                    stage=stage,
                    x=X[0],
                    y=X[1],
                    z=X[2],
                    f=speed))
        # Add time it takes
        self.add_time_to(stage, X, speed)

    def focus(self, stage, zfrom, zto, zstep):
        "Focus"
        self._lines.append(f"focus {stage} {zfrom} {zto} {zstep}")
        # Time estimation
        self.min_time += 0.2 * (zto - zfrom) / zstep
        self.position[stage][2] = 0

    def save(self, fn):
        "Save to file"
        with open(fn, 'w') as f:
            f.write('\n'.join(self._lines))

    def piezo_reset(self):
        "Reset the piezo"
        self._lines.append('piezoreset')

        self.position['piezo'] = np.zeros(3)

    def piezo_slope(self):
        "Find the piezo slope"
        self._lines.append("piezoslope")
        # Time estimation
        self.min_time += 10

    def piezo_waveform(self, X, time_step, measure_time_step=None):
        "Perform a waveform"
        assert np.all(np.abs(X[:3]) < 50)
        assert X.shape[0] == 3 or X.shape[0] == 4
        self._lines.append(
            f"BEGIN waveform R{time_step} N{X.shape[1]}"
            )
        if measure_time_step is not None:
            self._lines[-1] += f" M{measure_time_step}"

        axes = ['X', 'Y', 'Z', 'E']
        for ax_idx, axis in enumerate(axes):
            self._lines.append(
                axis +
                " " +
                " ".join(
                    f'{e:.3f}' for e in X[ax_idx]))
        self._lines.append("END")
        # Update time
        self.position['piezo'] = X[:3, -1]
        self.min_time += X.shape[1] * time_step

    def save_measure(self, filename, numvalues):
        self._lines.append(f"savemeasure {filename} {numvalues}")
