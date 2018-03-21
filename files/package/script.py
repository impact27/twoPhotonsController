# -*- coding: utf-8 -*-
"""
Created on Fri Mar  9 12:18:02 2018

@author: quentinpeter
"""

class Script():
    
    def __init__(self, *, focus_int, off_speed, write_speed, write_power):
        self._lines = ['focusint 0.5']
        self.off_speed = off_speed
        self._lines.append("laser power 0")
        self._lines.append("laser ON")
        self._write_ready = False
        self.write_speed = write_speed
        self.write_power = write_power

    def write_line_motor(self, Xfrom, Xto):
        self.write_line(Xfrom, Xto, 'motor')
        
    def write_line_piezo(self, Xfrom, Xto):
        self.write_line(Xfrom, Xto, 'piezo')
        
    def write_line(self, Xfrom, Xto, stage):
        if not self._write_ready and stage =='piezo':
            self.prepare_piezo_write()
        self._lines.append("laser power 0")
        self._lines.append("{stage} X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:d}".format(
            stage=stage,
            x=Xfrom[0],
            y=Xfrom[1],
            z=Xfrom[2],
            f=self.off_speed))
    
        self._lines.append("laser power {:f}".format(
                self.write_power))
        self._lines.append("{stage} X{x:.3f} Y{y:.3f} Z{z:.3f} F{f:d}".format(
            stage=stage,
            x=Xto[0],
            y=Xto[1],
            z=Xto[2],
            f=self.write_speed))
        self._lines.append("laser power 0")
        
        
    def move_motor(self, X):
        self._write_ready = False
        self._lines.append('piezoreset')
        self._lines.append("motor X{x:.3f} Y{y:.3f} Z{z:.3f} F{s:.3f}".format(
                x=X[0], y=X[1], z=X[2], s=self.off_speed))
        
    def prepare_piezo_write(self):
        self._lines.append("focus motor 0 -40 -1")
        self._lines.append("piezoslope")
        self._write_ready = True

    def save(self, fn):
         with open(fn, 'w') as f:
             f.write('\n'.join(self._lines))