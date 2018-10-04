# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 17:25:10 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets
import numpy as np
import sys
import time
from delegates.thread import lockmutex
from errors import FocusError
V_MIN = 0.01
V_VERY_SMALL = 1e-4
INTENSITY_MAX = 255
DECREASE_FACTOR = 0.8
INCREASE_FACTOR = 1.2
STOP_FRACTION = 1/3
MIN_DIFF = 0.8
MIN_RADIUS_REFINE = 3
MIN_PEAK_INTENSITY = 150

class Focus_delegate(QtCore.QObject):

    updatelist = QtCore.pyqtSignal(list)
    update_settings = QtCore.pyqtSignal(dict)

    def __init__(self, app_delegate):
        super().__init__()
        self._mutex = QtCore.QMutex(QtCore.QMutex.Recursive)
        self._positions = []
        self.app_delegate = app_delegate
        self.md = app_delegate.movement_delegate
        self.canvas = app_delegate.canvas_delegate
        self.app_delegate = app_delegate
        self.init_thread()
        self._settings = {
            "From": 15,
            "To": -15,
            "Step": -0.5,
            "NLoops": 1,
            "Intensity": 0.1
        }
        self._last_result = None
        self.md.motor.coordinatesCorrected.connect(lambda x: self._update())
        self.md.piezo.coordinatesCorrected.connect(lambda x: self._update())

    def init_thread(self):
        self.thread = ZThread(self.md,
                              self.app_delegate.camera_delegate,
                              self.app_delegate.laser_delegate,
                              self.addGraph)

    @lockmutex
    def delete_pos(self, idx):
        del self._positions[idx]
        self._update()

    @lockmutex
    def display_pos(self, idx):
        self.app_delegate.canvas_delegate.switch_live(False)
        self.app_delegate.canvas_delegate.switch_draw(False)
        self.plotZCorr(*self._positions[idx]["focus_result"])

    @lockmutex
    def plotZCorr(self, data, zBest, success):
        try:
            if success:
                c = None
            else:
                c = 'red'
            list_Z, list_I = data
            self.canvas.clear()
            for Z, I in zip(list_Z, list_I):
                self.canvas.plot(Z, I, 'x', c=c)
            self.canvas.plot(zBest * np.ones(2), self.canvas.get_ylim(), 'k-')
            self.canvas.draw()
        except BaseException:
            print("Can't Plot!!!", sys.exc_info()[0])
            raise

    def focus(self, stage, *, start_offset=None, stop_offset=None, step=None,
              intensity=None, Nloops=None,
              wait=False, checkid=None, change_coordinates=True):
        """
        start_offset:
            How far back from current position
        stop_offset:
            How far forth from surrent position
        step:
            Step size
        Nloops default 1:
            Each loop has a 10X smaller step size.
        wait default False:
            Should the thread wait for completion
        """
       
        if self.thread.isRunning():
            raise FocusError('Already Focusing')
        
        self._mutex.lock()
        self._last_result = None

        if intensity is not None:
            self._settings["Intensity"] = intensity
        if start_offset is not None:
            self._settings["From"] = start_offset
        if stop_offset is not None:
            self._settings["To"] = stop_offset
        if step is not None:
            self._settings["Step"] = step
        if Nloops is not None:
            self._settings["NLoops"] = Nloops

        self.update_settings.emit(self._settings)
        self.thread.set_args(
            self._settings,
            stage,
            checkid,
            change_coordinates)
        self.thread.start()
        self._mutex.unlock()
        if wait:
            self.thread.wait()

    def get_result(self):
        if self.thread.isRunning():
            self.thread.wait()
        if self._last_result is None:
            raise FocusError("No result to show, check focus is not running")
        return self._last_result

    @lockmutex
    def addGraph(self, data, z_best, success):
        self._last_result = data, z_best, success
        if not success:
            self.app_delegate.error.emit("Focus Failed")
        else:
            intensity = self.app_delegate.laser_delegate.get_intensity()
            if np.abs(intensity - self._settings["Intensity"]) > 1e-3:
                self._settings["Intensity"] = intensity
                self.update_settings.emit(self._settings)

        self._positions.append({
            "motor_Xs": self.md.motor.get_position(raw=True),
            "piezo_Xs": self.md.piezo.get_position(raw=True),
            "focus_result": (data, z_best, success),
            "intensity": self.app_delegate.laser_delegate.get_intensity(),
            "time": time.time()
        })
        self._update()

    @lockmutex
    def save(self):
        fn = QtWidgets.QFileDialog.getSaveFileName(
            QtWidgets.QApplication.topLevelWidgets()[0], 'TXT file',
            QtCore.QDir.homePath(), "Text (*.txt)")[0]
        with open(fn, 'bw') as f:
            for pos in self._positions:
                f.write((str(pos["motor_Xs"]) + '\n').encode())
                data = pos["focus_result"][0]
                for scan_idx in range(data.shape[1]):
                    f.write(('{} pass:\n').format(scan_idx).encode())
                    for line in data[:, scan_idx]:
                        np.savetxt(f, line[np.newaxis])
                f.write(('Best: {}\nIntensity: {}\n').format(
                            pos["focus_result"][1],
                            pos["intensity"]
                        ).encode())
        with open(fn[:-4] + '_times.txt', 'w') as f:
            for pos in self._positions:
                f.write("{time}, {position_motor}, {position_piezo}\n".format(
                        time=pos["time"], position_motor=pos["motor_Xs"],
                        position_piezo=pos["piezo_Xs"]))

    @lockmutex
    def clear(self):
        self._positions = []
        self._update()

    @lockmutex
    def _update(self):
        ret = []
        for pos in self._positions:
            ret.append((self.md.motor.XstoXm(
                pos["motor_Xs"]), self.md.piezo.XstoXm(pos["piezo_Xs"])))
        self.updatelist.emit(ret)

    @lockmutex
    def ESTOP(self):
        self.thread.terminate()
        self.init_thread()

    def set_intensity(self, intensity):
        self._settings["Intensity"] = intensity


class ZThread(QtCore.QThread):

    def __init__(self, movement_delegate, camera, laser, callback):
        super().__init__()
        self.callback = callback
        self._zcorrector = Zcorrector(None, camera, laser)
        self._settings = None
        self._checkid = None
        self._md = movement_delegate

    def set_args(self, settings, stage, checkid, change_coordinates):
        self._zcorrector.stage = stage
        self._settings = settings
        self._checkid = checkid
        self._change_coordinates = change_coordinates

    def run(self):
        if self._settings is None:
            raise FocusError("Settings not initialised!")

        if self._checkid is None:
            lockid = self._md.lock()
            if lockid is None:
                self.error = "Unable to lock the movement"
                return
        else:
            lockid = self._checkid

        data, z_best, success = self._zcorrector.focus(
            self._settings, checkid=lockid,
            change_coordinates=self._change_coordinates)
        self._md.unlock()
        self._settings = None
        self.callback(data, z_best, success)


class Zcorrector():

    def __init__(self, stage, camera, laser):
        super().__init__()
        self.stage = stage
        self.camera = camera
        self.lockid = None
        self.laser = laser

    def change_power(self, factor=DECREASE_FACTOR):
        """Change intensity of laser to get best focus"""
        V = self.laser.get_intensity() * factor
        if factor > 1 and V < V_VERY_SMALL:
            V = V_MIN
        self.laser.set_intensity(V)

    def startlaser(self, intensity):
        """Start laser with intensity"""
        if intensity is None or intensity < V_VERY_SMALL:
            intensity = V_MIN
        self.camera.auto_exposure_time(False)
        self.camera.set_exposure_time(self.camera.exposure_time_range()[0])
        self.laser.set_intensity(intensity)
        self.camera.extShutter(True)

    def endlaser(self):
        """Stop laser"""
        pass

    def get_intensity(self):
        """get intensity from camera"""
        self.camera.restart_streaming()
        im = self.camera.get_image()
        mymax = np.amax(im)
        return mymax

    def get_intensity_range(self, start, stop, step):
        """get the images corresponding to the positions in zPos
        """
        zPos = np.arange(start, stop, step)
        data = np.zeros((len(zPos), 2))
        data[:, 0] = zPos

        for i, z in enumerate(zPos):
            self.stage.goto_position([np.nan, np.nan, z],
                                     wait=True, checkid=self.lockid, isRaw=True)

            intensity = self.get_intensity()

            data[i, 1] = intensity

            if intensity == INTENSITY_MAX:
                if i > 1:
                    start = zPos[i - 2]
                self.change_power(DECREASE_FACTOR)
                return self.get_intensity_range(start, stop, step)

            if intensity < np.max(data[:, 1]) * STOP_FRACTION:

                return data[:i + 1]

        return data

    def focus_range(self, z_start, z_stop, current_step):
        data = self.get_intensity_range(
            z_start, z_stop, current_step)

        # Failed focus
        if np.min(data[:, 1]) > MIN_DIFF * np.max(data[:, 1]):
            return data, False

        argbest = np.argmax(data[..., 1])
        zBest = data[..., 0][argbest]

        # If on side
        if argbest == 0 or argbest == len(data) - 1:
            return self.redo_around_max(zBest, current_step)

        # Check intensity is high enough
        if np.max(data[..., 1]) < MIN_PEAK_INTENSITY:

            self.stage.goto_position([np.nan, np.nan, zBest],
                                     wait=True, checkid=self.lockid, isRaw=True)

            intensity = self.get_intensity()
            #Check intensity CAN be increased
            i = 0
            N_max = 40
            while intensity < MIN_PEAK_INTENSITY and i < N_max:
                self.change_power(INCREASE_FACTOR)
                intensity = self.get_intensity()
                
            if i == N_max:
                print("Couldn't raise intensity to acceptable level")
                return data, False
            else:
                return self.redo_around_max(zBest, current_step)

        return data, True

    def redo_around_max(self, zBest, current_step):
        distance = np.max(np.abs([3.1 * current_step, MIN_RADIUS_REFINE]))
        distance *= np.sign(current_step)
        return self.focus_range(
            zBest - distance,
            zBest + distance,
            current_step)
        
    def focus(self, settings, checkid=None, change_coordinates=True):
        """ Go to the best focal point for the laser
        """
        start_offset = settings["From"]
        stop_offset = settings["To"]
        step = settings["Step"]
        N_loops = settings["NLoops"]
        intensity = settings["Intensity"]

        self.lockid = checkid
        self.startlaser(intensity)

        Z = self.stage.get_position(raw=True)[2]
        z_start = Z + start_offset
        z_stop = Z + stop_offset

        current_step = float(step)

        list_zpos = []
        list_int = []

        for i in range(N_loops):
            data, success = self.focus_range(z_start, z_stop, current_step)

            zPos, intensities = data.T
            list_zpos.append(zPos)
            list_int.append(intensities)

            if not success:
                return np.asarray([list_zpos, list_int]), np.nan, False

            argbest = np.argmax(intensities)
            current_step /= 10
            z_start = zPos[argbest - 1]
            z_stop = zPos[argbest + 1]

        self.endlaser()

        Y = intensities

        close = intensities > .8 * intensities.max()
        if np.sum(close) < 4:
            close = np.abs(zPos - zPos[argbest]) < 1.5 * np.abs(step)
        fit = np.polyfit(zPos[close], Y[close], 2)
        zBest = -fit[1] / (2 * fit[0])
        if np.abs(zBest - zPos[argbest]) > 2 * np.abs(step):
            zBest = zPos[argbest]

        self.stage.goto_position([np.nan, np.nan, zBest],
                                 wait=True, checkid=self.lockid, isRaw=True)

        if change_coordinates:
            self.stage.set_Z_zero()

        # save result and position
        return np.asarray([list_zpos, list_int]), zBest, True

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
