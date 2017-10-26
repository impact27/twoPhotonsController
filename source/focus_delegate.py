# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 17:25:10 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets
import numpy as np

class Focus_delegate(QtCore.QObject):
    
    updatelist = QtCore.pyqtSignal(list)
    
    def __init__(self, app_delegate):
        super().__init__()
        self._positions = []
        self.md = app_delegate.mouvment_delegate
        self.canvas = app_delegate.imageCanvas
        self._zcorrector = Zcorrector(self.md.motor,
                                      app_delegate.camera_delegate,
                                      self.canvas)
        
    def delete_pos(self, idx):
        del self._positions[idx]
        self._update()
    
    def display_pos(self, idx):
        self.canvas.plotZCorr(*self._positions[idx]["graphs"])
    
    def focus(self, pos_range):
        graphs = self._zcorrector.focus(pos_range, checkid=self.md.lock())
        self.md.unlock()
        self._positions.append({
                "Xs": self.md.motor.get_position(raw=True),
                "graphs": graphs})
        self._update()
    
    def save(self):
        fn = QtWidgets.QFileDialog.getSaveFileName(
            self.canvas, 'TXT file', QtCore.QDir.homePath(),
            "Text (*.txt)")[0]
        with open(fn, 'bw') as f:
            for pos in self._positions:
                f.write((str(pos["Xs"]) + '\n').encode())
                np.savetxt(f, pos["graphs"])
                
    
    def clear(self):
        self._positions = []
        self._update()
    
    def _update(self):
        ret = []
        for pos in self._positions:
            ret.append(self.md.motor.XstoXm(pos["Xs"]))
        self.updatelist.emit(ret)



class Zcorrector():

    def __init__(self, motor, camera, imageCanvas):
        super().__init__()
        self.motor = motor
        self.camera = camera
        self.error = None
        self._empty_im = np.zeros_like(self.camera.get_image())
        self.lockid = None
        self.ic = imageCanvas

    def get_image_range(self, zPos, condition=None):
        """get the images corresponding to the positions in zPos

        condition gives the stop value
        """
        imrange = np.tile(self._empty_im, (len(zPos), 1, 1))

        if condition is None:
            def condition(a, b): return False

        for im, z in zip(imrange, zPos):
            self.motor.goto_position([np.nan, np.nan, z],
                                     wait=True, checkid=self.lockid)
            im[:] = self.camera.get_image()
            if condition(im, imrange):
                return imrange
        return imrange

    def startlaser(self):
        self.camera.autoShutter(False)
        self._camshutter = self.camera.shutter
        self.camera.set_shutter(self.camera.shutter_range()[0])
#         self.laser.open_shutter()

    def endlaser(self):
        self.camera.shutter = self._camshutter
#         self.laser.close_shutter()

    def focus(self, ZRange, Npass=3, checkid=None):
        """ Go to the best focal point for the laser
        """
        self.lockid = checkid

        def get_spot_sizes(imrange):
            return np.sum(imrange >=
                          np.reshape(np.max(imrange, (1, 2)) / 10, (-1, 1, 1)),
                          (1, 2))

        def max_condition(im, ims):
            return np.max(im) < np.max(ims) / 2

        self.startlaser()

        Z = self.motor.position[2]
        zrange = [Z - ZRange / 2, Z + ZRange / 2]
        Zs = []
        Is = []
        Ss = []
        for i in range(Npass):
            zPos = np.linspace(*zrange, 21)
            imrange = self.get_image_range(zPos, max_condition)

            intensity = np.max(imrange, (1, 2))
            argbest = np.argmax(intensity)

            if argbest == 0:
                zrange = [zPos[argbest], zPos[argbest + 1]]
            elif argbest == len(intensity) - 1:
                zrange = [zPos[argbest - 1], zPos[argbest]]
            else:
                zrange = [zPos[argbest - 1], zPos[argbest + 1]]

            if i > 0:
                size = get_spot_sizes(imrange)
                Zs.extend(zPos)
                Is.extend(intensity)
                Ss.extend(size)
                try:
                    self.ic.plotZCorr(zPos, intensity, size)
                except BaseException as error:
                    print("Can't Plot!!!", error.args[0])

        self.motor.goto_position([np.nan, np.nan, zPos[argbest]],
                                 wait=True, checkid=self.lockid)

        self.endlaser()
        # save result and position
        return np.asarray([Zs, Ss, Is])