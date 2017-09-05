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
from PyQt5 import QtCore, QtWidgets, QtGui
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from application_delegate import application_delegate
from myWidgets import LightWidget, doubleSelector
from functools import partial
#%%
        

#==============================================================================
# Plot canevas
#==============================================================================

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self._axes = fig.add_subplot(111)
        
        self.compute_initial_figure()

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass
    
class imageCanvas(MyMplCanvas):
    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        self.clear()
        self._lastim=np.zeros((2,2))
        self._autoc = False
        
    def imshow(self, im , vmax = None):
        self._lastim=im
        self.figure.clear()
        self._axes = self.figure.add_subplot(111)
        self._imhandle=self._axes.imshow(im, vmax = vmax)
        self._axes.axis('image')
        self.figure.colorbar(self._imhandle)
        self.draw()
        
    def frameshow(self, im):
        self._lastim=im
        if self._imhandle is not None:
            self._imhandle.set_data(im)
            if self._autoc:
                self._imhandle.set_clim(im.min(), im.max())
            self.draw()
        else:
            self.imshow(im, vmax = 255)
            
    def clear(self):
        self._imhandle=None
        self.figure.clear()
        self._axes = self.figure.add_subplot(111)
        self.draw()
        
    def plot(self, X, Y, fmt='-', axis='normal', **kwargs):
        if self._imhandle is not None:
            self.clear()
        self._axes.plot(X, Y, fmt, **kwargs)
        self._axes.axis(axis)
        self.draw()
        
    def get_im(self):
        return self._lastim
        
        
#==============================================================================
# Tabs            
#==============================================================================        
    
class layout_wrapper(QtWidgets.QWidget):
    def __init__(self, layout, *args, **kwargs):       
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        self.setLayout(layout)
        
class coordinates_tab(QtWidgets.QWidget):
    
    deleterow = QtCore.pyqtSignal(int)
    displayrow = QtCore.pyqtSignal(int)
    
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        
        #======================================================================
        #       Create Widgets
        #======================================================================
        
        Xinput = QtWidgets.QLineEdit('0, 0, 0')
#         X_validator = QtGui.QDoubleValidator(-1,100,3)
#         Xinput.setValidator(X_validator)
        
        newpos_button = QtWidgets.QPushButton("New Reference Position")
        
        path_field = QtWidgets.QLineEdit()
        pos_file_button = QtWidgets.QPushButton('Load Positions File')
        
        pos_list=QtWidgets.QTableWidget()
        pos_list.setColumnCount(3)
        pos_list.setHorizontalHeaderLabels(['Xm','Xs','Delete'])
        pos_list.setColumnWidth(0,90)
        pos_list.setColumnWidth(1,90)
        pos_list.setColumnWidth(2,40)
        pos_list.horizontalHeader().setStretchLastSection(True)
        pos_list.verticalHeader().setDefaultSectionSize(48)
        
        clear_list_button = QtWidgets.QPushButton("Clear List")
        validate_button = QtWidgets.QPushButton("Process next Position")
        
        correction_label = QtWidgets.QLabel('')
        self.correction_label = correction_label
        self.updateCorrection(
                *application_delegate.mouvment_delegate.get_corrections())
        
        correction_reset = QtWidgets.QPushButton('Reset')
        correction_save = QtWidgets.QPushButton('Save')
        correction_load = QtWidgets.QPushButton('Load')
        
        save_errors = QtWidgets.QPushButton('Save Errors')
        #======================================================================
        #     Layout    
        #======================================================================
        
        coord= QtWidgets.QHBoxLayout()
        coord.addWidget(QtWidgets.QLabel("X (x, y, z):"))
        coord.addWidget(Xinput)
        
        tab1Layout=QtWidgets.QVBoxLayout()
        tab1Layout.addLayout(coord)
        tab1Layout.addWidget(newpos_button)
        
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(path_field)
        
        tab2Layout=QtWidgets.QVBoxLayout()
        tab2Layout.addLayout(path_layout)
        tab2Layout.addWidget(pos_file_button)
        
        tabs_widget=QtWidgets.QTabWidget()
        tabs_widget.addTab(layout_wrapper(tab2Layout), 'File')
        tabs_widget.addTab(layout_wrapper(tab1Layout), 'Manual')
        
        tabs_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Minimum)
        
        load_layout = QtWidgets.QHBoxLayout()
        load_layout.addWidget(correction_save)
        load_layout.addWidget(correction_load)
        
        correction_layout = QtWidgets.QVBoxLayout()
        correction_layout.addWidget(correction_label)
        correction_layout.addWidget(correction_reset)
        correction_layout.addLayout(load_layout)
        
        hbuttons=QtWidgets.QHBoxLayout()
        hbuttons.addWidget(save_errors)
        hbuttons.addWidget(clear_list_button)
        
        main_layout=QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(tabs_widget)
        main_layout.addWidget(pos_list)
        main_layout.addWidget(validate_button)
        main_layout.addLayout(hbuttons)
        main_layout.addLayout(correction_layout)
        self.setLayout(main_layout)
        
        #======================================================================
        #      Connections   
        #======================================================================
        cd = application_delegate.coordinates_delegate
        
        pos_list.cellClicked.connect(self.cellClicked)
        pos_list.verticalHeader().sectionClicked.connect(self.rowClicked)
        
        newpos_button.clicked.connect( lambda: cd.add_position(
                    np.fromstring(Xinput.text(), sep=',')))
            
        pos_file_button.clicked.connect(self.openfile)
            
        clear_list_button.clicked.connect(cd.clear_positions)
        validate_button.clicked.connect(cd.processPos)
        
        self.deleterow.connect(cd.del_position)
        self.displayrow.connect(cd.displayrow)
        cd.updatelist.connect(self.updateList)
        
        
        application_delegate.coordinatesCorrected.connect(self.updateCorrection)
        correction_reset.clicked.connect(cd.clear_positions)
        
        md = application_delegate.mouvment_delegate
        correction_save.clicked.connect(md.save_corrections)
        correction_load.clicked.connect(md.load_corrections)
        
        save_errors.clicked.connect(cd.save_errors)
        
        #======================================================================
        #         Save variables
        #======================================================================
        
        self.xinput=Xinput
        self.fninput=path_field
        self.pos_list=pos_list
        self.path_field = path_field
        self.cd = cd
        
    def openfile(self):
        fn = self.path_field.text()
        
        check = QtCore.QFileInfo(fn)
        
        if not check.exists() or not check.isFile():
            fn=QtWidgets.QFileDialog.getOpenFileName(
                    self,'Position File',QtCore.QDir.homePath())
            self.path_field.setText(fn[0])
            
        self.cd.load_list(fn)
        
        
    def cellClicked(self, row,column):
        if column==2:
            self.deleterow.emit(row)
        else:
            self.displayrow.emit(row)
            
    def rowClicked(self, row):
        self.displayrow.emit(row)
        
    def updateList(self,dictlist):
        self.pos_list.clearContents()
        self.pos_list.setRowCount(0)
        for d in dictlist:
            Xm=d['Xm']
            Xs=d['Xs']
            self.addRow(Xm, Xs)
        
    def addRow(self, Xm, Xs):
        """Assume X are [x,y]"""
        row=self.pos_list.rowCount()
        self.pos_list.insertRow(row)
        
        Xmtext = "[{:.0f},\n {:.0f},\n {:.0f}]".format(*Xm)
        Xm_label=QtWidgets.QLabel(Xmtext)
        Xm_label.setAlignment(QtCore.Qt.AlignCenter)
        
        if Xs is None:
            Xstext = '?'
        else:
            Xstext = "[{:.0f},\n {:.0f},\n {:.0f}]".format(*Xs)
        Xs_label=QtWidgets.QLabel(Xstext)
        Xs_label.setAlignment(QtCore.Qt.AlignCenter)
        
        Delete=QtWidgets.QLabel('Delete')
        Delete.setStyleSheet("background-color: red")
        Delete.setAlignment(QtCore.Qt.AlignCenter)
        
        self.pos_list.setCellWidget(row,0,Xm_label)
        self.pos_list.setCellWidget(row,1,Xs_label)
        self.pos_list.setCellWidget(row,2,Delete)
        
    def updateCorrection(self, XYcoeff, Zcoeffs):
        text = ( '{:.3e}X + {:.3e}Y\n+ {:.3f}μm\n'.format(*Zcoeffs)
                + 'Φ:\t{:.5g}π\nθ:\t{:.5g}π\nXo:\t[{:.3f}, {:.3f}]μm'.format(
                    XYcoeff[0]/np.pi, XYcoeff[1]/np.pi, *XYcoeff[2:]))
        self.correction_label.setText(text)
    
class write_tab(QtWidgets.QWidget):
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        #======================================================================
        #       Create Widgets
        #======================================================================
        
        Origin_label = QtWidgets.QLabel('Origin:')
        
        Xinput=QtWidgets.QLineEdit('0')
        X_validator = QtGui.QDoubleValidator(-1,100,3)
        Xinput.setValidator(X_validator)
        
        Yinput=QtWidgets.QLineEdit('0')
        Y_validator = QtGui.QDoubleValidator(-1,100,3)
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
        Nx_input.setValidator(QtGui.QIntValidator(0,100))
        Ny_input = QtWidgets.QLineEdit("1")
        Ny_input.setValidator(QtGui.QIntValidator(0,100))
        dx_input = QtWidgets.QLineEdit("0")
        dx_input.setValidator(QtGui.QDoubleValidator(-1e6,1e6,3))
        dy_input = QtWidgets.QLineEdit("0")
        dy_input.setValidator(QtGui.QDoubleValidator(-1e6,1e6,3))
        
        draw_button = QtWidgets.QPushButton('Draw')
        write_button = QtWidgets.QPushButton('Write')
        
        #======================================================================
        #     Layout    
        #======================================================================
        
        origin_layout= QtWidgets.QGridLayout()
        origin_layout.addWidget(Origin_label,0,0,1,4)
        origin_layout.addWidget(QtWidgets.QLabel("X:"),1,0)
        origin_layout.addWidget(Xinput,1,1)
        origin_layout.addWidget(QtWidgets.QLabel("Y:"),1,2)
        origin_layout.addWidget(Yinput,1,3)
        
        path_layout = QtWidgets.QGridLayout()
        path_layout.addWidget(gcode_label,0,0,1,2)
        path_layout.addWidget(path_field,1,0)
        path_layout.addWidget(browse_button,1,1)
        
        tile_layout = QtWidgets.QGridLayout()
        tile_layout.addWidget(tile_label,0,0,1,2)
        tile_layout.addWidget(Nx_label,1,0)
        tile_layout.addWidget(Ny_label,2,0)
        tile_layout.addWidget(dx_label,3,0)
        tile_layout.addWidget(dy_label,4,0)
        tile_layout.addWidget(Nx_input,1,1)
        tile_layout.addWidget(Ny_input,2,1)
        tile_layout.addWidget(dx_input,3,1)
        tile_layout.addWidget(dy_input,4,1)
        
        main_layout=QtWidgets.QVBoxLayout()
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

        self.path_field=path_field
        
    def browse_gfile(self):
        fn=QtWidgets.QFileDialog.getOpenFileName(
                    self,'Position File',QtCore.QDir.homePath(),
                    'GCode File (*.gcode)')
        self.path_field.setText(fn[0])
    
class control_tab(QtWidgets.QWidget):
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        
        md = application_delegate.mouvment_delegate
        ld = application_delegate.laser_delegate
        cd =  application_delegate.camera_delegate
        #======================================================================
        #       Create Widgets
        #======================================================================
        
        monitor_switch = QtWidgets.QPushButton('Set')
        monitor_switch.setCheckable(True)
        
        laser_label = QtWidgets.QLabel("Laser")
        laser_label.setStyleSheet("font: bold large")
        laser_reconnect = QtWidgets.QPushButton('Reconnect')
        laser_switch = QtWidgets.QPushButton('Off')
        laser_switch.setCheckable(True)
        laser_switch.setChecked(ld.get_state())
        if ld.get_state():
            laser_switch.setText("On")
        laser_V_label = QtWidgets.QLabel("I [V]:")
        laser_setV = doubleSelector(ld.get_range(),ld.get_intensity())
        
        motor_label = QtWidgets.QLabel('Linear Stage')
        motor_label.setStyleSheet("font: bold large")
        motor_status = LightWidget()
        stage_motor_reconnect = QtWidgets.QPushButton('Reconnect')
        stage_cube_reconnect = QtWidgets.QPushButton('Reconnect')
        
        
        vel_motor_range = md.motor.get_velocityRange(0)
        vel_cube_range = md.piezzo.get_velocityRange(0)
        
        vel_motor_label = QtWidgets.QLabel('V [μm/s]:')
        vel_cube_label = QtWidgets.QLabel('V [μm/s]:')
        vel_motor_selector = doubleSelector(vel_motor_range, md.motor.velocity)
        vel_cube_selector = doubleSelector(vel_cube_range, md.piezzo.velocity)
        
        motor_Ranges =md.motor.positionRange
        
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
                                -motor_Ranges[i, 0], 3) for i in range(3)]
        for v, step in zip(validators, steps) :
            v.setNotation(QtGui.QDoubleValidator.StandardNotation)
            step.setValidator(v)
        
        goto_motor_button = QtWidgets.QPushButton("GO")
        getcurr_motor_button = QtWidgets.QPushButton("Get Current")
        
        cube_label = QtWidgets.QLabel('Piezzo Stage')
        cube_label.setStyleSheet("font: bold large")
        cube_status = LightWidget()
        
        cube_ranges = md.piezzo.positionRange
        cube_pos = md.piezzo.position
        cube_selectors = [doubleSelector(r, x) for r, x in zip(cube_ranges, 
                                                               cube_pos)]
        cube_labels = [QtWidgets.QLabel(s + ' [μm]: ') for s in AxisNames]
        
        goto_cube_button = QtWidgets.QPushButton("GO")
        getcurr_cube_button = QtWidgets.QPushButton("Get Current")
        
        cam_label = QtWidgets.QLabel('Camera')
        cam_label.setStyleSheet("font: bold large")
        cam_reconnect = QtWidgets.QPushButton('Reconnect')
        cam_range = cd.shutter_range()
        cam_init = cd.get_shutter()
        cam_exposure_label = QtWidgets.QLabel('Exp. [s]:')
        cam_exposure_selector = doubleSelector(cam_range, cam_init, isLog=True)
        cam_autoshutter = QtWidgets.QPushButton('Auto')
        cam_autoshutter.setCheckable(True)
        #======================================================================
        #     Layout    
        #======================================================================
        
        laser_H_layout = QtWidgets.QHBoxLayout()
        laser_H_layout.addWidget(laser_label)
        laser_H_layout.addWidget(laser_reconnect)
        
        laser_layout = QtWidgets.QHBoxLayout()
        laser_layout.addWidget(laser_V_label)
        laser_layout.addWidget(laser_setV)
        
        motor_H_layout = QtWidgets.QHBoxLayout()
        motor_H_layout.addWidget(motor_label)
        motor_H_layout.addWidget(motor_status)
        motor_H_layout.addWidget(stage_motor_reconnect)
        
        motor_layout = QtWidgets.QGridLayout()
        motor_layout.addWidget(vel_motor_label, 0, 0)
        motor_layout.addWidget(vel_motor_selector, 0, 1)
        for i in range(3):
            motor_layout.addWidget(motor_labels[i], 1+2*i, 0)
            motor_layout.addWidget(motor_selectors[i], 1+2*i, 1)
            layout = QtWidgets.QHBoxLayout()
            layout.addStretch()
            layout.addWidget(step_labels[i])
            layout.addWidget(steps[i])
            layout.addWidget(minuses[i])
            layout.addWidget(pluses[i])
            layout.addStretch()
            motor_layout.addLayout(layout, 2*(1+i), 0, 1, 2)
        
        motor_GO_layout = QtWidgets.QHBoxLayout()
        motor_GO_layout.addWidget(getcurr_motor_button)
        motor_GO_layout.addWidget(goto_motor_button)
        
        
        cube_H_layout = QtWidgets.QHBoxLayout()
        cube_H_layout.addWidget(cube_label)
        cube_H_layout.addWidget(cube_status)
        cube_H_layout.addWidget(stage_cube_reconnect)
        
        cube_layout = QtWidgets.QGridLayout()
        cube_layout.addWidget(vel_cube_label, 0, 0)
        cube_layout.addWidget(vel_cube_selector, 0, 1)
        for i in range(3):
            cube_layout.addWidget(cube_labels[i], 1+i, 0)
            cube_layout.addWidget(cube_selectors[i], 1+i, 1)
        
        cube_GO_layout = QtWidgets.QHBoxLayout()
        cube_GO_layout.addWidget(getcurr_cube_button)
        cube_GO_layout.addWidget(goto_cube_button)
        
        cam_H_layout = QtWidgets.QHBoxLayout()
        cam_H_layout.addWidget(cam_label)
        cam_H_layout.addWidget(cam_reconnect)
        
        cam_layout = QtWidgets.QHBoxLayout()
        cam_layout.addWidget(cam_exposure_label)
        cam_layout.addWidget(cam_exposure_selector)
        
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(motor_H_layout)
        main_layout.addLayout(motor_layout)
        main_layout.addLayout(motor_GO_layout)
        
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine);
        line.setFrameShadow(QtWidgets.QFrame.Sunken);
        main_layout.addWidget(line)

        main_layout.addLayout(cube_H_layout)
        main_layout.addLayout(cube_layout)
        main_layout.addLayout(cube_GO_layout)
        
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine);
        line.setFrameShadow(QtWidgets.QFrame.Sunken);
        main_layout.addWidget(line)
        
        main_layout.addLayout(laser_H_layout)
        main_layout.addLayout(laser_layout)
        main_layout.addWidget(laser_switch)
                
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine);
        line.setFrameShadow(QtWidgets.QFrame.Sunken);
        main_layout.addWidget(line)
        
        main_layout.addLayout(cam_H_layout)
        main_layout.addLayout(cam_layout)
        main_layout.addWidget(cam_autoshutter)
        
        main_layout.addStretch()
        
        self.setLayout(main_layout)
        #======================================================================
        #      Connections   
        #======================================================================
        laser_reconnect.clicked.connect(ld.reconnect)
        laser_switch.toggled.connect(ld.switch)
        laser_setV.newValue.connect(ld.set_intensity)
        
        stage_motor_reconnect.clicked.connect(md.motor.reconnect)
        stage_cube_reconnect.clicked.connect(md.piezzo.reconnect)
        
        goto_motor_button.clicked.connect(self.goto_motor)
            
        goto_cube_button.clicked.connect(lambda: md.piezzo.goto_position(
                                    [s.getValue() for s in cube_selectors]))
        
        vel_motor_selector.newValue.connect(md.motor.set_velocity)
        
        vel_cube_selector.newValue.connect(md.piezzo.set_velocity)
        
        cam_reconnect.clicked.connect(cd.reconnect)
        
        cam_exposure_selector.newValue.connect(cd.set_shutter)
        
        cd.shutterState.connect(self.setCamShutter)
        
        def switchLaserText(on):
            if on:
                laser_switch.setText("On")
            else:
                laser_switch.setText("Off")
        
        laser_switch.toggled.connect(switchLaserText)
        
        ld.newIntensity.connect(laser_setV.setValue)
        ld.switched.connect(laser_switch.setChecked)
        
        cd.newShutter.connect(cam_exposure_selector.setValue)
        
        application_delegate.newMotorState.connect(motor_status.setOn)
        application_delegate.newCubeState.connect(cube_status.setOn)
        
        for i in range(3):
            pluses[i].clicked.connect(partial(self.step, i, 1))
            minuses[i].clicked.connect(partial(self.step, i, -1))
            
        getcurr_cube_button.clicked.connect(self.updateCube)
        getcurr_motor_button.clicked.connect(self.update_motor)
        
        application_delegate.update_motor.connect(self.update_motor)
        
        application_delegate.newPosition.connect(self.updatePos)
        
        cam_autoshutter.toggled.connect(cd.autoShutter)
        
        def setMotorPos(motor_selectors, ranges):
            for s, r in zip(motor_selectors, ranges):
                s.setRange(*r,3)
            
        application_delegate.newPosRange.connect(partial(setMotorPos, 
                                                         motor_selectors))
        
        #======================================================================
        #         Save variables
        #======================================================================
        self.application_delegate = application_delegate
        self.vel_motor_selector = vel_motor_selector
        self.motor_selectors = motor_selectors
        self.vel_cube_selector = vel_cube_selector
        self.cube_selectors = cube_selectors
        self.cam_autoshutter = cam_autoshutter
        self.steps = steps
    
    def setCamShutter(self, on):
        if on:
            txt = "Auto: On"
        else:
            txt = "Auto: Off"
        self.cam_autoshutter.setText(txt)
        
    def goto_motor(self):
            self.application_delegate.mouvment_delegate.motor.goto_position(
                    [s.getValue() for s in self.motor_selectors])
            
    def step(self, axis, d):
        step = d*float(self.steps[axis].text())
        selector = self.motor_selectors[axis]
        val = selector.getValue()
        selector.setValue(val+step)
        self.goto_motor()
        
    def update_motor(self):
        V = self.application_delegate.mouvment_delegate.motor.velocity
        Pos = self.application_delegate.mouvment_delegate.motor.position
        self.vel_motor_selector.setValue(V)
        [s.setValue(x) for s, x in zip(self.motor_selectors, Pos)]
        
        
    def updateCube(self):
        md = self.application_delegate.mouvment_delegate
        V = md.piezzo.velocity
        Pos = md.piezzo.position
        self.vel_cube_selector.setValue(V)
        [s.setValue(x) for s, x in zip(self.cube_selectors, Pos)]
        
    def updatePos(self):
        self.update_motor()
        self.updateCube()
        
        
        
        
class secondary_widget(QtWidgets.QWidget):
    
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        #======================================================================
        #       Create Widgets
        #======================================================================
        
        ESTOP_button=QtWidgets.QPushButton("EMERGENCY STOP")
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
        
        
        main_layout = QtWidgets.QGridLayout(self)
        main_layout.addWidget(live_button,0,0)
        main_layout.addWidget(draw_button,0,1)
        main_layout.addWidget(clear_button,1,0)
        main_layout.addWidget(bg_button,1,1)
        main_layout.addWidget(ESTOP_button,0,3,2,3)
        main_layout.addWidget(save_im_button,0,2)
        main_layout.addWidget(save_fig_button,1,2)
        
        self.setLayout(main_layout)
        #======================================================================
        #      Connections   
        #======================================================================
        
        
        
        ESTOP_button.clicked.connect(application_delegate.ESTOP)
        clear_button.clicked.connect(application_delegate.clearFig)
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
        self.live_button=live_button
        self.draw_button=draw_button
        
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
        
        
class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        
        #Init everything
        QtWidgets.QMainWindow.__init__(self)
        
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")
        
        #create menu
        self.file_menu = QtWidgets.QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                                 QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QtWidgets.QMenu('&Help', self)
#        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&About', self.about)

#        self.statusBar().showMessage("Hello", 2000)

        #Create canevas
        imCanvas=imageCanvas()
        
        #create appication delegate
        self.application_delegate=application_delegate(imCanvas)
        
        
        #======================================================================
        #       Create Widgets
        #======================================================================
        
        #Create main widget
        self.main_widget = QtWidgets.QWidget(self)
        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)
        
        #Create tab widget
        tabs_widget=QtWidgets.QTabWidget()

        tabs_widget.addTab(coordinates_tab(self.application_delegate),
                           'Coordinates')
        tabs_widget.addTab(write_tab(self.application_delegate),
                           'Write')
        
        tabs_widget.setMaximumWidth(300)
        
        control_widget = control_tab(self.application_delegate)
        #======================================================================
        #     Layout    
        #======================================================================
        vertical = QtWidgets.QVBoxLayout()
        vertical.addWidget(imCanvas,1)
        vertical.addWidget(secondary_widget(self.application_delegate))
        
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
        
