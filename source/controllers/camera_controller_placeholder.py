# -*- coding: utf-8 -*-
"""
Created on Mon May  1 11:17:56 2017

@author: quentinpeter

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
from matplotlib.image import imread
from glob import glob
import random
import numpy as np
import re


class camera_controller():
    def __init__(self):
        self.exposure_time = .01

    def reconnect(self):
        print('Connected Camera')

    def get_image(self):
        return np.random.rand(50, 100) * 256
        fns = 'Misc/Images/50_50/*.bmp'
        reg = 'Misc/Images\/50_50\/(\d+)\.bmp'
        fns = glob(fns)
        if fns != []:
            fns = np.array(fns)
            X = np.array([int(re.search(reg, fn)[1]) for fn in fns])
            fns = fns[np.argsort(X)]
            X = X[np.argsort(X)]

            if z is not None:
                idx = np.argmin((z - X)**2)
                fn = fns[idx]
            else:
                fn = random.choice(fns)
            im = imread(fn)[:, :, 0]
            return im
        else:
            print(fns)
            return np.random.rand(50, 50) * 256

    def exposure_time_range(self):
        return [1.9e-5, .1]

    def set_exposure_time(self, time):
        self.exposure_time = time

    def get_exposure_time(self):
        return self.exposure_time
