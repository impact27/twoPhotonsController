# -*- coding: utf-8 -*-
"""
Created on Tue Sep  4 19:08:26 2018

@author: Local_Admin
"""

import unittest
import numpy as np
import sys
sys.path.append('../..')
from delegates.movement_delegate import Movement_delegate


class Test_script(unittest.TestCase):
    def setUp(self):
        pass

    def test_init(self):
        md = Movement_delegate()


if __name__ == '__main__':
    unittest.main()
