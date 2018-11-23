# -*- coding: utf-8 -*-
"""
Created on Wed May 10 16:57:45 2017

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
import sys
from delegates.application_delegate import Application_delegate
from PyQt5 import QtWidgets
from threading import Thread
import traceback



import time
from collections import Counter
import os.path
import json
import numpy as np

#from controllers.camera_controller import Camera_controller

#%%
#cc = Camera_controller()
#%%


def fun():
    qApp = QtWidgets.QApplication(sys.argv)
    ad = Application_delegate()
    print("READY!")
    sys.exit(qApp.exec_())
thread = Thread(target=fun)
thread.start()
#fun()

#%%
profile = {}
tlast = time.time()
Ntot = 0
while(thread.isAlive()):
    Ntot += 1
    time.sleep(.1)
    for threadId, stack in sys._current_frames().items():
        seen_filename = []
        for filename, lineno, name, line in traceback.extract_stack(stack):
            if 'twoPhotonsController' not in filename:
                continue
            if filename not in profile:
                profile[filename] = {'total': 0}
            if lineno not in profile[filename]:
                profile[filename][lineno] = 0
            if filename not in seen_filename:
                profile[filename]['total'] += 1
                seen_filename.append(filename)
            profile[filename][lineno] += 1
    if time.time() - tlast > 10:
        tlast = time.time()
#        save the most used lines
        profile_save = {}
        files = list(profile.keys())
        files_hits = [profile[file]['total'] for file in files]
        argsort = np.argsort(files_hits)[::-1]
        for arg in argsort:
            file = files[arg]
            profile_save[file] = dict(zip(list(
                    profile[file].keys())[1:],
                    np.asarray(list(profile[file].values())[1:])
                    * 100 / profile[file]['total']))
            profile_save[file]['total'] = profile[file]['total'] / Ntot
#        for
        with open('profile.txt', 'w') as f:
            json.dump(profile_save, f, indent=4)
#%%

#current = []
#for idx in range(100):
#    current.append([])
#    time.sleep(0.01)
#    for filename, lineno, name, line in traceback.extract_stack(
#            sys._current_frames()[thread.ident]):
#        if 'twoPhotonsController' in filename:
#            current[idx] = [filename, lineno, name, line]
##%
#files = []
#lines = {}
#for stack in current:
#    if len(stack) == 0:
#        continue
#    fn = os.path.basename(stack[0])
#    files.append(fn)
#    if not fn in lines:
#        lines[fn] = []
#    lines[fn].append(stack[1])
#print(Counter(files))
#for key in lines:
#    print(key)
#    print(Counter(lines[key]))
