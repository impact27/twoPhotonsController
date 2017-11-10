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
        self.app_delegate = app_delegate
        self.md = app_delegate.mouvment_delegate
        self.canvas = app_delegate.canvas_delegate._canvas
        self.thread = zThread(self.md, app_delegate.camera_delegate,
                              app_delegate.laser_delegate,
                              self.canvas, self.addGraph)
        
    def delete_pos(self, idx):
        del self._positions[idx]
        self._update()
    
    def display_pos(self, idx):
        self.app_delegate.canvas_delegate.switch_live(False)
        self.app_delegate.canvas_delegate.switch_draw(False)
        self.canvas.plotZCorr(*self._positions[idx]["graphs"])
    
    def focus(self, back, forth, step, precise=True):
        self.thread.set_pos_range(back, forth, step, precise)
        self.thread.start()
        
    def addGraph(self, graphs):
        self._positions.append({
                "Xs": self.md.motor.get_position(raw=True),
                "graphs": graphs})
        self._update()
    
    def save(self):
        fn = QtWidgets.QFileDialog.getSaveFileName(
            QtWidgets.QApplication.topLevelWidgets()[0], 'TXT file', 
            QtCore.QDir.homePath(), "Text (*.txt)")[0]
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

    def set_pos_range(self, back, forth, step, precise):
        self._back = back
        self._forth = forth
        self._step = step
        self._precise = precise
        
    def run(self):
        lockid = self._md.lock()
        if lockid is None:
            self.error = "Unable to lock the mouvment"
            return
        graphs = self._zcorrector.focus(self._back, self._forth, self._step,
                                        checkid=lockid, precise=self._precise)
        self._md.unlock()

        self.addGraph(graphs)

class Zcorrector():

    def __init__(self, motor, camera, laser, canvas=None):
        super().__init__()
        self.motor = motor
        self.camera = camera
        self.error = None
        self.lockid = None
        self.canvas = canvas

    def get_image_range(self, start, stop, step):
        """get the images corresponding to the positions in zPos

        condition gives the stop value
        """
        zPos = np.arange(start, stop, step)
        intensities = np.zeros(len(zPos))
        sizes = np.zeros(len(zPos))

        for i, z in enumerate(zPos):
            self.motor.goto_position([np.nan, np.nan, z],
                                     wait=True, checkid=self.lockid)
            self.camera.get_image()
            im = self.camera.get_image()
            mymax = np.amax(im)
            size = np.sum(im>mymax/10)
            intensities[i] = mymax
            sizes[i] = size
            if mymax < np.max(intensities)/2:
                return zPos, intensities, sizes
             
        return zPos, intensities, sizes

    def startlaser(self):
        self.camera.auto_exposure_time(False)
        self._cam_exposure_time = self.camera.exposure_time
        self.camera.set_exposure_time(self.camera.exposure_time_range()[0])
#         self.laser.open_shutter()

    def endlaser(self):
        self.camera.exposure_time = self._cam_exposure_time
#         self.laser.close_shutter()

    def focus(self, back, forth, step, checkid=None, precise=True):
        """ Go to the best focal point for the laser
        """
        self.lockid = checkid
        self.startlaser()

        Z = self.motor.position[2]
        z_start = Z + back
        z_stop = Z + forth
        
        current_step = step
        
        list_zpos = []
        list_int = []
        list_sizes = []

        for i in range(2):
#            if precise:
            zPos, intensity, sizes = self.get_image_range(
                        z_start, z_stop, current_step)
#            else:
#                zPos, intensity, sizes = self.get_image_range_quick(
#                        z_start, z_stop, current_step)  
            
            argbest = np.argmax(intensity)
            
            if intensity[argbest] == 255:
                argbest = (np.argwhere(intensity == 255)
                    [np.argmin(sizes[intensity == 255])][0])
                
            current_step /=10
            
            if argbest == 0:
                z_start = zPos[0]
            else:
                z_start = zPos[argbest-1]
                
            if argbest == len(intensity) - 1:
                z_stop = zPos[argbest]
            else:
                z_stop = zPos[argbest+1]
            
            list_zpos.append(zPos)
            list_int.append(intensity)
            list_sizes.append(sizes)
                
        self.endlaser()
        
        Y = intensity
        if intensity[argbest] == 255:
            Y = sizes
            
        close = np.abs(zPos-zPos[argbest]) < step/2
        fit = np.polyfit(zPos[close], Y[close], 2)
        zBest = -fit[1]/(2*fit[0])
        
        ret = np.asarray([list_zpos, list_int, list_sizes]), fit
        
        if self.canvas is not None:
            self.canvas.plotZCorr(*ret)
        
        self.motor.goto_position([np.nan, np.nan, zBest],
                                 wait=True, checkid=self.lockid)
        
        

        # save result and position
        return ret

    def get_image_range_quick(self, start, stop, step):
        
        
        #Move to start
        self.motor.goto_position([np.nan, np.nan, start],
                                     wait=True, checkid=self.lockid)
        
        z_array = [self.motor.position[2]]
        intensities = []
        sizes = []
        
        #Compute speed assuming 5fps
        speed = step*5
        
        #Move to finish with small speed
        self.motor.goto_position([np.nan, np.nan, stop], speed=speed,
                                     wait=False, checkid=self.lockid)
        #while not finished, record position and intensity
        stop = False
        while not stop:
            im = self.camera.get_image()
            mymax = np.amax(im)
            size = np.sum(im>mymax/10)
            intensities.append(mymax)
            sizes.append(size)
            z_array.append(self.motor.position[2])
            #Stop if condition met
            if mymax < np.max(intensities)/2:
                self.motor.stop(True, checkid=self.lockid)
                stop = True
            if self.motor.is_onTarget():
                stop =True
        
        z_array = np.asarray(z_array)
        z_array = z_array[:-1] + np.diff(z_array)/2
        
        return z_array, np.asarray(intensities), np.asarray(sizes)
        
            
        
        