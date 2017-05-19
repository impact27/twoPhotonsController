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
        
    def imshow(self, im , vmax = None):
        self.figure.clear()
        self._axes = self.figure.add_subplot(111)
        self._imhandle=self._axes.imshow(im, vmax = vmax)
        self._axes.axis('image')
        self.figure.colorbar(self._imhandle)
        self.draw()
        
    def frameshow(self, im):
        if self._imhandle is not None:
            self._imhandle.set_data(im)
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
        
        
#==============================================================================
# Tabs            
#==============================================================================
        
class orientation_tab(QtWidgets.QWidget):
    
    #Signals
    deleterow = QtCore.pyqtSignal(int)
    displayrow = QtCore.pyqtSignal(int)
    newposition = QtCore.pyqtSignal(float, float)
    
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        
        #======================================================================
        #       Create Widgets
        #======================================================================
        
        coord_label=QtWidgets.QLabel("Position in master coordinates [μm]")
        
        Xinput=QtWidgets.QLineEdit()
        Xinput.setValidator(QtGui.QDoubleValidator(-1e6,1e6,3))
        Xinput.setText('0')
        
        Yinput=QtWidgets.QLineEdit()
        Yinput.setValidator(QtGui.QDoubleValidator(-1e6,1e6,3))
        Yinput.setText('0')
        
        newpos_button=QtWidgets.QPushButton("New Reference Position")
        
        pos_list=QtWidgets.QTableWidget()
        pos_list.setColumnCount(3)
        pos_list.setHorizontalHeaderLabels(['Xmaster','Xstage','Delete'])
        pos_list.setColumnWidth(0,100)
        pos_list.setColumnWidth(1,100)
        pos_list.setColumnWidth(2,40)
        pos_list.horizontalHeader().setStretchLastSection(True)
        
        clear_list_button=QtWidgets.QPushButton("Clear List")
        validate_button=QtWidgets.QPushButton("Validate")
        
        
        correction_label = QtWidgets.QLabel('')
        self.correction_label = correction_label
        self.updateCorrection(
                application_delegate.mouvment_delegate.get_XY_correction())
        
        correction_reset = QtWidgets.QPushButton('Reset')
        correction_save = QtWidgets.QPushButton('Save')
        correction_load = QtWidgets.QPushButton('Load')
        
        #======================================================================
        #     Layout    
        #======================================================================
        
        coord= QtWidgets.QHBoxLayout()
        coord.addWidget(QtWidgets.QLabel("X:"))
        coord.addWidget(Xinput)
        coord.addWidget(QtWidgets.QLabel("Y:"))
        coord.addWidget(Yinput)
        
        hbuttons=QtWidgets.QHBoxLayout()
        hbuttons.addWidget(validate_button)
        hbuttons.addWidget(clear_list_button)
        
        load_layout = QtWidgets.QHBoxLayout()
        load_layout.addWidget(correction_save)
        load_layout.addWidget(correction_load)
        
        correction_layout = QtWidgets.QVBoxLayout()
        correction_layout.addWidget(correction_label)
        correction_layout.addWidget(correction_reset)
        correction_layout.addLayout(load_layout)
        
        main_layout=QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(coord_label)
        main_layout.addLayout(coord)
        main_layout.addWidget(newpos_button)
        main_layout.addWidget(pos_list)
        main_layout.addLayout(hbuttons)
        main_layout.addLayout(correction_layout)
        self.setLayout(main_layout)
        
        #======================================================================
        #      Connections   
        #======================================================================
        
        pos_list.cellClicked.connect(self.cellClicked)
        pos_list.verticalHeader().sectionClicked.connect(self.rowClicked)
        
        
        self.deleterow.connect(
                application_delegate.orientation_delegate.del_position)
        self.displayrow.connect(
                application_delegate.orientation_delegate.displayrow)
        self.newposition.connect(
                application_delegate.orientation_delegate.newXYpos)
        
        newpos_button.clicked.connect(self.newPosClicked)
        clear_list_button.clicked.connect(
                application_delegate.orientation_delegate.clear_positions)
        validate_button.clicked.connect(
                application_delegate.correct_orientation)
        
        application_delegate.orientation_delegate.updatelist.connect(
                self.updateList)
        
        application_delegate.orientationCorrected.connect(
                self.updateCorrection)
        
        correction_reset.clicked.connect(
                application_delegate.reset_orientation)
        
        md=application_delegate.mouvment_delegate

        correction_save.clicked.connect(lambda: md.save_XY_correction())
        correction_load.clicked.connect(lambda: md.load_XY_correction())
        #======================================================================
        #         Save variables
        #======================================================================
        
        self.xpos = Xinput
        self.ypos = Yinput
        self.pos_list = pos_list
        
    def newPosClicked(self,checked):
        self.newposition.emit(float(self.xpos.text()),float(self.ypos.text()))
        
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
            Xm=d['Xmaster']
            Xs=d['Xstage']
            self.addRow(Xm,Xs)
        
    def addRow(self, Xmaster, Xstage):
        """Assume X are [x,y]"""
        row=self.pos_list.rowCount()
        self.pos_list.insertRow(row)
        
        Xm_label=QtWidgets.QLabel("[{:.0f},\n {:.0f}]".format(*Xmaster))
        Xm_label.setAlignment(QtCore.Qt.AlignCenter)
        
        Xs_label=QtWidgets.QLabel("[{:.0f},\n {:.0f}]".format(*Xstage))
        Xs_label.setAlignment(QtCore.Qt.AlignCenter)
        
        Delete=QtWidgets.QLabel('Delete')
        Delete.setStyleSheet("background-color: red")
        Delete.setAlignment(QtCore.Qt.AlignCenter)
        
        self.pos_list.setCellWidget(row,0,Xm_label)
        self.pos_list.setCellWidget(row,1,Xs_label)
        self.pos_list.setCellWidget(row,2,Delete)
        
    def updateCorrection(self, coeff):
        self.correction_label.setText(
                'θ:\t{:.3f}π\nXo:\t[{:.3f}, {:.3f}]μm'.format(coeff[0]/np.pi,
                                                             *coeff[1:]))
        
    
class layout_wrapper(QtWidgets.QWidget):
    def __init__(self, layout, *args, **kwargs):       
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        self.setLayout(layout)
        
class tilt_tab(QtWidgets.QWidget):
    
    deleterow = QtCore.pyqtSignal(int)
    displayrow = QtCore.pyqtSignal(int)
    plotCurveRow = QtCore.pyqtSignal(int)
    
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        
        #======================================================================
        #       Create Widgets
        #======================================================================
        
        Xinput = QtWidgets.QLineEdit('0')
        X_validator = QtGui.QDoubleValidator(0,100,3)
        Xinput.setValidator(X_validator)
        
        Yinput = QtWidgets.QLineEdit('0')
        Y_validator = QtGui.QDoubleValidator(0,100,3)
        Yinput.setValidator(Y_validator)
        
        newpos_button = QtWidgets.QPushButton("New Reference Position")
        
        path_field = QtWidgets.QLineEdit()
        browse_button = QtWidgets.QPushButton('Browse')
        pos_file_button = QtWidgets.QPushButton('Load Positions File')
        
        pos_list=QtWidgets.QTableWidget()
        pos_list.setColumnCount(3)
        pos_list.setHorizontalHeaderLabels(['Position','Z','Delete'])
        pos_list.setColumnWidth(0,90)
        pos_list.setColumnWidth(1,40)
        pos_list.setColumnWidth(2,40)
        pos_list.horizontalHeader().setStretchLastSection(True)
        
        clear_list_button = QtWidgets.QPushButton("Clear List")
        validate_button = QtWidgets.QPushButton("Validate") 
        raise_button = QtWidgets.QPushButton("Raise cube for manual focusing")
        
        correction_label = QtWidgets.QLabel('')
        self.correction_label = correction_label
        self.updateCorrection(
                application_delegate.mouvment_delegate.get_Z_correction())
        
        correction_reset = QtWidgets.QPushButton('Reset')
        correction_save = QtWidgets.QPushButton('Save')
        correction_load = QtWidgets.QPushButton('Load')
        #======================================================================
        #     Layout    
        #======================================================================
        
        coord= QtWidgets.QHBoxLayout()
        coord.addWidget(QtWidgets.QLabel("X:"))
        coord.addWidget(Xinput)
        coord.addWidget(QtWidgets.QLabel("Y:"))
        coord.addWidget(Yinput)
        
        tab1Layout=QtWidgets.QVBoxLayout()
        tab1Layout.addLayout(coord)
        tab1Layout.addWidget(newpos_button)
        
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(path_field)
        path_layout.addWidget(browse_button)
        
        tab2Layout=QtWidgets.QVBoxLayout()
        tab2Layout.addLayout(path_layout)
        tab2Layout.addWidget(pos_file_button)
        
        tabs_widget=QtWidgets.QTabWidget()
        tabs_widget.addTab(layout_wrapper(tab2Layout), 'File')
        tabs_widget.addTab(layout_wrapper(tab1Layout), 'Manual')
        
        tabs_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Minimum)
        
        valLayout=QtWidgets.QHBoxLayout()
        valLayout.addWidget(validate_button)
        valLayout.addWidget(clear_list_button)
        
        load_layout = QtWidgets.QHBoxLayout()
        load_layout.addWidget(correction_save)
        load_layout.addWidget(correction_load)
        
        correction_layout = QtWidgets.QVBoxLayout()
        correction_layout.addWidget(correction_label)
        correction_layout.addWidget(correction_reset)
        correction_layout.addLayout(load_layout)
        
        main_layout=QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(tabs_widget)
        main_layout.addWidget(raise_button)
        main_layout.addWidget(pos_list)
        main_layout.addLayout(valLayout)
        main_layout.addLayout(correction_layout)
        self.setLayout(main_layout)
        
        #======================================================================
        #      Connections   
        #======================================================================
        td = application_delegate.tilt_delegate
        
        pos_list.cellClicked.connect(self.cellClicked)
        pos_list.verticalHeader().sectionClicked.connect(self.rowClicked)
        
        newpos_button.clicked.connect( lambda: td.add_position(
                                                    float(Xinput.text()),
                                                    float(Yinput.text())))
        
        browse_button.clicked.connect(self.openfile)
            
        pos_file_button.clicked.connect( lambda: 
                                            td.load_file(path_field.text()))
            
        clear_list_button.clicked.connect(td.clear_positions)
        validate_button.clicked.connect(td.validate_positions)
        
        self.deleterow.connect(td.deleteIdx)
        self.displayrow.connect(td.display_row)
        self.plotCurveRow.connect(td.plotCurveRow)
        td.updatelist.connect(self.updateList)
        raise_button.clicked.connect(application_delegate.manualFocus)
        
        application_delegate.tiltCorrected.connect(
                self.updateCorrection)
        
        correction_reset.clicked.connect(
                application_delegate.reset_tilt)
        
        application_delegate.newXRange.connect(X_validator.setRange)
        application_delegate.newYRange.connect(Y_validator.setRange)
        
        md = application_delegate.mouvment_delegate
        correction_save.clicked.connect(lambda: md.save_Z_correction())
        correction_load.clicked.connect(lambda: md.load_Z_correction())
        
        #======================================================================
        #         Save variables
        #======================================================================
        
        self.xinput=Xinput
        self.yinput=Yinput
        self.fninput=path_field
        self.pos_list=pos_list
        self.path_field = path_field
        
    def openfile(self):
        fn=QtWidgets.QFileDialog.getOpenFileName(
                    self,'Position File',QtCore.QDir.homePath())
        self.path_field.setText(fn[0])
        
    def cellClicked(self, row,column):
        if column==2:
            self.deleterow.emit(row)
        elif column==1:
            self.plotCurveRow.emit(row)
        else:
            self.displayrow.emit(row)
            
    def rowClicked(self, row):
        self.displayrow.emit(row)
        
    def updateList(self,dictlist):
        self.pos_list.clearContents()
        self.pos_list.setRowCount(0)
        for d in dictlist:
            Pos=d['X']
            Z=d['Z']
            self.addRow(Pos,Z)
        
    def addRow(self, Position, Z):
        """Assume X are [x,y]"""
        row=self.pos_list.rowCount()
        self.pos_list.insertRow(row)
        
        pos_label=QtWidgets.QLabel("[{:.0f},\n {:.0f}]".format(*Position))
        pos_label.setAlignment(QtCore.Qt.AlignCenter)
        
        ztext="{:.2f}".format(Z)
        if np.isnan(Z):
            ztext='?'
        z_label=QtWidgets.QLabel(ztext)
        z_label.setAlignment(QtCore.Qt.AlignCenter)
        
        Delete=QtWidgets.QLabel('Delete')
        Delete.setStyleSheet("background-color: red")
        Delete.setAlignment(QtCore.Qt.AlignCenter)
        
        self.pos_list.setCellWidget(row,0,pos_label)
        self.pos_list.setCellWidget(row,1,z_label)
        self.pos_list.setCellWidget(row,2,Delete)
        
    def updateCorrection(self, coeff):
        self.correction_label.setText(
                '{:.3e}X + {:.3e}Y\n+ {:.3f}μm'.format(*coeff))
        
    
class write_tab(QtWidgets.QWidget):
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        #======================================================================
        #       Create Widgets
        #======================================================================
        
        Origin_label = QtWidgets.QLabel('Origin:')
        
        Xinput=QtWidgets.QLineEdit('0')
        X_validator = QtGui.QDoubleValidator(0,100,3)
        Xinput.setValidator(X_validator)
        
        Yinput=QtWidgets.QLineEdit('0')
        Y_validator = QtGui.QDoubleValidator(0,100,3)
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
        
        application_delegate.newXRange.connect(X_validator.setRange)
        application_delegate.newYRange.connect(Y_validator.setRange)
        
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
        laser_V_label = QtWidgets.QLabel("I [V]:")
        laser_setV = doubleSelector(ld.get_range(),ld.get_intensity())
        
        XY_label = QtWidgets.QLabel('Linear Stage')
        XY_label.setStyleSheet("font: bold large")
        XY_status = LightWidget()
        stage_XY_reconnect = QtWidgets.QPushButton('Reconnect')
        stage_cube_reconnect = QtWidgets.QPushButton('Reconnect')
        
        
        vel_XY_range = md.get_XY_VelRange(0)
        vel_cube_range = md.get_cube_VelRange(0)
        
        vel_XY_label = QtWidgets.QLabel('V [μm/s]:')
        vel_cube_label = QtWidgets.QLabel('V [μm/s]:')
        vel_XY_selector = doubleSelector(vel_XY_range, md.get_XY_velocity())
        vel_cube_selector =doubleSelector(vel_cube_range, md.get_cube_velocity())
        
        X_XY_Range =md.get_XY_PosRange(0)
        Y_XY_Range =md.get_XY_PosRange(1)
        
        X_XY_label = QtWidgets.QLabel('X [μm]: ')
        Y_XY_label = QtWidgets.QLabel('Y [μm]: ')
        x, y = md.get_XY_position()
        X_XY_selector = doubleSelector(X_XY_Range, x)
        Y_XY_selector = doubleSelector(Y_XY_Range, y)
        
        X_step_label = QtWidgets.QLabel('X Step [μm]: ')
        X_plus = QtWidgets.QPushButton(' + ')
        X_step = QtWidgets.QLineEdit('1')
        validator=QtGui.QDoubleValidator(0,X_XY_Range[-1]-X_XY_Range[0],3)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        X_step.setValidator(validator)
        X_minus = QtWidgets.QPushButton(' - ')
        
        Y_step_label = QtWidgets.QLabel('Y Step [μm]: ')
        Y_plus = QtWidgets.QPushButton(' + ')
        Y_step = QtWidgets.QLineEdit('1')
        validator=QtGui.QDoubleValidator(0,Y_XY_Range[-1]-Y_XY_Range[0],3)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        Y_step.setValidator(validator)
        Y_minus = QtWidgets.QPushButton(' - ')
        
        goto_XY_button = QtWidgets.QPushButton("GO")
        getcurr_XY_button = QtWidgets.QPushButton("Get Current")
        
        cube_label = QtWidgets.QLabel('Piezzo Stage')
        cube_label.setStyleSheet("font: bold large")
        cube_status = LightWidget()
        X_cube_Range =md.get_cube_PosRange(0)
        Y_cube_Range =md.get_cube_PosRange(1)
        Z_cube_Range =md.get_cube_PosRange(3)
        
        X_cube_label = QtWidgets.QLabel('X [μm]: ')
        Y_cube_label = QtWidgets.QLabel('Y [μm]: ')
        Z_cube_label = QtWidgets.QLabel('Z [μm]: ')
        x, y, z = md.get_cube_position()
        X_cube_selector = doubleSelector(X_cube_Range, x)
        Y_cube_selector = doubleSelector(Y_cube_Range, y)
        Z_cube_selector = doubleSelector(Z_cube_Range, y)
        
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
        
        XY_H_layout = QtWidgets.QHBoxLayout()
        XY_H_layout.addWidget(XY_label)
        XY_H_layout.addWidget(XY_status)
        XY_H_layout.addWidget(stage_XY_reconnect)
        
        X_layout = QtWidgets.QHBoxLayout()
        X_layout.addStretch()
        X_layout.addWidget(X_step_label)
        X_layout.addWidget(X_step)
        X_layout.addWidget(X_minus)
        X_layout.addWidget(X_plus)
        X_layout.addStretch()
        
        Y_layout = QtWidgets.QHBoxLayout()
        Y_layout.addStretch()
        Y_layout.addWidget(Y_step_label)
        Y_layout.addWidget(Y_step)
        Y_layout.addWidget(Y_minus)
        Y_layout.addWidget(Y_plus)
        Y_layout.addStretch()
        
        XY_layout = QtWidgets.QGridLayout()
        XY_layout.addWidget(vel_XY_label, 0, 0)
        XY_layout.addWidget(vel_XY_selector, 0, 1)
        XY_layout.addWidget(X_XY_label, 1, 0)
        XY_layout.addWidget(Y_XY_label, 3, 0)
        XY_layout.addWidget(X_XY_selector, 1, 1)
        XY_layout.addWidget(Y_XY_selector, 3, 1)
        XY_layout.addLayout(X_layout, 2, 0, 1, 2)
        XY_layout.addLayout(Y_layout, 4, 0, 1, 2)
        
        XY_GO_layout = QtWidgets.QHBoxLayout()
        XY_GO_layout.addWidget(getcurr_XY_button)
        XY_GO_layout.addWidget(goto_XY_button)
        
        
        cube_H_layout = QtWidgets.QHBoxLayout()
        cube_H_layout.addWidget(cube_label)
        cube_H_layout.addWidget(cube_status)
        cube_H_layout.addWidget(stage_cube_reconnect)
        
        cube_layout = QtWidgets.QGridLayout()
        cube_layout.addWidget(vel_cube_label, 0, 0)
        cube_layout.addWidget(vel_cube_selector, 0, 1)
        cube_layout.addWidget(X_cube_label, 1, 0)
        cube_layout.addWidget(Y_cube_label, 2, 0)
        cube_layout.addWidget(Z_cube_label, 3, 0)
        cube_layout.addWidget(X_cube_selector, 1, 1)
        cube_layout.addWidget(Y_cube_selector, 2, 1)
        cube_layout.addWidget(Z_cube_selector, 3, 1)
        
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
        main_layout.addLayout(XY_H_layout)
        main_layout.addLayout(XY_layout)
        main_layout.addLayout(XY_GO_layout)
        
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
        
        stage_XY_reconnect.clicked.connect(md.XY_reconnect)
        stage_cube_reconnect.clicked.connect(md.cube_reconnect)
        
        goto_XY_button.clicked.connect(self.goto_XY)
            
        goto_cube_button.clicked.connect(lambda:
            application_delegate.goto_cube_position(
                    X_cube_selector.getValue(),
                    Y_cube_selector.getValue(),
                    Z_cube_selector.getValue()))
        
        vel_XY_selector.newValue.connect( 
            application_delegate.mouvment_delegate.set_XY_velocity)
        
        vel_cube_selector.newValue.connect(
            application_delegate.mouvment_delegate.set_cube_velocity)
        
        cam_reconnect.clicked.connect(cd.reconnect)
        
        cam_exposure_selector.newValue.connect(cd.set_shutter)
        
        def switchLaserText(on):
            if on:
                laser_switch.setText("On")
            else:
                laser_switch.setText("Off")
        
        laser_switch.toggled.connect(switchLaserText)
        
        ld.newIntensity.connect(laser_setV.setValue)
        ld.switched.connect(laser_switch.setChecked)
        
        cd.newShutter.connect(cam_exposure_selector.setValue)
        
        application_delegate.newXYState.connect(XY_status.setOn)
        application_delegate.newCubeState.connect(cube_status.setOn)
        
        X_plus.clicked.connect(lambda: self.step('X',float(X_step.text())))
        X_minus.clicked.connect(lambda: self.step('X',-float(X_step.text())))
        Y_plus.clicked.connect(lambda: self.step('Y',float(Y_step.text())))
        Y_minus.clicked.connect(lambda: self.step('Y',-float(Y_step.text())))
        
        getcurr_cube_button.clicked.connect(self.updateCube)
        getcurr_XY_button.clicked.connect(self.updateXY)
        
        application_delegate.updateXY.connect(self.updateXY)
        
        application_delegate.newPosition.connect(self.updatePos)
        
        cam_autoshutter.toggled.connect(cd.autoShutter)
        
        application_delegate.newXRange.connect(X_XY_selector.setRange)
        application_delegate.newYRange.connect(Y_XY_selector.setRange)
        
        #======================================================================
        #         Save variables
        #======================================================================
        self.application_delegate = application_delegate
        self.vel_XY_selector = vel_XY_selector
        self.X_XY_selector = X_XY_selector
        self.Y_XY_selector = Y_XY_selector
        self.vel_cube_selector = vel_cube_selector
        self.X_cube_selector = X_cube_selector
        self.Y_cube_selector = Y_cube_selector
        self.Z_cube_selector = Z_cube_selector
        
    def goto_XY(self):
            self.application_delegate.goto_XY_position(
                    self.X_XY_selector.getValue(),
                    self.Y_XY_selector.getValue())
            
    def step(self, axis, step):
        if axis == 'X':
            selector = self.X_XY_selector
        elif axis == 'Y':
            selector = self.Y_XY_selector
        else:
            return
        
        val = selector.getValue()
        selector.setValue(val+step)
        self.goto_XY()
        
    def updateXY(self):
        V = self.application_delegate.mouvment_delegate.get_XY_velocity()
        X, Y = self.application_delegate.mouvment_delegate.get_XY_position()
        self.vel_XY_selector.setValue(V)
        self.X_XY_selector.setValue(X)
        self.Y_XY_selector.setValue(Y)
        
        
    def updateCube(self):
        md = self.application_delegate.mouvment_delegate
        V = md.get_cube_velocity()
        X, Y, Z = md.get_cube_position()
        self.vel_cube_selector.setValue(V)
        self.X_cube_selector.setValue(X)
        self.Y_cube_selector.setValue(Y)
        self.Z_cube_selector.setValue(Z)
        
    def updatePos(self):
        self.updateXY()
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
        
        clear_button = QtWidgets.QPushButton('Clear Graph')
        
        #======================================================================
        #     Layout    
        #======================================================================
        
        
        main_layout = QtWidgets.QGridLayout(self)
        main_layout.addWidget(live_button,0,0)
        main_layout.addWidget(draw_button,0,1)
        main_layout.addWidget(clear_button,1,0,1,2)
        main_layout.addWidget(ESTOP_button,0,2,2,3)
        
        self.setLayout(main_layout)
        #======================================================================
        #      Connections   
        #======================================================================
        
        
        
        ESTOP_button.clicked.connect(application_delegate.ESTOP)

        clear_button.clicked.connect(application_delegate.clearFig)
        
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

        tabs_widget.addTab(orientation_tab(self.application_delegate),
                           'Orientation')
        tabs_widget.addTab(tilt_tab(self.application_delegate),
                           'Tilt')
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
        
