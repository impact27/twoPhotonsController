# -*- coding: utf-8 -*-
import unittest
import numpy as np
import sys
import time
sys.path.append('../..')

# If I am on my mac, the stages are not connected
if sys.platform == "darwin":
    from controllers.stage_controller_placeholder import (Linear_controller,
                                                          Cube_controller,
                                                          z_controller)
else:
    from controllers.stage_controller import (Linear_controller,
                                              Cube_controller,
                                              z_controller)

class Test_Linear(unittest.TestCase):
    def setUp(self):
        self.stage = Linear_controller()

    def test_move(self):
        pos = self.stage.get_position()
        self.stage.MOVVEL(pos+1, [10, 10])
        time.sleep(1)
        self.stage.waitEndMotion()
        self.assertTrue(
                np.all(np.abs(self.stage.get_position() - (pos + 1)) < 1e-1))
        
    def test_reconnect(self):
        self.stage.waitEndMotion()
        pos = self.stage.get_position()
        self.stage.disconnect()
        self.assertFalse(self.stage.connected())
        self.stage.connect()
        self.assertTrue(
                np.all(np.abs(self.stage.get_position() - (pos)) < 1e-1))
        
    def test_onTarget(self):
        self.stage.MOVVEL([25000, 25000], [1000, 1000])
        self.stage.waitEndMotion()
        self.assertTrue(self.stage.is_onTarget())
        self.stage.MOVVEL([25001, 25001], [1, 1])
        self.assertFalse(self.stage.is_onTarget())
        time.sleep(1)
        self.stage.waitEndMotion()
        
    def test_STOP(self):
        self.stage.MOVVEL([25000, 25000], [1000, 1000])
        self.stage.waitEndMotion()
        self.assertTrue(self.stage.is_onTarget())
        self.stage.MOVVEL([25005, 25005], [1, 1])
        self.assertTrue(self.stage.is_moving())
        self.stage.stop()
        self.assertFalse(self.stage.is_moving())
        
    def test_ESTOP(self):
        self.stage.MOVVEL([25000, 25000], [1000, 1000])
        self.stage.waitEndMotion()
        self.assertTrue(self.stage.is_onTarget())
        self.stage.MOVVEL([25005, 25005], [1, 1])
        self.assertTrue(self.stage.is_moving())
        self.stage.ESTOP()
        self.assertFalse(self.stage.is_moving())
        
class Test_cube(unittest.TestCase):
    def setUp(self):
        self.stage = Cube_controller()

    def test_move(self):
        pos = self.stage.get_position()
        self.stage.MOVVEL(pos+1, [10, 10, 10])
        time.sleep(1)
        self.stage.waitEndMotion(3)
        self.assertTrue(
                np.all(np.abs(self.stage.get_position() - (pos + 1)) < 1e-1))
        
    def test_reconnect(self):
        self.stage.waitEndMotion(3)
        self.stage.disconnect()
        self.assertFalse(self.stage.isConnected())
        self.stage.connect()
        self.stage.waitEndMotion(3)
        self.assertTrue(self.stage.isConnected())
        
    def test_onTarget(self):
        self.stage.MOVVEL([0, 0, 0], [1000, 1000, 1000])
        self.stage.waitEndMotion(3)
        self.assertTrue(self.stage.is_onTarget())
        self.stage.MOVVEL([5, 5, 5], [1, 1, 1])
        time.sleep(1) # Doesn't move right away
        self.assertTrue(self.stage.is_moving())
        self.assertFalse(self.stage.is_onTarget())
        time.sleep(1)
        self.stage.waitEndMotion(3)
        
    def test_STOP(self):
        self.stage.MOVVEL([0, 0, 0], [1000, 1000, 1000])
        self.stage.waitEndMotion(3)
        self.assertTrue(self.stage.is_onTarget())
        self.stage.MOVVEL([5, 5, 5], [1, 1, 1])
        time.sleep(1)
        self.assertTrue(self.stage.is_moving())
        self.stage.stop()
        self.assertFalse(self.stage.is_moving())
        
    def test_ESTOP(self):
        self.stage.MOVVEL([0, 0, 0], [1000, 1000, 1000])
        self.stage.waitEndMotion(3)
        self.assertTrue(self.stage.is_onTarget())
        self.stage.MOVVEL([5, 5, 5], [1, 1, 1])
        time.sleep(1)
        self.assertTrue(self.stage.is_moving())
        self.stage.ESTOP()
        self.assertFalse(self.stage.is_moving())
        
    def test_macro(self):
        self.stage.MOVVEL([20, 20, 20], [1000, 1000, 1000])
        self.stage.waitEndMotion(3)
        self.stage.MAC_BEG('test')
        self.stage.MOVVEL([10, 10, 10], [10, 10, 10])
        self.stage.macro_wait()
        self.stage.MOVVEL([0, 0, 0], [10, 10, 10])
        self.stage.macro_wait()
        self.stage.MAC_END()
        self.assertFalse(self.stage.is_macro_running())
        self.stage.MAC_START('test')
        time.sleep(0.1)
        self.assertTrue(self.stage.is_macro_running())
        self.assertTrue(self.stage.is_moving())
        time.sleep(3)
        self.assertFalse(self.stage.is_macro_running())
        self.assertFalse(self.stage.is_moving())
        self.stage.MAC_DEL('test')
        self.assertTrue(
                np.all(np.abs(self.stage.get_position() - ([0, 0, 0])) < 1e-1))
        
    def test_wave(self):
        self.stage.MOVVEL([0, 0, 0], [1000, 1000, 1000])
        self.stage.waitEndMotion(3)
        X = np.linspace(0, 20, 1000)
        X = np.repeat(X[:, np.newaxis], 3, axis=1)
        self.stage.run_waveform(1e-3, X)
        self.stage.waitEndMotion(3)
        self.assertTrue(
                np.all(np.abs(self.stage.get_position() - ([20, 20, 20])) < 1e-1))
        
        
class Test_LinearZ(unittest.TestCase):
    def setUp(self):
        self.stage = z_controller()

    def test_move(self):
        pos = self.stage.get_position()
        self.stage.MOVVEL([pos - 1], [10])
        time.sleep(1)
        self.stage.wait_end_motion(5)
        self.assertTrue(
                np.all(np.abs(self.stage.get_position() - (pos - 1)) < 1e-1))
        
    def test_reconnect(self):
        self.stage.disconnect()
        self.assertFalse(self.stage.isConnected())
        self.stage.connect()
        self.stage.get_position()
        self.assertTrue(self.stage.isConnected())
        
    def test_STOP(self):
        pos = self.stage.get_position()
        self.stage.wait_end_motion(5)
        self.assertFalse(self.stage.is_moving())
        self.stage.MOVVEL([pos - 10], [5])
        time.sleep(0.1)
        self.assertTrue(self.stage.is_moving())
        self.stage.stop()
        self.assertFalse(self.stage.is_moving())
        
    def test_ESTOP(self):
        pos = self.stage.get_position()
        self.stage.wait_end_motion(5)
        self.assertFalse(self.stage.is_moving())
        self.stage.MOVVEL([pos - 10], [5])
        time.sleep(0.1)
        self.assertTrue(self.stage.is_moving())
        self.stage.ESTOP()
        self.assertFalse(self.stage.is_moving())
        
if __name__ == '__main__':
    unittest.main()