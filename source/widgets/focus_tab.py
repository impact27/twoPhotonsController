# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 16:51:32 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets
from focus_delegate import Focus_delegate

class Layout_wrapper(QtWidgets.QWidget):
    def __init__(self, layout, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        self.setLayout(layout)


class Focus_tab(QtWidgets.QWidget):

    deleterow = QtCore.pyqtSignal(int)
    displayrow = QtCore.pyqtSignal(int)

    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        
        self.fd = Focus_delegate(application_delegate)

        #======================================================================
        #       Create Widgets
        #======================================================================
        Range_label = QtWidgets.QLabel("Range:")
        Range_input = QtWidgets.QLineEdit('500')

        focus_button = QtWidgets.QPushButton("Focus")


        pos_list = QtWidgets.QTableWidget()
        pos_list.setColumnCount(2)
        pos_list.setHorizontalHeaderLabels(['Xm', 'Delete'])
        pos_list.setColumnWidth(0, 90)
        pos_list.setColumnWidth(1, 40)
        pos_list.horizontalHeader().setStretchLastSection(True)
        pos_list.verticalHeader().setDefaultSectionSize(48)

        clear_list_button = QtWidgets.QPushButton("Clear List")
        save_button = QtWidgets.QPushButton('Save')
        #======================================================================
        #     Layout
        #======================================================================

        Range_hbox = QtWidgets.QHBoxLayout()
        Range_hbox.addWidget(Range_label)
        Range_hbox.addWidget(Range_input)

        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addWidget(save_button)
        bottom_layout.addWidget(clear_list_button)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(Range_hbox)
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
            float(Range_input.text())))

        clear_list_button.clicked.connect(self.fd.clear)
        save_button.clicked.connect(self.fd.save)
        
        self.fd.updatelist.connect(self.updateList)

        #======================================================================
        #         Save variables
        #======================================================================
        self.pos_list = pos_list

    def cellClicked(self, row, column):
        if column == 1:
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

    def addRow(self, Xm):
        """Assume X are [x,y]"""
        row = self.pos_list.rowCount()
        self.pos_list.insertRow(row)

        Xmtext = "[{:.1f},\n {:.1f},\n {:.1f}]".format(*Xm)
        Xm_label = QtWidgets.QLabel(Xmtext)
        Xm_label.setAlignment(QtCore.Qt.AlignCenter)

        Delete = QtWidgets.QLabel('Delete')
        Delete.setStyleSheet("background-color: red")
        Delete.setAlignment(QtCore.Qt.AlignCenter)

        self.pos_list.setCellWidget(row, 0, Xm_label)
        self.pos_list.setCellWidget(row, 1, Delete)