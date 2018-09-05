# -*- coding: utf-8 -*-
import unittest
import numpy as np
import sys
sys.path.append('../..')

if sys.platform == "darwin":
    from controllers.camera_controller_placeholder import Camera_controller
else:
    from controllers.camera_controller import Camera_controller

class Test_Camera(unittest.TestCase):
    def setUp(self):
        self.cam = Camera_controller()

    def test_roi(self):
        roi = self.cam.roi
        self.cam.roi = [1, 1, 11, 11]
        self.assertTrue(np.all(self.cam.roi == [1, 1, 11, 11]))
        self.cam.roi_reset()
        self.assertTrue(np.all(self.cam.roi == roi))
        
    def test_grab(self):
        im = self.cam.get_image()
        self.assertTrue(np.all(im.shape == self.cam.roi[2:][::-1]))
        
    def test_exposure_time(self):
        self.cam.exposure_time = 1e-2
        self.assertTrue(self.cam.exposure_time == 1e-2)
        
    def test_reconnect(self):
        roi = self.cam.roi
        self.cam.disconnect()
        self.assertFalse(self.cam.isConnected())
        self.cam.connect()
        self.assertTrue(np.all(self.cam.roi == roi))
        
if __name__ == '__main__':
    unittest.main()