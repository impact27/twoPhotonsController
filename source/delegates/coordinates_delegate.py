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
from PyQt5 import QtCore, QtWidgets

#from position_correctors import XYcorrector
from .coordinates_solver import solve_z, solve_xyz


class coordinates_delegate(QtCore.QObject):

    updatelist = QtCore.pyqtSignal(list)

    def __init__(self, application_delegate):
        super().__init__()
        self._positions = []
        self._current_pos = None
        self.parent = application_delegate
        self.camera = application_delegate.camera_delegate
        self._md = application_delegate.mouvment_delegate
        self.init_thread()

    def init_thread(self):
        self.plane_thread = plane_thread(self.parent)

    def piezzo_plane(self, checkid=None, wait=False):
        stage = self._md.piezzo
        XYs = ([-45, -45], [-45, 45],
               [45, 45], [45, -45])
        intensity = 0.5
        self.plane_thread.settings(stage, intensity, XYs, 2, -2.1, -1, 2)
        if checkid is not None:
            self.plane_thread.checkid = checkid
        self.plane_thread.start()

        if wait:
            self.plane_thread.wait()
            
    def motor_plane(self, checkid=None, wait=False):
        if len(self._positions) < 3:
            return
        stage = self._md.motor
        Xms = np.asarray([p['Xm'] for p in self._positions])
        Xms = Xms[:, :2]
        intensity = 0.5
        self.plane_thread.settings(stage, intensity, Xms, 20, -20, -1, 1)
        if checkid is not None:
            self.plane_thread.checkid = checkid
        self.plane_thread.start()
        

    def ESTOP(self):
        self.plane_thread.terminate()
        self.init_thread()

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
        self.parent.canvas_delegate.imshow(pos['im'])

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
            self._md.piezzo.reset()
            self._md.motor.goto_position(self._current_pos['Xm'])

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
        self._current_pos['Xs'] = self._md.motor.get_position(raw=True)
        self._current_pos['im'] = self.camera.get_image()
        self._update()
        self._updateXYZCorr()

    def _updateXYZCorr(self):

        # get Xm and Xs
        Xms = np.asarray([p['Xm'] for p in self._positions])
        Xss = np.asarray([p['Xs'] for p in self._positions])
        valid = [p is not None for p in Xss]
        if np.any(valid):
            Xms = Xms[valid]
            Xss = np.asarray(list(Xss[valid]))
            # Get coeffs
            offset, rot_angles = solve_xyz(Xss, Xms)
        else:
            offset = np.zeros(3)
            rot_angles = np.zeros(4)

        corrections = {
            "offset": offset,
            "rotation angles": rot_angles
        }

        # Apply correction
        self._md.motor.corrections = corrections

        # Propagate Z cirrection to piezzo
        piezzo_corr = self._md.piezzo.corrections
        piezzo_corr["rotation angles"][2] = rot_angles[2]
        self._md.piezzo.corrections = piezzo_corr

    def _update(self):
        # use saved info to correct coordinates
        self.updatelist.emit(self._positions)

class plane_thread(QtCore.QThread):

    def __init__(self, application_delegate):
        super().__init__()
        self._md = application_delegate.mouvment_delegate
        self._fd = application_delegate.focus_delegate
        self.laser_delegate = application_delegate.laser_delegate
        self.checkid = None
        
        
    def settings(self, stage, laser_intensity, XYpos, start, stop, step, Nloops):
        self.focus_intensity = laser_intensity
        
        XYpos = np.asarray(XYpos)
        self._pos = np.zeros((len(XYpos), 3))
        self._pos[:, :2] = XYpos
        
        self._stage = stage
        self.range = (start, stop, step)
        self.Nloops = Nloops

    def run(self):
        positions = np.zeros((len(self._pos), 3))
        for i, corner in enumerate(self._pos):
            corner[2] = self.range[0]
            self._stage.goto_position(corner, speed=1000, wait=True,
                                          checkid=self.checkid)
            self._fd.focus(0, self.range[1] - self.range[0], self.range[2],
                           Nloops=self.Nloops,
                           stage=self._stage,
                           intensity=self.focus_intensity,
                           wait=True, checkid=self.checkid)
            
            self.focus_intensity = self.laser_delegate.get_intensity()

            positions[i] = self._stage.get_position(raw=True)

        corrections = self._stage.corrections
        offset, rotation_angles = solve_z(
            positions, offset=corrections["offset"],
            rotation_angles=corrections["rotation angles"])
        corrections["offset"] = offset
        corrections["rotation angles"] = rotation_angles
        self._stage.corrections = corrections