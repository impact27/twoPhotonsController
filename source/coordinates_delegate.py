# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 11:52:10 2017

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
from position_correctors import XYcorrector, Zcorrector
from coordinates_solver import Zsolver, XYsolver

class coordinate_delegate():
    
    def __init__(self, camera, mouvment_delegate):
        self._positions = []
        self._current_pos = None
        self._bgOffset= np.array([100, 100, 0])
        self.camera = camera
        self._md = mouvment_delegate
        self.motor = mouvment_delegate.motor
        self.XYcorrector = XYcorrector()
        self.Zcorrector = Zcorrector()
        self.Zsolver = Zsolver()
        self.XYsolver = XYsolver()
        
    def load_list(self, fn):
        """Read file containing 3 x N float numbers"""
        positions = list(np.loadtxt(fn))
        for pos in positions:
            self._positions.append(
                   {'Xm' : pos,
                    'Xs' : None,
                    'im' : None,
                    'graphs' : None})
        self._load_next()
        
    def processPos(self):
        #Add that in a thread
        
        #Turn off autoshutter
        self.camera.autoShutter(False)
        #go to bg position
        self.motor.move_by(self._bgOffset, wait=True)
        #focus using laser
        graphs = self.Zcorrector.focus()
        #take bg
        self.camera.set_bg()
        #return to image position
        self.motor.move_by(-self._bgOffset, wait=True)
        #correct XY if reference image exists, otherwise set reference image
        self.XYcorrector.align()
        #Save new position
        self._newPos(graphs)
        #use saved info to correct coordinates
        self._updateXYZCorr()
        #if still positions in the list & position is reachable:
        if self._load_next():
        	#go to position
            self.motor.goto_position(self._current_pos['Xm'], wait=True)
        
    def _load_next(self):
        for pos in self._positions:
            if pos['Xs'] is None:
                self._current_pos = pos
                return True
        self._current_pos = None
        return False
    
    def _newPos(self, graphs):
        #Save XYZ as new value
        self._current_pos['Xs'] = self.motor.get_position(raw = True)
        self._current_pos['im'] = self.camera.get_image()
        self._current_pos['graphs'] = graphs
        
    
        
    def _updateXYZCorr(self):
        #get Xm and Xs
        Xm = np.asarray([p['Xm'] for p in self._positions])
        Xs = np.asarray([p['Xs'] for p in self._positions])
        valid = [p is None for p in Xs]
        Xm = Xm[valid]
        Xs = np.asarray(list(Xs[valid]))
        #Get coeffs
        zcoeffs = self.Zsolver.solve(Xs)
        xycoeffs = self.XYsolver.solve(Xs[:2], Xm[:2])
        #Apply correction
        self._md.set_XY_correction(xycoeffs)
        self._md.set_Z_correction(zcoeffs)
        
        self.parent.correctTilt()
    
        
    
#     def run(self):
#         self.lockid=self.md.lock()
#         
#         if self.lockid is None:
#             self.error = "Unable to lock the mouvment"
#             return
#         
#         self.md.unlock()
        

        
    