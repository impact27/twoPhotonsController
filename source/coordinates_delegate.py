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
#from position_correctors import XYcorrector
from coordinates_solver import Zsolver, XYsolver
from PyQt5 import QtCore, QtWidgets


class coordinates_delegate(QtCore.QObject):

    updatelist = QtCore.pyqtSignal(list)

    def __init__(self, application_delegate):
        super().__init__()
        self._positions = []
        self._current_pos = None
        self.parent = application_delegate
        self.camera = application_delegate.camera_delegate
        self._md = application_delegate.mouvment_delegate
        self.motor = application_delegate.mouvment_delegate.motor
        self.Zsolver = Zsolver()
        self.XYsolver = XYsolver()

    def add_position(self, Xm):
        self._positions.append(
            {'Xm': Xm,
             'Xs': None,
             'im': None})
        self._load_next()
        self._update()

    def load_list(self, fn):
        """Read file containing 3 x N float numbers"""
        positions = list(np.loadtxt(fn))
        for pos in positions:
            self.add_position(pos)

    def displayrow(self, row):
        pos = self._positions[row]
        if pos['im'] is None:
            return
        self.parent.canvas_delegate.show_image(pos['im'])

    @property
    def positions(self):
        return self._positions

    def clear_positions(self):
        self._positions = []
        self._current_pos = None
        self._update()

    def del_position(self, idx):
        del self._positions[idx]
        self._update()

    def processPos(self):
        # Save new position
        self._newPos()
        # if still positions in the list & position is reachable:
        if self._load_next():
                # go to position
            self.motor.goto_position(self._current_pos['Xm'])

    def save_errors(self):
        fn = QtWidgets.QFileDialog.getSaveFileName(
            QtWidgets.QApplication.topLevelWidgets()[0], 'TXT file',
            QtCore.QDir.homePath(), "Text (*.txt)")[0]
        ret = np.zeros((len(self._positions), 3))
        for i, pos in enumerate(self._positions):
            Xm1 = pos['Xm']
            Xm2 = self._md.motor.XstoXm(pos['Xs'])
            ret[i] = (Xm1 - Xm2)
        np.savetxt(fn, ret)

    def _load_next(self):
        for pos in self._positions:
            if pos['Xs'] is None:
                self._current_pos = pos
                return True
        self._current_pos = None
        return False

    def _newPos(self):
        if not self._md.is_onTarget():
            raise RuntimeError("Stage is moving!")
        # Save XYZ as new value
        self._current_pos['Xs'] = self.motor.get_position(raw=True)
        self._current_pos['im'] = self.camera.get_image()
        self._update()

    def _updateXYZCorr(self):

        # get Xm and Xs
        Xms = np.asarray([p['Xm'] for p in self._positions])
        Xss = np.asarray([p['Xs'] for p in self._positions])
        valid = [p is not None for p in Xss]
        if np.any(valid):
            Xms = Xms[valid]
            Xss = np.asarray(list(Xss[valid]))
            # Get coeffs
            zcoeffs = self.Zsolver.solve(Xss)
            xycoeffs = self.XYsolver.solve(Xss[:, :2], Xms[:, :2])
        else:
            zcoeffs = np.zeros(3)
            xycoeffs = np.zeros(4)
            
        stage_diff_angle, rotation_angle, *XYoffset = xycoeffs
        Zslope, Zoffset = zcoeffs
        offset = np.asarray([*XYoffset, Zoffset])
        
        corrections = {
            "offset": offset,
            "slope": Zslope,
            "rotation angle": rotation_angle,
            "stage diff angle": stage_diff_angle
            }
        
        # Apply correction
        self._md.corrections = corrections

    def _update(self):
        # use saved info to correct coordinates
        self._updateXYZCorr()
        self.updatelist.emit(self._positions)
        
    def offset_origin(self, newXm):
        corrections = self._md.corrections
        oldXm = self._md.position
        corrections['offset'] += oldXm - newXm
        self._md.corrections = corrections
        