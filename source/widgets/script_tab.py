# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 10:49:39 2017

@author: quentinpeter
"""

from PyQt5 import QtCore, QtWidgets


class Script_tab(QtWidgets.QWidget):

    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.sd = application_delegate.script_delegate

        #======================================================================
        #       Create Widgets
        #======================================================================
        script_label = QtWidgets.QLabel("GCode Path:")
        path_field = QtWidgets.QLineEdit()
        browse_button = QtWidgets.QPushButton('Browse')
        run_button = QtWidgets.QPushButton('Run')
        draw_button = QtWidgets.QPushButton('Draw')

        #======================================================================
        #     Layout
        #======================================================================

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(script_label)
        main_layout.addWidget(path_field)
        main_layout.addWidget(browse_button)
        main_layout.addWidget(run_button)
        main_layout.addWidget(draw_button)
        main_layout.addStretch()
        self.setLayout(main_layout)

        #======================================================================
        #      Connections
        #======================================================================
        browse_button.clicked.connect(self.browse_file)
        run_button.clicked.connect(lambda: self.sd.execute(path_field.text()))
        draw_button.clicked.connect(lambda: self.sd.draw(path_field.text()))

        #======================================================================
        #         Save variables
        #======================================================================

        self.path_field = path_field

    def browse_file(self):
        fn = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Position File', QtCore.QDir.homePath(),
            'Text File (*.txt)')
        self.path_field.setText(fn[0])
