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
        

if __name__ == '__main__':
    unittest.main()