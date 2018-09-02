# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 16:54:21 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets, QtGui
import numpy as np


class Write_tab(QtWidgets.QWidget):
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        # ======================================================================
        #       Create Widgets
        # ======================================================================

        gcode_label = QtWidgets.QLabel("GCode:")
        path_field = QtWidgets.QLineEdit()
        browse_button = QtWidgets.QPushButton('Browse')

        origin_label = QtWidgets.QLabel('Origin:')
        origin_input = QtWidgets.QLineEdit('0, 0')

        Nsteps_label = QtWidgets.QLabel('Number steps:')
        Nsteps_input = QtWidgets.QLineEdit('1, 1')

        stepsize_label = QtWidgets.QLabel('Steps size:')
        stepsize_input = QtWidgets.QLineEdit('5373, 17000')

        retract_label = QtWidgets.QLabel('Retract:')
        retract_input = QtWidgets.QLineEdit('1000')

        focus_offset_label = QtWidgets.QLabel('Focus offset pos:')
        focus_offset_input = QtWidgets.QLineEdit('-100, -100')

        focus_range_label = QtWidgets.QLabel('Focus range:')
        focus_range_input = QtWidgets.QLineEdit('100')

        focus_step_label = QtWidgets.QLabel('focus step:')
        focus_step_input = QtWidgets.QLineEdit('-1')

        draw_button = QtWidgets.QPushButton('Draw')
        write_button = QtWidgets.QPushButton('Write')


#        Nx_input.setValidator(QtGui.QIntValidator(0, 100))
#        Ny_input.setValidator(QtGui.QIntValidator(0, 100))
#        dx_input.setValidator(QtGui.QDoubleValidator(-1e6, 1e6, 3))
#        dy_input.setValidator(QtGui.QDoubleValidator(-1e6, 1e6, 3))

        # ======================================================================
        #     Layout
        # ======================================================================

        settings_layout = QtWidgets.QGridLayout()
        settings_layout.addWidget(origin_label, 0, 0)
        settings_layout.addWidget(origin_input, 0, 1)
        settings_layout.addWidget(Nsteps_label, 1, 0)
        settings_layout.addWidget(Nsteps_input, 1, 1)
        settings_layout.addWidget(stepsize_label, 2, 0)
        settings_layout.addWidget(stepsize_input, 2, 1)
        settings_layout.addWidget(retract_label, 3, 0)
        settings_layout.addWidget(retract_input, 3, 1)
        settings_layout.addWidget(focus_offset_label, 4, 0)
        settings_layout.addWidget(focus_offset_input, 4, 1)
        settings_layout.addWidget(focus_range_label, 5, 0)
        settings_layout.addWidget(focus_range_input, 5, 1)
        settings_layout.addWidget(focus_step_label, 6, 0)
        settings_layout.addWidget(focus_step_input, 6, 1)

        path_layout = QtWidgets.QGridLayout()
        path_layout.addWidget(gcode_label, 0, 0, 1, 2)
        path_layout.addWidget(path_field, 1, 0)
        path_layout.addWidget(browse_button, 1, 1)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(path_layout)
        main_layout.addLayout(settings_layout)

        buttons_layout = QtWidgets.QHBoxLayout()
        buttons_layout.addWidget(draw_button)
        buttons_layout.addWidget(write_button)
        main_layout.addLayout(buttons_layout)

#        main_layout.addStretch()
        self.setLayout(main_layout)

        # ======================================================================
        #      Connections
        # ======================================================================

        def write_infos():
            settings = {}
            settings['XY origin'] = np.fromstring(
                origin_input.text(), sep=',')
            settings['[X, Y] number of steps'] = np.fromstring(
                Nsteps_input.text(), sep=',')
            settings['[X, Y] steps size'] = np.fromstring(
                stepsize_input.text(), sep=',')
            settings['movment retraction'] = float(retract_input.text())
            settings['focus offset'] = np.fromstring(
                focus_offset_input.text(), sep=',')
            settings['focus range'] = float(focus_range_input.text())
            settings['focus step'] = float(focus_step_input.text())

            return path_field.text(), settings

        draw_button.clicked.connect(lambda:
                                    application_delegate.write_delegate.draw(*write_infos()))
        write_button.clicked.connect(lambda:
                                     application_delegate.write_delegate.write(*write_infos()))

        browse_button.clicked.connect(self.browse_gfile)

#        application_delegate.newXRange.connect(X_validator.setRange)
#        application_delegate.newYRange.connect(Y_validator.setRange)

        # ======================================================================
        #         Save variables
        # ======================================================================

        self.path_field = path_field

    def browse_gfile(self):
        fn = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Position File', QtCore.QDir.homePath(),
            'GCode File (*.gcode)')
        self.path_field.setText(fn[0])
