# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 16:51:32 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets


class Layout_wrapper(QtWidgets.QWidget):
    def __init__(self, layout, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        self.setLayout(layout)


class Focus_tab(QtWidgets.QWidget):

    deleterow = QtCore.pyqtSignal(int)
    displayrow = QtCore.pyqtSignal(int)

    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.fd = application_delegate.focus_delegate

        #======================================================================
        #       Create Widgets
        #======================================================================
        back_label = QtWidgets.QLabel("Start: Pos +")
        back_input = QtWidgets.QLineEdit('20')

        forth_label = QtWidgets.QLabel("End: Pos +")
        forth_input = QtWidgets.QLineEdit('-20')

        step_label = QtWidgets.QLabel("Step:")
        step_input = QtWidgets.QLineEdit('-1')

        Nloops_label = QtWidgets.QLabel("Loops:")
        Nloops_input = QtWidgets.QLineEdit('1')

        precision_check = QtWidgets.QCheckBox("Piezzo")

        focus_button = QtWidgets.QPushButton("Focus")

        pos_list = QtWidgets.QTableWidget()
        pos_list.setColumnCount(3)
        pos_list.setHorizontalHeaderLabels(['X motor', 'X piezzo', 'Delete'])
        pos_list.setColumnWidth(0, 90)
        pos_list.setColumnWidth(1, 90)
        pos_list.setColumnWidth(2, 40)
        pos_list.horizontalHeader().setStretchLastSection(True)
        pos_list.verticalHeader().setDefaultSectionSize(48)

        clear_list_button = QtWidgets.QPushButton("Clear List")
        save_button = QtWidgets.QPushButton('Save')
        #======================================================================
        #     Layout
        #======================================================================

        focus_grid = QtWidgets.QGridLayout()
        focus_grid.addWidget(back_label, 0, 0)
        focus_grid.addWidget(back_input, 0, 1)
        focus_grid.addWidget(forth_label, 1, 0)
        focus_grid.addWidget(forth_input, 1, 1)
        focus_grid.addWidget(step_label, 2, 0)
        focus_grid.addWidget(step_input, 2, 1)
        focus_grid.addWidget(Nloops_label, 3, 0)
        focus_grid.addWidget(Nloops_input, 3, 1)
        focus_grid.addWidget(precision_check, 4, 0)

        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addWidget(save_button)
        bottom_layout.addWidget(clear_list_button)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(focus_grid)
        main_layout.addWidget(focus_button)
        main_layout.addWidget(pos_list)
        main_layout.addLayout(bottom_layout)
        self.setLayout(main_layout)

        #======================================================================
        #      Connections
        #======================================================================

        self.deleterow.connect(self.fd.delete_pos)
        self.displayrow.connect(self.fd.display_pos)

        pos_list.cellClicked.connect(self.cellClicked)
        pos_list.verticalHeader().sectionClicked.connect(self.rowClicked)

        focus_button.clicked.connect(lambda: self.fd.focus(
            float(back_input.text()),
            float(forth_input.text()),
            float(step_input.text()),
            intensity=None,
            Nloops=int(float(Nloops_input.text())),
            piezzo=precision_check.isChecked()))

        clear_list_button.clicked.connect(self.fd.clear)
        save_button.clicked.connect(self.fd.save)

        self.fd.updatelist.connect(self.updateList)

        #======================================================================
        #         Save variables
        #======================================================================
        self.pos_list = pos_list

    def cellClicked(self, row, column):
        if column == 2:
            self.deleterow.emit(row)
        else:
            self.displayrow.emit(row)

    def rowClicked(self, row):
        self.displayrow.emit(row)

    def updateList(self, poslist):
        self.pos_list.clearContents()
        self.pos_list.setRowCount(0)
        for d in poslist:
            self.addRow(d)

    def addRow(self, Xms):
        row = self.pos_list.rowCount()
        self.pos_list.insertRow(row)

        Xmtext = "[{:.1f},\n {:.1f},\n {:.3f}]".format(*Xms[0])
        Xm_motor_label = QtWidgets.QLabel(Xmtext)
        Xm_motor_label.setAlignment(QtCore.Qt.AlignCenter)

        Xmtext = "[{:.1f},\n {:.1f},\n {:.3f}]".format(*Xms[1])
        Xm_piezzo_label = QtWidgets.QLabel(Xmtext)
        Xm_piezzo_label.setAlignment(QtCore.Qt.AlignCenter)

        Delete = QtWidgets.QLabel('X')
        Delete.setStyleSheet("background-color: red")
        Delete.setAlignment(QtCore.Qt.AlignCenter)

        self.pos_list.setCellWidget(row, 0, Xm_motor_label)
        self.pos_list.setCellWidget(row, 1, Xm_piezzo_label)
        self.pos_list.setCellWidget(row, 2, Delete)
