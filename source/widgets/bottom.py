# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 16:58:40 2017

@author: quentinpeter
"""
from PyQt5 import QtWidgets
import numpy as np

class Bottom_widget(QtWidgets.QWidget):

    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        #======================================================================
        #       Create Widgets
        #======================================================================
        min_label = QtWidgets.QLabel("Min:")
        min_input = QtWidgets.QLineEdit('0')
        max_label = QtWidgets.QLabel("Max:")
        max_input = QtWidgets.QLineEdit('255')
        auto_button = QtWidgets.QPushButton("auto")
        full_button = QtWidgets.QPushButton("full")

    
        ESTOP_button = QtWidgets.QPushButton("EMERGENCY STOP")
        ESTOP_button.setStyleSheet("background-color: red")
        ESTOP_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)

        live_button = QtWidgets.QPushButton("Start Live")
        live_button.setCheckable(True)

        draw_button = QtWidgets.QPushButton("Start Draw")
        draw_button.setCheckable(True)

        bg_button = QtWidgets.QPushButton("Set Background")
        bg_button.setCheckable(True)

        clear_button = QtWidgets.QPushButton('Clear Graph')
        save_im_button = QtWidgets.QPushButton('Save Image')
        save_fig_button = QtWidgets.QPushButton('Save Figure')

        #======================================================================
        #     Layout
        #======================================================================
        range_layout = QtWidgets.QHBoxLayout()
        range_layout.addWidget(min_label)
        range_layout.addWidget(min_input)
        range_layout.addWidget(max_label)
        range_layout.addWidget(max_input)
        range_layout.addWidget(auto_button)
        range_layout.addWidget(full_button)

        buttons_layout = QtWidgets.QGridLayout()
        buttons_layout.addWidget(live_button, 0, 0)
        buttons_layout.addWidget(draw_button, 0, 1)
        buttons_layout.addWidget(clear_button, 1, 0)
        buttons_layout.addWidget(bg_button, 1, 1)
        buttons_layout.addWidget(ESTOP_button, 0, 3, 2, 3)
        buttons_layout.addWidget(save_im_button, 0, 2)
        buttons_layout.addWidget(save_fig_button, 1, 2)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(range_layout)
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
        #======================================================================
        #      Connections
        #======================================================================
        full_button.clicked.connect(lambda: 
            application_delegate.imageCanvas.imshow())
        
        def changeRange():
            vmin = float(min_input.text())
            vmax = float(max_input.text())
            application_delegate.imageCanvas.imshow(vmin=vmin, vmax=vmax)
            
        min_input.editingFinished.connect(changeRange)
        max_input.editingFinished.connect(changeRange)
        
        def autoRange():
            im = application_delegate.imageCanvas.get_im()
            vmin = np.percentile(im,1)
            vmax = np.percentile(im,99)
            application_delegate.imageCanvas.imshow(vmin=vmin, vmax=vmax)

        auto_button.clicked.connect(autoRange)


        ESTOP_button.clicked.connect(application_delegate.ESTOP)
        clear_button.clicked.connect(application_delegate.imageCanvas.clear)
        save_im_button.clicked.connect(application_delegate.save_im)
        save_fig_button.clicked.connect(application_delegate.save_fig)

        def switchBGButton(on):
            if on:
                bg_button.setText('Remove Background')
                application_delegate.camera_delegate.set_bg()
            else:
                bg_button.setText('Set Background')
                application_delegate.camera_delegate.reset_bg()
        bg_button.toggled.connect(switchBGButton)

        #======================================================================
        #         Save variables
        #======================================================================
        self.live_button = live_button
        self.draw_button = draw_button

        live_button.clicked.connect(application_delegate.switch_live)
        draw_button.clicked.connect(application_delegate.switch_draw)

        application_delegate.liveSwitched.connect(self.switch_live)
        application_delegate.drawSwitched.connect(self.switch_draw)

    def switch_live(self, on):
        if on:
            self.live_button.setText('Stop live')
            self.live_button.setChecked(True)
        else:
            self.live_button.setText('Start live')
            self.live_button.setChecked(False)

    def switch_draw(self, on):
        if on:
            self.draw_button.setText('Stop draw')
            self.draw_button.setChecked(True)
        else:
            self.draw_button.setText('Start draw')
            self.draw_button.setChecked(False)