# -*- coding: utf-8 -*-
"""
Created on Tue May  2 09:29:10 2017

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
from PyQt5 import QtCore, QtWidgets
from application_delegate import application_delegate

from widgets.canvas import Canvas
from widgets.coordinates_tab import Coordinates_tab
from widgets.write_tab import Write_tab
from widgets.controls_tab import Controls_tab
from widgets.bottom import Bottom_widget
from widgets.focus_tab import Focus_tab
from widgets.script_tab import Script_tab
from widgets.canvas_tab import Canvas_widget

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):

        # Init everything
        QtWidgets.QMainWindow.__init__(self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        # create menu
        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QtWidgets.QMenu('&Help', self)
#        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&About', self.about)

#        self.statusBar().showMessage("Hello", 2000)

        # Create canevas
        imCanvas = Canvas()

        # create appication delegate
        self.application_delegate = application_delegate(imCanvas)

        #======================================================================
        #       Create Widgets
        #======================================================================

        # Create main widget
        self.main_widget = QtWidgets.QWidget(self)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)

        # Create tab widget
        tabs_widget = QtWidgets.QTabWidget()

        tabs_widget.addTab(Coordinates_tab(self.application_delegate),
                           'Coordinates')
        tabs_widget.addTab(Write_tab(self.application_delegate),
                           'Write')
        tabs_widget.addTab(Focus_tab(self.application_delegate),
                           'Focus')
        tabs_widget.addTab(Script_tab(self.application_delegate),
                           'Script')

        tabs_widget.setMaximumWidth(300)

        control_widget = Controls_tab(self.application_delegate)
        #======================================================================
        #     Layout
        #======================================================================
        vertical = QtWidgets.QVBoxLayout()
        vertical.addWidget(imCanvas, 1)
        vertical.addWidget(Canvas_widget(self.application_delegate))
        vertical.addWidget(Bottom_widget(self.application_delegate))

        horizontal = QtWidgets.QHBoxLayout(self.main_widget)
        horizontal.addWidget(tabs_widget)
        horizontal.addLayout(vertical, 1)
        horizontal.addWidget(control_widget)

        self.application_delegate.error.connect(self.showError)

        self.activateWindow()
        self.setFocus()

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtCore.Qt
        QtWidgets.QMessageBox.about(self, "About",
                                    """Two photons controller GUI written by Quentin Peter""")

    def showError(self, msg):
        QtWidgets.QErrorMessage(self).showMessage(msg)
