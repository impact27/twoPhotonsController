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

qApp = QtWidgets.QApplication(sys.argv)
ad = Application_delegate()
print("READY!")
sys.exit(qApp.exec_())