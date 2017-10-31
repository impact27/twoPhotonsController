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
        self.thread = zThread(self.md, app_delegate.camera_delegate,
                              app_delegate.laser_delegate,
                              self.canvas, self.addGraph)
        
    def delete_pos(self, idx):
        del self._positions[idx]
        self._update()
    
    def display_pos(self, idx):
        self.canvas.plotZCorr(*self._positions[idx]["graphs"])
    
    def focus(self, back, forth, step):
        self.thread.set_pos_range(back, forth, step)
        self.thread.start()
        
    def addGraph(self, graphs):
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
        
    def ESTOP(self):
        self.thread.terminate()


class zThread(QtCore.QThread):

    def __init__(self, md, camera, laser, canvas, addGraph):
        super().__init__()
        self._zcorrector = Zcorrector(md.motor, camera, laser, canvas)
        self.addGraph = addGraph
        self._back = 0
        self._forth = 0
        self._step = 0
        self._md = md

    def set_pos_range(self, back, forth, step):
        self._back = back
        self._forth = forth
        self._step = step
        
    def run(self):
        lockid = self._md.lock()
        if lockid is None:
            self.error = "Unable to lock the mouvment"
            return
        graphs = self._zcorrector.focus(self._back, self._forth, self._step,
                                        checkid=lockid)
        self._md.unlock()

        self.addGraph(graphs)

class Zcorrector():

    def __init__(self, motor, camera, laser, imageCanvas=None):
        super().__init__()
        self.motor = motor
        self.camera = camera
        self.error = None
        self.lockid = None
        self.ic = imageCanvas

#    @profile
    def get_image_range(self, zPos):
        """get the images corresponding to the positions in zPos

        condition gives the stop value
        """
        intensities = np.zeros(len(zPos))
        sizes = np.zeros(len(zPos))



        for i, z in enumerate(zPos):
            self.motor.goto_position([np.nan, np.nan, z],
                                     wait=True, checkid=self.lockid)
            im = self.camera.get_image()
            mymax = np.amax(im)
            size = np.sum(im>mymax/10)
            intensities[i] = mymax
            sizes[i] = size
            if mymax < np.max(intensities)/2:
                return intensities, sizes
        return  intensities, size

    def startlaser(self):
        self.camera.auto_exposure_time(False)
        self._cam_exposure_time = self.camera.exposure_time
        self.camera.set_exposure_time(self.camera.exposure_time_range()[0])
#         self.laser.open_shutter()

    def endlaser(self):
        self.camera.exposure_time = self._cam_exposure_time
#         self.laser.close_shutter()

    def focus(self, back, forth, step, checkid=None):
        """ Go to the best focal point for the laser
        """
        self.lockid = checkid
        self.startlaser()

        Z = self.motor.position[2]
        zrange = [Z + back, Z + forth]
        zPos = np.arange(*zrange, step)

        for i in range(2):
            
            intensity, sizes = self.get_image_range(zPos)
            argbest = np.argmax(intensity)
            if intensity[argbest] == 255:
                argbest = np.argmin(sizes)

            if i == 0:
                if argbest == 0:
                    zPos = np.linspace(zPos[0], zPos[1], 11)
                elif argbest == len(intensity) - 1:
                    zPos = np.linspace(zPos[-2], zPos[-1], 11)
                else:
                    zPos = np.linspace(zPos[argbest-1], zPos[argbest+1], 21)
                
        self.endlaser()
        
        Y = intensity
        if intensity[argbest] == 255:
            Y = sizes
        close = np.abs(zPos-zPos[argbest]) < step/2
        fit = np.polyfit(zPos[close], Y[close], 2)
        zBest = -fit[1]/(2*fit[0])
        
        ret = np.asarray([zPos, intensity, sizes]), fit
        
        if self.ic is not None:
            self.ic.plotZCorr(*ret)
        
        self.motor.goto_position([np.nan, np.nan, zBest],
                                 wait=True, checkid=self.lockid)
        
        

        # save result and position
        return ret