# -*- coding: utf-8 -*-
"""
Created on Tue May  2 09:29:10 2017

@author: quentinpeter
"""
import sys
from PyQt5 import QtCore, QtWidgets, QtGui
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from application_delegate import application_delegate
#%%
    
class doubleSelector(QtWidgets.QWidget):
    
    newValue = QtCore.pyqtSignal(float)
    
    def __init__(self, valuesrange, initValue):
        super().__init__()
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(*valuesrange)
        slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                          QtWidgets.QSizePolicy.Preferred)
        slider.setValue(initValue)
        
        lineInput = QtWidgets.QLineEdit()
        
        def getValue():
            return float(lineInput.text())
        
        def myfixup(string):
            val=getValue()
            if val<valuesrange[0]:
                val=valuesrange[0]   
            elif val>valuesrange[1]:
                val=valuesrange[1]
            lineInput.setText(str(val))
            lineInput.editingFinished.emit()
        
        validator=QtGui.QDoubleValidator(*valuesrange,3)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        validator.fixup=myfixup
        lineInput.setValidator(validator)
        lineInput.setText(str(initValue))
        lineInput.setMaximumWidth(60)
        
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(slider)
        layout.addWidget(lineInput)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
    
        def updateLineInput(value):
            if value != int(getValue()):
                lineInput.setText(str(value))
                
        slider.valueChanged.connect(updateLineInput)            
        lineInput.editingFinished.connect(lambda: slider.setValue(getValue()))
        
        sendNewValue =lambda: self.newValue.emit(getValue())
        
        slider.sliderReleased.connect(sendNewValue)
        lineInput.editingFinished.connect(sendNewValue)

        self.slider=slider
        self.lineInput=lineInput
    
    def getValue(self):
        return float(self.lineInput.text())
    
    def setValue(self, value):
        self.lineInput.setText(str(value))
        self.slider.setValue(value)
        
        

#==============================================================================
# Plot canevas
#==============================================================================

class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        
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
        self.positions=[]
                
    def setimage(self,im):
        self.positions=[]
        self.im=im
        self.update_figure()
        
    
    def update_figure(self):
        self.figure.clear()
        self.axes = self.figure.add_subplot(111)
        mp=self.axes.imshow(self.im)
        self.axes.axis('image')
        self.figure.colorbar(mp)
        self.draw()
        
    def standalone(self):
        if hasattr(self, 'im'):
            plt.figure()
            plt.imshow(self.im)
            plt.colorbar()
            plt.show()
            
    def clear(self):
        self.figure.clear()
        self.axes = self.figure.add_subplot(111)
        self.draw()
        
    def plot(self,*args, **kwargs):
        self.axes.plot(*args, **kwargs)
        self.axes.axis('equal')
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
        Xinput.setValidator(QtGui.QDoubleValidator(0,100,3))
        Xinput.setText('0')
        
        Yinput=QtWidgets.QLineEdit()
        Yinput.setValidator(QtGui.QDoubleValidator(0,100,3))
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
        
        main_layout=QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(coord_label)
        main_layout.addLayout(coord)
        main_layout.addWidget(newpos_button)
        main_layout.addWidget(pos_list)
        main_layout.addLayout(hbuttons)
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

        #======================================================================
        #         Save variables
        #======================================================================
        
        self.xpos=Xinput
        self.ypos=Yinput
        self.pos_list=pos_list
        
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
    
class layout_wrapper(QtWidgets.QWidget):
    def __init__(self, layout, *args, **kwargs):       
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        self.setLayout(layout)
        
class tilt_tab(QtWidgets.QWidget):
    
    deleterow = QtCore.pyqtSignal(int)
    displayrow = QtCore.pyqtSignal(int)
    
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        
        #======================================================================
        #       Create Widgets
        #======================================================================
        
        Xinput = QtWidgets.QLineEdit('0')
        Xinput.setValidator(QtGui.QDoubleValidator(0,100,3))
        
        Yinput = QtWidgets.QLineEdit('0')
        Yinput.setValidator(QtGui.QDoubleValidator(0,100,3))
        
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
        
        main_layout=QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(tabs_widget)
        main_layout.addWidget(raise_button)
        main_layout.addWidget(pos_list)
        main_layout.addLayout(valLayout)
        self.setLayout(main_layout)
        
        #======================================================================
        #      Connections   
        #======================================================================
        
        pos_list.cellClicked.connect(self.cellClicked)
        pos_list.verticalHeader().sectionClicked.connect(self.rowClicked)
        
        newpos_button.clicked.connect( lambda:
                application_delegate.tilt_delegate.add_position(
                        float(Xinput.text()),
                        float(Yinput.text())))
        
        browse_button.clicked.connect(self.openfile)
            
        pos_file_button.clicked.connect( lambda:
                application_delegate.tilt_delegate.load_file(
                        path_field.text()))
            
        clear_list_button.clicked.connect(
                application_delegate.tilt_delegate.clear_positions)
        validate_button.clicked.connect(
                application_delegate.tilt_delegate.validate_positions)
        
        self.deleterow.connect(application_delegate.tilt_delegate.deleteIdx)
        self.displayrow.connect(application_delegate.tilt_delegate.display_row)
        application_delegate.tilt_delegate.updatelist.connect(self.updateList)
        raise_button.clicked.connect(application_delegate.manualFocus)
        
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
        
    
class write_tab(QtWidgets.QWidget):
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        #======================================================================
        #       Create Widgets
        #======================================================================
        
        Origin_label = QtWidgets.QLabel('Origin:')
        
        Xinput=QtWidgets.QLineEdit('0')
        Xinput.setValidator(QtGui.QDoubleValidator(0,100,3))
        
        Yinput=QtWidgets.QLineEdit('0')
        Yinput.setValidator(QtGui.QDoubleValidator(0,100,3))
        
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
        dx_input.setValidator(QtGui.QDoubleValidator(0,100,3))
        dy_input = QtWidgets.QLineEdit("0")
        dy_input.setValidator(QtGui.QDoubleValidator(0,100,3))
        
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
        
        #======================================================================
        #         Save variables
        #======================================================================

        self.path_field=path_field
        
    def browse_gfile(self):
        fn=QtWidgets.QFileDialog.getOpenFileName(
                    self,'Position File',QtCore.QDir.homePath(),
                    'GCode File (*.gcode)')
        self.path_field.setText(fn[0])
    
class secondary_widget(QtWidgets.QWidget):
    
    def __init__(self, application_delegate, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        
        md=application_delegate.mouvment_delegate
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
        
        XRange =md.get_XY_PosRange(0)
        YRange =md.get_XY_PosRange(1)
        
        Xlabel = QtWidgets.QLabel('X [μm]: ')
        Ylabel = QtWidgets.QLabel('Y [μm]: ')
        Xselector = doubleSelector(XRange, 0)
        Yselector = doubleSelector(YRange, 0)
        
        goto_button = QtWidgets.QPushButton("GO")
        
        vel_XY_range = md.get_XY_VelRange(0)
        vel_cub_range = md.get_cube_VelRange(0)
        
        vel_XY_label = QtWidgets.QLabel('Linear Stage Velocity [μm/s]:')
        vel_cub_label = QtWidgets.QLabel('Piezzo Stage Velocity [μm/s]:')
        vel_XY_selector = doubleSelector(vel_XY_range, md.get_XY_velocity())
        
        vel_cub_selector =doubleSelector(vel_cub_range, md.get_cube_velocity())
        clear_button = QtWidgets.QPushButton('Clear Graph')
        
        #======================================================================
        #     Layout    
        #======================================================================
        
        
        main_layout = QtWidgets.QGridLayout(self)
        main_layout.addWidget(vel_XY_label,0,0)
        main_layout.addWidget(vel_cub_label,1,0)
        main_layout.addWidget(vel_XY_selector,0,1)
        main_layout.addWidget(vel_cub_selector,1,1)
        main_layout.addWidget(live_button,2,0)
        main_layout.addWidget(draw_button,2,1)
        main_layout.addWidget(clear_button,3,0,1,2)
        main_layout.addWidget(Xlabel,0,2)
        main_layout.addWidget(Ylabel,1,2)
        main_layout.addWidget(Xselector,0,3)
        main_layout.addWidget(Yselector,1,3)
        main_layout.addWidget(goto_button,0,4,2,1)
        main_layout.addWidget(ESTOP_button,2,2,2,3)
        
        self.setLayout(main_layout)
        #======================================================================
        #      Connections   
        #======================================================================
        
        goto_button.clicked.connect(lambda:
            application_delegate.goto_XY_position(
                    Xselector.getValue(),
                    Yselector.getValue()))
        
        ESTOP_button.clicked.connect(application_delegate.ESTOP)
        
        vel_XY_selector.newValue.connect( 
            application_delegate.mouvment_delegate.set_XY_velocity)
        vel_cub_selector.newValue.connect(
            application_delegate.mouvment_delegate.set_cube_velocity)

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
        
        #======================================================================
        #     Layout    
        #======================================================================
        vertical = QtWidgets.QVBoxLayout()
        vertical.addWidget(imCanvas,1)
        vertical.addWidget(secondary_widget(self.application_delegate))
        
        horizontal = QtWidgets.QHBoxLayout(self.main_widget)
        horizontal.addWidget(tabs_widget)
        horizontal.addLayout(vertical)
        
        
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
        
qApp = QtWidgets.QApplication(sys.argv)
progname='Two Photons Controller'
aw = ApplicationWindow()
aw.setWindowTitle("%s" % progname)
aw.show()
sys.exit(qApp.exec_())