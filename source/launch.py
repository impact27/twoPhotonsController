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
# from controllers.camera_controller import Camera_controller

#%%
# cc = Camera_controller()
def fun():
    qApp = QtWidgets.QApplication(sys.argv)
    ad = Application_delegate()
    print("READY!")
    sys.exit(qApp.exec_())
thread = Thread(target=fun)
# thread.start()
fun()

#%%
print( "\n*** STACKTRACE - START ***\n")
code = []
for threadId, stack in sys._current_frames().items():
    if threadId != thread.ident:
        continue
    code.append("\n# ThreadID: %s" % threadId)
    for filename, lineno, name, line in traceback.extract_stack(stack):
        code.append('File: "%s", line %d, in %s' % (filename,
                                                    lineno, name))
        if line:
            code.append("  %s" % (line.strip()))

for line in code:
    print(line)
print("\n*** STACKTRACE - END ***\n")
#%%
import time
from collections import Counter
import os.path
current = []
for idx in range(100):
    current.append([])
    time.sleep(0.1)
    for filename, lineno, name, line in traceback.extract_stack(
            sys._current_frames()[thread.ident]):
        if 'twoPhotonsController' in filename:
            current[idx] = [filename, lineno, name, line]
#%%
files = []
lines = {}
for stack in current:
    fn = os.path.basename(stack[0])
    files.append(fn)
    if not fn in lines:
        lines[fn] = []
    lines[fn].append(stack[1])
print(Counter(files))
for key in lines:
    print(key)
    print(Counter(lines[key]))
