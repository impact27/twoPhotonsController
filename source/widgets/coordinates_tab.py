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
        correction_reset_piezo = QtWidgets.QPushButton('Reset')
        correction_save = QtWidgets.QPushButton('Save')
        correction_load = QtWidgets.QPushButton('Load')

        piezo_label = QtWidgets.QLabel("Piezo")
        piezo_label.setStyleSheet("font: bold large")

        piezo_plane_button = QtWidgets.QPushButton('Piezo Plane')
        motor_plane_button = QtWidgets.QPushButton('Motor Plane')

        correction_label_piezo = QtWidgets.QLabel('')
        self.correction_label_piezo = correction_label_piezo

        #======================================================================
        #     Layout
        #======================================================================

        coord = QtWidgets.QHBoxLayout()
        coord.addWidget(QtWidgets.QLabel("x, y, z:"))
        coord.addWidget(Xinput)

        tab1Layout = QtWidgets.QVBoxLayout()
        tab1Layout.addLayout(coord)
        tab1Layout.addWidget(newpos_button)

        tab2Layout = QtWidgets.QVBoxLayout()
        tab2Layout.addWidget(pos_file_button)

        tabs_widget = QtWidgets.QTabWidget()
        tabs_widget.addTab(Layout_wrapper(tab1Layout), 'Manual')
        tabs_widget.addTab(Layout_wrapper(tab2Layout), 'File')

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
        main_layout.addWidget(motor_plane_button)

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

        main_layout.addWidget(piezo_label)
        main_layout.addWidget(piezo_plane_button)
        main_layout.addWidget(correction_label_piezo)
        main_layout.addWidget(correction_reset_piezo)

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
        md = application_delegate.movement_delegate
        self.md = md

        self.updateCorrection_motor(md.motor.corrections)
        self.updateCorrection_piezo(md.piezo.corrections)

        motor_plane_button.clicked.connect(cd.motor_plane)
        piezo_plane_button.clicked.connect(cd.piezo_plane)
        pos_list.cellClicked.connect(self.cellClicked)
        pos_list.verticalHeader().sectionClicked.connect(self.rowClicked)

        def newpos():
            cd.add_position(np.fromstring(Xinput.text(), sep=','))
            
        newpos_button.clicked.connect(newpos)
        Xinput.editingFinished.connect(newpos)
        

        pos_file_button.clicked.connect(self.open_position_file)

        clear_list_button.clicked.connect(cd.clear_positions)
        validate_button.clicked.connect(cd.processPos)

        self.deleterow.connect(cd.del_position)
        self.displayrow.connect(cd.displayrow)
        cd.updatelist.connect(self.updateList)

        md.motor.coordinatesCorrected.connect(self.updateCorrection_motor)
        md.piezo.coordinatesCorrected.connect(self.updateCorrection_piezo)

        correction_reset_motor.clicked.connect(md.motor.reset_corrections)
        correction_reset_piezo.clicked.connect(md.piezo.reset_corrections)

        correction_save.clicked.connect(self.save_correction_file)
        correction_load.clicked.connect(self.open_correction_file)

        save_errors.clicked.connect(cd.save_errors)

        offset_button.clicked.connect(lambda: md.motor.offset_origin(
                            np.fromstring(offset_input.text(), sep=',')))
            

        #======================================================================
        #         Save variables
        #======================================================================

        self.xinput = Xinput
        self.pos_list = pos_list
        self.cd = cd

    def open_correction_file(self):
        fn = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Position File', QtCore.QDir.homePath() +'/correction.txt',
            'Text File (*.txt)')[0]
        if len(fn) > 0:
            self.md.load_corrections(fn)
        
    def save_correction_file(self):
        fn = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Position File', QtCore.QDir.homePath() +'/correction.txt' ,
            'Text File (*.txt)')[0]
        if len(fn) > 0:
            self.md.save_corrections(fn)
        
    def open_position_file(self):
        fn = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Position File', QtCore.QDir.homePath())[0]
        if len(fn) > 0:
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
                "Angles: {angles}".format(
                    offset=np.array_str(corrections['offset'],
                                        precision=2,
                                        max_line_width=40,
                                        suppress_small=True),
                    angles=np.array_str(corrections["rotation angles"],
                                        precision=4,
                                        max_line_width=40,
                                        suppress_small=True)
                ))

        label.setText(text)

    def updateCorrection_motor(self, corrections):
        self._updateCorrection(corrections, self.correction_label_motor)

    def updateCorrection_piezo(self, corrections):
        self._updateCorrection(corrections, self.correction_label_piezo)
