# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 16:19:16 2017

@author: quentinpeter
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 16:58:40 2017

@author: quentinpeter
"""
from PyQt5 import QtWidgets
import numpy as np


class Canvas_widget(QtWidgets.QWidget):

    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        # ======================================================================
        #       Range
        # ======================================================================
        min_label = QtWidgets.QLabel("Min:")
        min_input = QtWidgets.QLineEdit('0')
        max_label = QtWidgets.QLabel("Max:")
        max_input = QtWidgets.QLineEdit('255')
        auto_button = QtWidgets.QPushButton("auto")
        full_button = QtWidgets.QPushButton("full")

        range_layout = QtWidgets.QGridLayout(self)
        range_layout.addWidget(min_label, 0, 0)
        range_layout.addWidget(min_input, 0, 1)
        range_layout.addWidget(max_label, 1, 0)
        range_layout.addWidget(max_input, 1, 1)
        range_layout.addWidget(auto_button, 0, 2)
        range_layout.addWidget(full_button, 1, 2)

        full_button.clicked.connect(lambda:
                                    application_delegate.canvas_delegate.set_range())

        def changeRange():
            vmin = float(min_input.text())
            vmax = float(max_input.text())
            application_delegate.canvas_delegate.set_range(vmin, vmax)

        min_input.editingFinished.connect(changeRange)
        max_input.editingFinished.connect(changeRange)

        auto_button.clicked.connect(
            application_delegate.canvas_delegate.auto_range)
        application_delegate.canvas_delegate.newrange.connect(self.setrange)
        self.min_input = min_input
        self.max_input = max_input

        cross0_label = QtWidgets.QLabel("Point0:")
        cross0_pos = QtWidgets.QLabel("")
        cross1_label = QtWidgets.QLabel("Point1:")
        cross1_pos = QtWidgets.QLabel("")
        dist_label = QtWidgets.QLabel("Distance:")
        dist_display = QtWidgets.QLabel("")
        pxsize_label = QtWidgets.QLabel("Pixel Size:")
        pxsize_input = QtWidgets.QLineEdit('1')
        crosses_clear_button = QtWidgets.QPushButton("Clear")

        range_layout.addWidget(cross0_label, 0, 3)
        range_layout.addWidget(cross0_pos, 0, 4)
        range_layout.addWidget(cross1_label, 1, 3)
        range_layout.addWidget(cross1_pos, 1, 4)
        range_layout.addWidget(dist_label, 0, 5)
        range_layout.addWidget(dist_display, 0, 6)
        range_layout.addWidget(pxsize_label, 1, 5)
        range_layout.addWidget(pxsize_input, 1, 6)
        range_layout.addWidget(crosses_clear_button, 0, 7)

        self.setLayout(range_layout)

        def changePX():
            pxsize = float(pxsize_input.text())
            application_delegate.canvas_delegate.set_pixel_size(pxsize)

        pxsize_input.editingFinished.connect(changePX)
        application_delegate.canvas_delegate.newclick.connect(self.showPos)
        crosses_clear_button.clicked.connect(lambda:
                                             application_delegate.canvas_delegate.clear_click())
        self.cross0_pos = cross0_pos
        self.cross1_pos = cross1_pos
        self.dist_display = dist_display

    def setrange(self, vmin, vmax):
        self.min_input.setText("{:.2f}".format(vmin))
        self.max_input.setText("{:.2f}".format(vmax))

    def showPos(self, pos):
        vec = pos[0] - pos[1]
        dist = np.sqrt(np.dot(vec, vec))
        if np.all(np.isfinite(pos[0])):
            text = "{:.2f}, {:.2f}".format(*pos[0])
        else:
            text = ''
        self.cross0_pos.setText(text)
        if np.all(np.isfinite(pos[1])):
            text = "{:.2f}, {:.2f}".format(*pos[1])
        else:
            text = ''
        self.cross1_pos.setText(text)
        if np.isfinite(dist):
            text = "{:.2f}".format(dist)
        else:
            text = ''
        self.dist_display.setText(text)
