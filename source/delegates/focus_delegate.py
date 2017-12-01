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
                              self.addGraph)
        
    def delete_pos(self, idx):
        del self._positions[idx]
        self._update()
    
    def display_pos(self, idx):
        self.app_delegate.canvas_delegate.switch_live(False)
        self.app_delegate.canvas_delegate.switch_draw(False)
        self.canvas.plotZCorr(*self._positions[idx]["graphs"])
    

    def focus(self, back, forth, step, intensity, Nloops=1, *, 
              piezzo=False, wait=False, checkid=None):
        """
        back:
            How far back from current position
        forth:
            How far forth from surrent position
        step:
            Step size
        Nloops default 1:
            Each loop has a 10X smaller step size.
        piezzo default False:
            SHould the piezzo be used
        wait default False:
            Should the thread wait for completion
        """
        if intensity is None:
            intensity = self.app_delegate.laser_delegate.get_intensity()
        if piezzo:
            stage = self.md.piezzo
        else:
            stage = self.md.motor
        self.thread.set_args(back, forth, step, Nloops, stage, intensity, checkid)
        self.thread.start()
        
        if wait:
            self.thread.wait()
        
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
                data = pos["graphs"][0]
                for scan_idx in range(data.shape[1]):
                    f.write(('{} pass:\n').format(scan_idx).encode())
                    for line in data[:, scan_idx]:
                       np.savetxt(f, line)
                f.write(('Best: {}\n').format(pos["graphs"][1]).encode())
                
    
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

    def __init__(self, mouvment_delegate, camera, laser, addGraph):
        super().__init__()
        self.addGraph = addGraph
        self._zcorrector = Zcorrector(None, camera, laser)
        self._focus_args = None
        self._md = mouvment_delegate
        
    def set_args(self, back, forth, step, Nloops, stage, intensity, checkid):
        self._zcorrector.stage = stage
        self._focus_args = (back, forth, step, Nloops, intensity, checkid)
        
    def run(self):
        if self._focus_args is None:
            raise RuntimeError("args not initialised!")
            
        if self._focus_args[-1] is None:
            lockid = self._md.lock()
            if lockid is None:
                self.error = "Unable to lock the mouvment"
                return
        else:
            lockid = self._focus_args[-1]
       
        
        graphs = self._zcorrector.focus(*self._focus_args[:-1], lockid)
        self._md.unlock()
        self._focus_args = None
        self.addGraph(graphs)

class Zcorrector():

    def __init__(self, stage, camera, laser):
        super().__init__()
        self.stage = stage
        self.camera = camera
        self.lockid = None
        self.laser = laser
    
    def decrease_power(self):
        V = self.laser.get_intensity()
        V = 0.8*V
        self.laser.set_intensity(V)
        
    def startlaser(self, intensity):
        self.camera.auto_exposure_time(False)
        self.camera.set_exposure_time(self.camera.exposure_time_range()[0])
        self.laser.set_intensity(intensity)
        self.laser.switch(True)
        self.camera.extShutter(True)
#         self.laser.open_shutter()

    def endlaser(self):
        pass

    def get_image_range(self, start, stop, step):
        """get the images corresponding to the positions in zPos

        condition gives the stop value
        """
        zPos = np.arange(start, stop, step)
        intensities = np.zeros(len(zPos))
        sizes = np.zeros(len(zPos))

        for i, z in enumerate(zPos):
            self.stage.goto_position([np.nan, np.nan, z],
                                     wait=True, checkid=self.lockid, isRaw=True)
            self.camera.restart_streaming()
            im = self.camera.get_image()
            mymax = np.amax(im)
            size = np.sum(im>mymax/10)
            intensities[i] = mymax
            sizes[i] = size
            if mymax == 255:
                if i > 1:
                    start = zPos[i-2]
                self.decrease_power()
                return self.get_image_range(start, stop, step)
            
            if mymax < np.max(intensities)/3:
                return zPos, intensities, sizes
             
        return zPos, intensities, sizes

    def focus(self, back, forth, step, N_loops=1, intensity=None, checkid=None):
        """ Go to the best focal point for the laser
        """
        self.lockid = checkid
        self.startlaser(intensity)

        Z = self.stage.get_position(raw=True)[2]
        z_start = Z + back
        z_stop = Z + forth
        
        current_step = step
        
        list_zpos = []
        list_int = []
        list_sizes = []

        for i in range(N_loops):

            zPos, intensity, sizes = self.get_image_range(
                        z_start, z_stop, current_step)

            
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
            
        
        close = intensity > .8*intensity.max()
        if np.sum(close) < 4:
            close = np.abs(zPos-zPos[argbest]) < 1.5*step
        fit = np.polyfit(zPos[close], Y[close], 2)
        zBest = -fit[1]/(2*fit[0])
        if np.abs(zBest - zPos[argbest]) > 2*step:
            zBest = zPos[argbest]
        
        ret = np.asarray([list_zpos, list_int, list_sizes]), zBest
            
        self.stage.goto_position([np.nan, np.nan, zBest],
                                 wait=True, checkid=self.lockid, isRaw=True)
        
        self.stage.set_raw_Z_zero(zBest)
        
        # save result and position
        return ret

#    def get_image_range_quick(self, start, stop, step):
#        
#        
#        #Move to start
#        self.motor.goto_position([np.nan, np.nan, start],
#                                     wait=True, checkid=self.lockid)
#        
#        z_array = [self.motor.position[2]]
#        intensities = []
#        sizes = []
#        
#        #Compute speed assuming 5fps
#        speed = step*5
#        
#        #Move to finish with small speed
#        self.motor.goto_position([np.nan, np.nan, stop], speed=speed,
#                                     wait=False, checkid=self.lockid)
#        #while not finished, record position and intensity
#        stop = False
#        while not stop:
#            im = self.camera.get_image()
#            mymax = np.amax(im)
#            size = np.sum(im>mymax/10)
#            intensities.append(mymax)
#            sizes.append(size)
#            z_array.append(self.motor.position[2])
#            #Stop if condition met
#            if mymax < np.max(intensities)/2:
#                self.motor.stop(True, checkid=self.lockid)
#                stop = True
#            if self.motor.is_onTarget():
#                stop =True
#        
#        z_array = np.asarray(z_array)
#        z_array = z_array[:-1] + np.diff(z_array)/2
#        
#        return z_array, np.asarray(intensities), np.asarray(sizes)
#        
            
        
        