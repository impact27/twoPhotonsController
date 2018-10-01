# -*- coding: utf-8 -*-
import unittest
import numpy as np
import sys
sys.path.append('../..')

if sys.platform == "darwin":
    from controllers.laser_controller_placeholder import Laser_controller
else:
    from controllers.laser_controller import Laser_controller


class Test_Camera(unittest.TestCase):
    def setUp(self):
        self.laser = Laser_controller()

    def test_intensity(self):
        self.laser.intensity = 0.1
        self.assertTrue(np.abs(
            self.laser.intensity - 0.1) < 1e-5)
        self.laser.intensity = 0

    def test_reconnect(self):
        self.laser.disconnect()
        self.assertFalse(self.laser.isConnected())

        self.laser.connect()
        self.assertTrue(np.abs(
            self.laser.intensity - 0) < 1e-5)


if __name__ == '__main__':
    unittest.main()
