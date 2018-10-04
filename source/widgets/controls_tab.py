# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 16:55:28 2017

@author: quentinpeter
"""
from PyQt5 import QtWidgets, QtGui, QtCore
from functools import partial
import numpy as np

from .myWidgets import LightWidget, doubleSelector
from .switch import Switch
from errors import MotionError

class Controls_tab(QtWidgets.QWidget):
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        md = application_delegate.movement_delegate
        ld = application_delegate.laser_delegate
        cd = application_delegate.camera_delegate
        # ======================================================================
        #       Create Widgets
        # ======================================================================

        laser_label = QtWidgets.QLabel("Laser")
        laser_label.setStyleSheet("font: bold large")
        laser_reconnect = QtWidgets.QPushButton('Reconnect')
        laser_V_label = QtWidgets.QLabel("I [V]:")
        laser_setV = doubleSelector(ld.get_range(), ld.get_intensity())

        motor_label = QtWidgets.QLabel('Linear Stage')
        motor_label.setStyleSheet("font: bold large")
        motor_status = LightWidget()
        motor_target_status = LightWidget()
        stage_motor_reconnect = QtWidgets.QPushButton('Reconnect')
        stage_cube_reconnect = QtWidgets.QPushButton('Reconnect')

        vel_motor_range = md.motor.get_velocityRange(0)
        vel_cube_range = md.piezo.get_velocityRange(0)

        vel_motor_label = QtWidgets.QLabel('V [μm/s]:')
        vel_cube_label = QtWidgets.QLabel('V [μm/s]:')
        vel_motor_selector = doubleSelector(vel_motor_range, md.motor.velocity)
        vel_cube_selector = doubleSelector(vel_cube_range, md.piezo.velocity)

        motor_Ranges = md.motor.positionRange

        AxisNames = ['X', 'Y', 'Z']

        motor_labels = [QtWidgets.QLabel(s + ' [μm]: ') for s in AxisNames]
        motor_position = md.motor.position
        motor_selectors = [doubleSelector(r, x)for r, x in zip(motor_Ranges,
                                                               motor_position)]

        step_labels = [QtWidgets.QLabel(s + ' Step [μm]: ') for s in AxisNames]
        pluses = [QtWidgets.QPushButton(' + ') for s in AxisNames]
        minuses = [QtWidgets.QPushButton(' - ') for s in AxisNames]
        steps = [QtWidgets.QLineEdit('1') for s in AxisNames]
        validators = [QtGui.QDoubleValidator(0, motor_Ranges[i, -1]
                                             - motor_Ranges[i, 0], 3) for i in range(3)]
        for v, step in zip(validators, steps):
            v.setNotation(QtGui.QDoubleValidator.StandardNotation)
            step.setValidator(v)

        goto_motor_button = QtWidgets.QPushButton("GO")
        getcurr_motor_button = QtWidgets.QPushButton("Get Current")

        motor_z_piezo_button = Switch()
        motor_z_piezo_label = QtWidgets.QLabel("Z Piezo")

        cube_label = QtWidgets.QLabel('Piezo Stage')
        cube_label.setStyleSheet("font: bold large")
        cube_status = LightWidget()
        cube_target_status = LightWidget()

        cube_ranges = md.piezo.positionRange
        cube_pos = md.piezo.position
        cube_selectors = [doubleSelector(r, x) for r, x in zip(cube_ranges,
                                                               cube_pos)]
        cube_labels = [QtWidgets.QLabel(s + ' [μm]: ') for s in AxisNames]

        goto_cube_button = QtWidgets.QPushButton("GO")
        getcurr_cube_button = QtWidgets.QPushButton("Get Current")
        reset_cube_button = QtWidgets.QPushButton("Reset")

        cam_label = QtWidgets.QLabel('Camera')
        cam_label.setStyleSheet("font: bold large")
        cam_reconnect = QtWidgets.QPushButton('Reconnect')
        cam_range = cd.exposure_time_range()
        cam_init = cd.get_exposure_time()
        cam_exposure_label = QtWidgets.QLabel('Exp. [s]:')
        cam_exposure_selector = doubleSelector(cam_range, cam_init, isLog=True)
        
        cam_autoexposure_time = Switch()
        cam_autoexposure_time_label = QtWidgets.QLabel('Auto')
        cam_extshutter = Switch()
        cam_extshutter_label = QtWidgets.QLabel('Shutter')
        
        piezo_outok_button = Switch()
        piezo_outok_button.setChecked(False)
        piezo_outok_label = QtWidgets.QLabel('Clip range')

        # ======================================================================
        #     Layout
        # ======================================================================

        laser_H_layout = QtWidgets.QHBoxLayout()
        laser_H_layout.addWidget(laser_label)
        laser_H_layout.addWidget(laser_reconnect)

        laser_layout = QtWidgets.QHBoxLayout()
        laser_layout.addWidget(laser_V_label)
        laser_layout.addWidget(laser_setV)

        motor_H_layout = QtWidgets.QHBoxLayout()
        motor_H_layout.addWidget(motor_label)
        motor_H_layout.addWidget(motor_status)
        motor_H_layout.addWidget(motor_target_status)
        motor_H_layout.addWidget(stage_motor_reconnect)

        motor_layout = QtWidgets.QGridLayout()
        motor_layout.addWidget(vel_motor_label, 0, 0)
        motor_layout.addWidget(vel_motor_selector, 0, 1)
        for i in range(3):
            motor_layout.addWidget(motor_labels[i], 1 + 2 * i, 0)
            motor_layout.addWidget(motor_selectors[i], 1 + 2 * i, 1)
            layout = QtWidgets.QHBoxLayout()
            layout.addStretch()
            layout.addWidget(step_labels[i])
            layout.addWidget(steps[i])
            layout.addWidget(minuses[i])
            layout.addWidget(pluses[i])
            layout.addStretch()
            motor_layout.addLayout(layout, 2 * (1 + i), 0, 1, 2)

        motor_GO_layout = QtWidgets.QHBoxLayout()
        motor_GO_layout.addWidget(getcurr_motor_button)
        motor_GO_layout.addWidget(goto_motor_button)

        cube_H_layout = QtWidgets.QHBoxLayout()
        cube_H_layout.addWidget(cube_label)
        cube_H_layout.addWidget(cube_status)
        cube_H_layout.addWidget(cube_target_status)
        cube_H_layout.addWidget(stage_cube_reconnect)

        cube_layout = QtWidgets.QGridLayout()
        cube_layout.addWidget(vel_cube_label, 0, 0)
        cube_layout.addWidget(vel_cube_selector, 0, 1)
        for i in range(3):
            cube_layout.addWidget(cube_labels[i], 1 + i, 0)
            cube_layout.addWidget(cube_selectors[i], 1 + i, 1)

        cube_GO_layout = QtWidgets.QHBoxLayout()
        cube_GO_layout.addWidget(getcurr_cube_button)
        cube_GO_layout.addWidget(reset_cube_button)
        cube_GO_layout.addWidget(goto_cube_button)
        
        cube_toogle_layout = QtWidgets.QHBoxLayout()
        cube_toogle_layout.addWidget(piezo_outok_label)
        cube_toogle_layout.addWidget(piezo_outok_button)

        cam_H_layout = QtWidgets.QHBoxLayout()
        cam_H_layout.addWidget(cam_label)
        cam_H_layout.addWidget(cam_reconnect)

        cam_layout = QtWidgets.QHBoxLayout()
        cam_layout.addWidget(cam_exposure_label)
        cam_layout.addWidget(cam_exposure_selector)

        cam_Button_layout = QtWidgets.QHBoxLayout()
        cam_Button_layout.addWidget(cam_autoexposure_time_label)
        cam_Button_layout.addWidget(cam_autoexposure_time)
        cam_Button_layout.addWidget(cam_extshutter_label)
        cam_Button_layout.addWidget(cam_extshutter)

        motor_z_piezo_layout = QtWidgets.QHBoxLayout()
        motor_z_piezo_layout.addWidget(motor_z_piezo_label)
        motor_z_piezo_layout.addWidget(motor_z_piezo_button)
        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(motor_H_layout)
        main_layout.addLayout(motor_layout)
        main_layout.addLayout(motor_GO_layout)
        main_layout.addLayout(motor_z_piezo_layout)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)

        main_layout.addLayout(cube_H_layout)
        main_layout.addLayout(cube_layout)
        main_layout.addLayout(cube_GO_layout)
        main_layout.addLayout(cube_toogle_layout)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)

        main_layout.addLayout(laser_H_layout)
        main_layout.addLayout(laser_layout)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)

        main_layout.addLayout(cam_H_layout)
        main_layout.addLayout(cam_layout)
        main_layout.addLayout(cam_Button_layout)

        main_layout.addStretch()

        self.setLayout(main_layout)
        # ======================================================================
        #      Connections
        # ======================================================================
#        laser_reconnect.clicked.connect(ld.reconnect)
        laser_setV.newValue.connect(ld.set_intensity)

        stage_motor_reconnect.clicked.connect(md.motor.reconnect)
        stage_cube_reconnect.clicked.connect(md.piezo.reconnect)

        goto_motor_button.clicked.connect(self.goto_motor)
        motor_z_piezo_button.clicked.connect(md.motor_z_switcher.switch)
        
        def movepiezzo():
            try:
                md.piezo.goto_position([s.getValue() for s in cube_selectors])
            except MotionError as e:
                application_delegate.error.emit(f"Can't move {e}")
        goto_cube_button.clicked.connect(movepiezzo)

        vel_motor_selector.newValue.connect(md.motor.set_velocity)

        vel_cube_selector.newValue.connect(md.piezo.set_velocity)

#        cam_reconnect.clicked.connect(cd.reconnect)

        cam_exposure_selector.newValue.connect(cd.set_exposure_time)

        cd.state_auto_exposure_time.connect(self.setCamShutter)

        ld.newIntensity.connect(laser_setV.setValue)

        cd.new_exposure_time.connect(cam_exposure_selector.setValue)

        for i in range(3):
            pluses[i].clicked.connect(partial(self.step, i, 1))
            minuses[i].clicked.connect(partial(self.step, i, -1))

        getcurr_cube_button.clicked.connect(self.update_cube)
        getcurr_motor_button.clicked.connect(self.update_motor)
        reset_cube_button.clicked.connect(md.piezo.reset)

        md.updatePosition.connect(
            self.updatePos)

        cam_autoexposure_time.toggled.connect(cd.auto_exposure_time)
        cam_extshutter.toggled.connect(cd.extShutter)

        def setMotorRange(corrections):
            ranges = md.motor.positionRange
            for s, r in zip(motor_selectors, ranges):
                s.setRange(*r, 3)
            self.update_motor()

        md.motor.coordinatesCorrected.connect(setMotorRange)
        md.motor.move_signal.connect(
            self.set_target_motor)
        md.piezo.move_signal.connect(
            self.set_target_piezo)
        
        piezo_outok_button.toggled.connect(md.piezo.set_out_of_range_ok)

        # ======================================================================
        #         Save variables
        # ======================================================================
        self.application_delegate = application_delegate
        self.vel_motor_selector = vel_motor_selector
        self.motor_selectors = motor_selectors
        self.vel_cube_selector = vel_cube_selector
        self.cube_selectors = cube_selectors
        self.cam_autoexposure_time = cam_autoexposure_time
        self.steps = steps
        self.laser_selector = laser_setV

        # Update status
        def updateStatus():
            motor_status.setOn(md.motor.is_ready())
            motor_target_status.setOn(md.motor.is_onTarget())
            cmutex = md.piezo.controller_mutex()
            if not cmutex.tryLock():
                return
            try:
                if md.piezo.isRecordingMacro:
                    return
                cube_status.setOn(md.piezo.is_ready())
                cube_target_status.setOn(md.piezo.is_onTarget())
                if md.piezo.is_macro_running():
                    self.updatePos()
            finally:
                cmutex.unlock()

        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(updateStatus)
        self.status_timer.start(1000)

    def set_target_motor(self, target_pos, speed):
        for sel, pos in zip([*(self.motor_selectors), self.vel_motor_selector],
                            [*target_pos, speed]):
            if np.isfinite(pos):
                sel.setValue(pos)

    def set_target_piezo(self, target_pos, speed):
        for sel, pos in zip([*(self.cube_selectors), self.vel_cube_selector],
                            [*target_pos, speed]):
            if np.isfinite(pos):
                sel.setValue(pos)

    def setCamShutter(self, on):
        self.cam_autoexposure_time.setChecked(on)

    def goto_motor(self):
        self.application_delegate.movement_delegate.motor.goto_position(
            [s.getValue() for s in self.motor_selectors])

    def step(self, axis, d):
        step = d * float(self.steps[axis].text())
        selector = self.motor_selectors[axis]
        val = selector.getValue()
        selector.setValue(val + step)
        self.goto_motor()

    def update_motor(self):
        V = self.application_delegate.movement_delegate.motor.velocity
        Pos = self.application_delegate.movement_delegate.motor.position
        self.vel_motor_selector.setValue(V)
        [s.setValue(x) for s, x in zip(self.motor_selectors, Pos)]

    def update_cube(self):
        md = self.application_delegate.movement_delegate
        cmutex = md.piezo.controller_mutex()
        if not cmutex.tryLock():
            return
        try:
            if md.piezo.isRecordingMacro:
                return
            V = md.piezo.velocity
            Pos = md.piezo.position
            self.vel_cube_selector.setValue(V)
            [s.setValue(x) for s, x in zip(self.cube_selectors, Pos)]
            I = self.application_delegate.laser_delegate.get_intensity()
            self.laser_selector.setValue(I)
        finally:
            cmutex.unlock()

    def updatePos(self):
        self.update_motor()
        self.update_cube()
