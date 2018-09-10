# -*- coding: utf-8 -*-
"""
Created on Fri Mar  9 12:18:02 2018

@author: quentinpeter
"""
import numpy as np
class Script():
    
    def __init__(self, *, off_speed, safety_z):
        self._lines = []
        self.off_speed = off_speed
        self.safety_z = safety_z
        self._lines.append("laser power 0")
        self._lines.append("laser ON")
        self._write_ready = False

    def write_line_motor(self, Xfrom, Xto):
        self.write_line(Xfrom, Xto, 'motor')
        
    def write_line_piezo(self, Xfrom, Xto):
        assert np.all(np.abs(Xfrom) < 49)
        assert np.all(np.abs(Xto) < 49)
        self.write_line(Xfrom, Xto, 'piezo')
        
    def write_line(self, Xfrom, Xto, stage):
        if not self._write_ready and stage =='piezo':
            self.prepare_piezo_write()
        self._lines.append("laser power 0")
        self._lines.append("{stage} X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:.3f}".format(
            stage=stage,
            x=Xfrom[0],
            y=Xfrom[1],
            z=Xfrom[2],
            f=self.off_speed))
    
        self._lines.append("laser power {:.3f}".format(
                float(self.write_voltage)))
        self._lines.append("{stage} X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:.3f}".format(
            stage=stage,
            x=Xto[0],
            y=Xto[1],
            z=Xto[2],
            f=self.write_speed))
        self._lines.append("laser power 0")
        
    def move_piezo(self, X):
        assert np.all(np.abs(X) < 49)
        self._lines.append("laser power 0")
        self._lines.append("{stage} X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:.3f}".format(
            stage='piezo',
            x=X[0],
            y=X[1],
            z=X[2],
            f=self.off_speed))
        
    def move_motor(self, X):
        self._write_ready = False
        self._lines.append('piezoreset')
        self._lines.append("motor X{x:.3f} Y{y:.3f} Z{z:.3f} F{s:.3f}".format(
                x=X[0], y=X[1], z=X[2], s=self.off_speed))
        
    def prepare_piezo_write(self):
        self._lines.append("focus motor 0 -{safety_z} -1".format(
                safety_z= 2 * self.safety_z))
        self._lines.append("piezoslope")
        self._write_ready = True

    def save(self, fn):
         with open(fn, 'w') as f:
             f.write('\n'.join(self._lines))
             
    def waveform(self, X, time_step):
        assert np.all(np.abs(X) < 49)
        assert X.shape[0] == 3 or X.shape[0] == 4
        if not self._write_ready:
            self.prepare_piezo_write()
        self._lines.append(
                "BEGIN waveform R{time_step} N{number_points}".format(
                time_step=time_step,
                number_points=X.shape[1]
                ))
        axes = ['X', 'Y', 'Z', 'E']
        for ax_idx, axis in enumerate(axes):
            self._lines.append(axis + " " + " ".join(f'{e:.3f}' for e in X[ax_idx]))
        self._lines.append("END")
