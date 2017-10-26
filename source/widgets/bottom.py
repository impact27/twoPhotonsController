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
                
# =============================================================================
#         Buttons
# =============================================================================
        
        

    
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

        buttons_layout = QtWidgets.QGridLayout(self)
        buttons_layout.addWidget(live_button, 0, 0)
        buttons_layout.addWidget(draw_button, 0, 1)
        buttons_layout.addWidget(clear_button, 1, 0)
        buttons_layout.addWidget(bg_button, 1, 1)
        buttons_layout.addWidget(ESTOP_button, 0, 3, 2, 3)
        buttons_layout.addWidget(save_im_button, 0, 2)
        buttons_layout.addWidget(save_fig_button, 1, 2)
        
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
        #      Layout
        #======================================================================
        
        self.setLayout(buttons_layout)

        

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