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
    def __init__(self):
        self.cam = Camera_controller()

    def test_roi(self):
        roi = self.cam.roi
        self.cam.roi_zoom([1, 1, 11, 11])
        new_roi = [roi[0] + 1, roi[1] + 1, roi[0] + 11, roi[1] + 11]
        self.assertTrue(np.all(self.cam.roi == new_roi))
        self.cam.roi_reset()
        self.assertTrue(np.all(self.cam.roi == roi))
        

if __name__ == '__main__':
    unittest.main()