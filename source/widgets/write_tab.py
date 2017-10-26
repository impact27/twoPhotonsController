# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 16:54:21 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets, QtGui

class Write_tab(QtWidgets.QWidget):
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        #======================================================================
        #       Create Widgets
        #======================================================================

        Origin_label = QtWidgets.QLabel('Origin:')

        Xinput = QtWidgets.QLineEdit('0')
        X_validator = QtGui.QDoubleValidator(-1, 100, 3)
        Xinput.setValidator(X_validator)

        Yinput = QtWidgets.QLineEdit('0')
        Y_validator = QtGui.QDoubleValidator(-1, 100, 3)
        Yinput.setValidator(Y_validator)

        gcode_label = QtWidgets.QLabel("GCode Path:")

        path_field = QtWidgets.QLineEdit()
        browse_button = QtWidgets.QPushButton('Browse')

        tile_label = QtWidgets.QLabel("Tile")
        Nx_label = QtWidgets.QLabel("Nx")
        Ny_label = QtWidgets.QLabel("Ny")
        dx_label = QtWidgets.QLabel("dx")
        dy_label = QtWidgets.QLabel("dy")

        Nx_input = QtWidgets.QLineEdit("1")
        Nx_input.setValidator(QtGui.QIntValidator(0, 100))
        Ny_input = QtWidgets.QLineEdit("1")
        Ny_input.setValidator(QtGui.QIntValidator(0, 100))
        dx_input = QtWidgets.QLineEdit("0")
        dx_input.setValidator(QtGui.QDoubleValidator(-1e6, 1e6, 3))
        dy_input = QtWidgets.QLineEdit("0")
        dy_input.setValidator(QtGui.QDoubleValidator(-1e6, 1e6, 3))

        draw_button = QtWidgets.QPushButton('Draw')
        write_button = QtWidgets.QPushButton('Write')

        #======================================================================
        #     Layout
        #======================================================================

        origin_layout = QtWidgets.QGridLayout()
        origin_layout.addWidget(Origin_label, 0, 0, 1, 4)
        origin_layout.addWidget(QtWidgets.QLabel("X:"), 1, 0)
        origin_layout.addWidget(Xinput, 1, 1)
        origin_layout.addWidget(QtWidgets.QLabel("Y:"), 1, 2)
        origin_layout.addWidget(Yinput, 1, 3)

        path_layout = QtWidgets.QGridLayout()
        path_layout.addWidget(gcode_label, 0, 0, 1, 2)
        path_layout.addWidget(path_field, 1, 0)
        path_layout.addWidget(browse_button, 1, 1)

        tile_layout = QtWidgets.QGridLayout()
        tile_layout.addWidget(tile_label, 0, 0, 1, 2)
        tile_layout.addWidget(Nx_label, 1, 0)
        tile_layout.addWidget(Ny_label, 2, 0)
        tile_layout.addWidget(dx_label, 3, 0)
        tile_layout.addWidget(dy_label, 4, 0)
        tile_layout.addWidget(Nx_input, 1, 1)
        tile_layout.addWidget(Ny_input, 2, 1)
        tile_layout.addWidget(dx_input, 3, 1)
        tile_layout.addWidget(dy_input, 4, 1)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(origin_layout)
        main_layout.addLayout(path_layout)
        main_layout.addLayout(tile_layout)

        main_layout.addWidget(draw_button)
        main_layout.addWidget(write_button)

        main_layout.addStretch()
        self.setLayout(main_layout)

        #======================================================================
        #      Connections
        #======================================================================

        def write_infos():
            return (float(Xinput.text()),
                    float(Yinput.text()),
                    path_field.text(),
                    int(Nx_input.text()),
                    int(Ny_input.text()),
                    float(dx_input.text()),
                    float(dy_input.text()))

        draw_button.clicked.connect(lambda: application_delegate.draw_device(
            *write_infos()))
        write_button.clicked.connect(lambda: application_delegate.write_device(
            *write_infos()))

        browse_button.clicked.connect(self.browse_gfile)

#        application_delegate.newXRange.connect(X_validator.setRange)
#        application_delegate.newYRange.connect(Y_validator.setRange)

        #======================================================================
        #         Save variables
        #======================================================================

        self.path_field = path_field

    def browse_gfile(self):
        fn = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Position File', QtCore.QDir.homePath(),
            'GCode File (*.gcode)')
        self.path_field.setText(fn[0])