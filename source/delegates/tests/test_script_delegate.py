# -*- coding: utf-8 -*-

import unittest

import matplotlib.pyplot as plt
import sys
sys.path.append('../..')
from delegates.application_delegate import Application_delegate
import numpy as np

from delegates.script_delegate import Draw_Parser, Execute_Parser

ad = Application_delegate()
class Test_script(unittest.TestCase):
    def setUp(self):
        self.fn = '../../../files/test/test.txt'

    def test_Draw(self):
        def test():
            pass
        fig = plt.figure()
        test._axes = fig.add_subplot(111)
        test.show = test
        test.clear = test
        test.draw = test
        plt.axis('auto')
        parser = Draw_Parser(test)
        parser.parse(self.fn)
        self.assertTrue(
            np.max(np.abs(
                parser.piezo_position - [40, 0, 0])) < 1)

    def test_execute(self):
        parser = Execute_Parser(ad)
        parser.parse(self.fn)
        self.assertTrue(
            np.max(np.abs(
                ad.movement_delegate.piezo.position - [40, 0, 0])) < 1)

if __name__ == '__main__':
    unittest.main()