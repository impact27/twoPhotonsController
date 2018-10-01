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

        # ======================================================================
        #       Create Widgets
        # ======================================================================
        script_label = QtWidgets.QLabel("Script")
        path_field = QtWidgets.QLineEdit()
        browse_button = QtWidgets.QPushButton('Browse')
        run_button = QtWidgets.QPushButton('Run')
        draw_button = QtWidgets.QPushButton('Draw')
        stop_button = QtWidgets.QPushButton('Stop')
        pause_resume_button = QtWidgets.QPushButton('Pause')

        # ======================================================================
        #     Layout
        # ======================================================================

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(script_label)
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(path_field)
        path_layout.addWidget(browse_button)
        main_layout.addLayout(path_layout)
        buttons_layout = QtWidgets.QGridLayout()
        buttons_layout.addWidget(draw_button, 0, 0)
        buttons_layout.addWidget(run_button, 0, 1)
        buttons_layout.addWidget(stop_button, 1, 0)
        buttons_layout.addWidget(pause_resume_button, 1, 1)
        main_layout.addLayout(buttons_layout)
#        main_layout.addStretch()
        self.setLayout(main_layout)

        # ======================================================================
        #      Connections
        # ======================================================================
        browse_button.clicked.connect(self.browse_file)
        run_button.clicked.connect(lambda: self.sd.execute(path_field.text()))
        draw_button.clicked.connect(lambda: self.sd.draw(path_field.text()))
        
        stop_button.clicked.connect(lambda: self.sd.execute_stop())
        def set_status(paused):
            if paused:
                pause_resume_button.setText('Resume')
            else:
                pause_resume_button.setText('Pause')
                
        def pause_resume():
            paused = self.sd.execute_pause_resume()
            set_status(paused)
                
        pause_resume_button.clicked.connect(pause_resume)
        self.sd.pause_status.connect(set_status)
        

        # ======================================================================
        #         Save variables
        # ======================================================================

        self.path_field = path_field

    def browse_file(self):
        fn = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Position File', QtCore.QDir.homePath(),
            'Text File (*.txt)')
        self.path_field.setText(fn[0])
