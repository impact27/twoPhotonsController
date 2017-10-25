# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 18:29:57 2017

@author: quentinpeter
"""
import cv2
import numpy as np

import registrator.image as ir


class XYcorrector():

    def __init__(self, motor, camera):
        self._refim = None
        self.motor = motor
        self.camera = camera

    def align(self, wait=True, checkid=None):
        """Use camera to align current image with ref image
        """
        if self._refim is None:
            # Save new reference image
            self._refim = self.camera.get_image()
        else:
            # Move
            self.motor.move_by(self.getOffset(), wait=wait, checkid=checkid)

    def getOffset(self):
        """Get offset between reference and current image
        """
        if self._refim is None:
            # No ref = no offset
            return np.zeros(3)
        # Blur images to get rid of noise
        curim = self.camera.get_image()
        refim = cv2.GaussianBlur(self._refim, (11, 11), 0)
        curim = cv2.GaussianBlur(curim, (11, 11), 0)
        # Get offset in um
        dy, dx = ir.find_shift_cc(refim, curim)
        dX = np.multiply([dx, dy, 0], self.camera.pixelSize)
        return dX



