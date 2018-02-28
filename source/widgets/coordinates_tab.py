# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 16:51:32 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets
import numpy as np


class Layout_wrapper(QtWidgets.QWidget):
    def __init__(self, layout, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        self.setLayout(layout)


class Coordinates_tab(QtWidgets.QWidget):

    deleterow = QtCore.pyqtSignal(int)
    displayrow = QtCore.pyqtSignal(int)

    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        #======================================================================
        #       Create Widgets
        #======================================================================

        motor_label = QtWidgets.QLabel("Motor")
        motor_label.setStyleSheet("font: bold large")
        
        Xinput = QtWidgets.QLineEdit('0, 0, 0')
#         X_validator = QtGui.QDoubleValidator(-1,100,3)
#         Xinput.setValidator(X_validator)
        newpos_button = QtWidgets.QPushButton("New Reference Position")

        path_field = QtWidgets.QLineEdit()
        pos_file_button = QtWidgets.QPushButton('Load Positions File')

        pos_list = QtWidgets.QTableWidget()
        pos_list.setColumnCount(3)
        pos_list.setHorizontalHeaderLabels(['Xm', 'Xs', 'Delete'])
        pos_list.setColumnWidth(0, 90)
        pos_list.setColumnWidth(1, 90)
        pos_list.setColumnWidth(2, 40)
        pos_list.horizontalHeader().setStretchLastSection(True)
        pos_list.verticalHeader().setDefaultSectionSize(48)

        clear_list_button = QtWidgets.QPushButton("Clear List")
        validate_button = QtWidgets.QPushButton("Process next Position")
        save_errors = QtWidgets.QPushButton('Save Errors')
        
        offset_label = QtWidgets.QLabel("Offset Position:")
        offset_input = QtWidgets.QLineEdit("0, 0, 0")
        offset_button = QtWidgets.QPushButton("Move Origin")
        

        correction_label_motor = QtWidgets.QLabel('')
        self.correction_label_motor = correction_label_motor
        
        correction_reset_motor = QtWidgets.QPushButton('Reset')
        correction_reset_piezzo = QtWidgets.QPushButton('Reset')
        correction_save = QtWidgets.QPushButton('Save')
        correction_load = QtWidgets.QPushButton('Load')
        
        
        
        piezzo_label = QtWidgets.QLabel("Piezzo")
        piezzo_label.setStyleSheet("font: bold large")
        
        piezzo_plane_button = QtWidgets.QPushButton('Piezzo Plane')
        
        correction_label_piezzo = QtWidgets.QLabel('')
        self.correction_label_piezzo = correction_label_piezzo

        #======================================================================
        #     Layout
        #======================================================================

        coord = QtWidgets.QHBoxLayout()
        coord.addWidget(QtWidgets.QLabel("X (x, y, z):"))
        coord.addWidget(Xinput)

        tab1Layout = QtWidgets.QVBoxLayout()
        tab1Layout.addLayout(coord)
        tab1Layout.addWidget(newpos_button)

        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(path_field)

        tab2Layout = QtWidgets.QVBoxLayout()
        tab2Layout.addLayout(path_layout)
        tab2Layout.addWidget(pos_file_button)

        tabs_widget = QtWidgets.QTabWidget()
        tabs_widget.addTab(Layout_wrapper(tab2Layout), 'File')
        tabs_widget.addTab(Layout_wrapper(tab1Layout), 'Manual')

        tabs_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                  QtWidgets.QSizePolicy.Minimum)

        

        offset_layout = QtWidgets.QHBoxLayout()
        offset_layout.addWidget(offset_label)
        offset_layout.addWidget(offset_input)

        

        hbuttons = QtWidgets.QHBoxLayout()
        hbuttons.addWidget(save_errors)
        hbuttons.addWidget(clear_list_button)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(motor_label)
        main_layout.addWidget(tabs_widget)
        main_layout.addWidget(pos_list)
        main_layout.addWidget(validate_button)
        main_layout.addLayout(hbuttons)
        
        correction_layout = QtWidgets.QVBoxLayout()
        correction_layout.addLayout(offset_layout)
        correction_layout.addWidget(offset_button)
        main_layout.addLayout(correction_layout)
        
        main_layout.addWidget(correction_label_motor)
        main_layout.addWidget(correction_reset_motor)
        
        
        
        
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)
        
        main_layout.addWidget(piezzo_label)
        main_layout.addWidget(piezzo_plane_button)
        main_layout.addWidget(correction_label_piezzo)
        main_layout.addWidget(correction_reset_piezzo)
        
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)
        
        load_layout = QtWidgets.QHBoxLayout()
        load_layout.addWidget(correction_save)
        load_layout.addWidget(correction_load)
        main_layout.addLayout(load_layout)
        
        self.setLayout(main_layout)

        #======================================================================
        #      Connections
        #======================================================================
        cd = application_delegate.coordinates_delegate
        md = application_delegate.mouvment_delegate

        self.updateCorrection_motor(md.motor.corrections)
        self.updateCorrection_piezzo(md.piezzo.corrections)

        piezzo_plane_button.clicked.connect(cd.piezzo_plane)
        pos_list.cellClicked.connect(self.cellClicked)
        pos_list.verticalHeader().sectionClicked.connect(self.rowClicked)

        newpos_button.clicked.connect(lambda: cd.add_position(
            np.fromstring(Xinput.text(), sep=',')))

        pos_file_button.clicked.connect(self.openfile)

        clear_list_button.clicked.connect(cd.clear_positions)
        validate_button.clicked.connect(cd.processPos)

        self.deleterow.connect(cd.del_position)
        self.displayrow.connect(cd.displayrow)
        cd.updatelist.connect(self.updateList)

        md.motor.coordinatesCorrected.connect(self.updateCorrection_motor)
        md.piezzo.coordinatesCorrected.connect(self.updateCorrection_piezzo)
        
        correction_reset_motor.clicked.connect(md.motor.reset_corrections)
        correction_reset_piezzo.clicked.connect(md.piezzo.reset_corrections)

        md = application_delegate.mouvment_delegate
        correction_save.clicked.connect(md.save_corrections)
        correction_load.clicked.connect(md.load_corrections)

        save_errors.clicked.connect(cd.save_errors)

        offset_button.clicked.connect(lambda:
            application_delegate.mouvment_delegate.motor.offset_origin(
                    np.fromstring(offset_input.text(), sep=',')))

        #======================================================================
        #         Save variables
        #======================================================================

        self.xinput = Xinput
        self.fninput = path_field
        self.pos_list = pos_list
        self.path_field = path_field
        self.cd = cd

    def openfile(self):
        fn = self.path_field.text()

        check = QtCore.QFileInfo(fn)

        if not check.exists() or not check.isFile():
            fn = QtWidgets.QFileDialog.getOpenFileName(
                self, 'Position File', QtCore.QDir.homePath())[0]
            self.path_field.setText(fn)

        self.cd.load_list(fn)

    def cellClicked(self, row, column):
        if column == 2:
            self.deleterow.emit(row)
        else:
            self.displayrow.emit(row)

    def rowClicked(self, row):
        self.displayrow.emit(row)

    def updateList(self, dictlist):
        self.pos_list.clearContents()
        self.pos_list.setRowCount(0)
        for d in dictlist:
            Xm = d['Xm']
            Xs = d['Xs']
            self.addRow(Xm, Xs)

    def addRow(self, Xm, Xs):
        """Assume X are [x,y]"""
        row = self.pos_list.rowCount()
        self.pos_list.insertRow(row)

        Xmtext = "[{:.1f},\n {:.1f},\n {:.1f}]".format(*Xm)
        Xm_label = QtWidgets.QLabel(Xmtext)
        Xm_label.setAlignment(QtCore.Qt.AlignCenter)

        if Xs is None:
            Xstext = '?'
        else:
            Xstext = "[{:.1f},\n {:.1f},\n {:.1f}]".format(*Xs)
        Xs_label = QtWidgets.QLabel(Xstext)
        Xs_label.setAlignment(QtCore.Qt.AlignCenter)

        Delete = QtWidgets.QLabel('X')
        Delete.setStyleSheet("background-color: red")
        Delete.setAlignment(QtCore.Qt.AlignCenter)

        self.pos_list.setCellWidget(row, 0, Xm_label)
        self.pos_list.setCellWidget(row, 1, Xs_label)
        self.pos_list.setCellWidget(row, 2, Delete)

    def _updateCorrection(self, corrections, label):
        text = ("Offset: {offset}\n"
                "Slope: {slope_x:.3g}X + {slope_y:.3g}Y\n"
                "Rotation angle: {rotation_angle:.5g}π\n"
                "Stage diff angle: {stage_angle:.5g}π".format(
                        offset=corrections['offset'],
                        slope_x=corrections['slope'][0],
                        slope_y=corrections['slope'][1],
                        rotation_angle=corrections["rotation angle"] / np.pi,
                        stage_angle=corrections["stage diff angle"] / np.pi
                ))
        label.setText(text)
        
    def updateCorrection_motor(self, corrections):
        self._updateCorrection(corrections, self.correction_label_motor)
        
    def updateCorrection_piezzo(self, corrections):
        self._updateCorrection(corrections, self.correction_label_piezzo)
