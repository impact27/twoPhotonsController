# -*- coding: utf-8 -*-
"""
Created on Wed May 17 10:34:47 2017

@author: quentinpeter
"""
from PyQt5 import QtCore, QtWidgets, QtGui
import numpy as np

class LightWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.on = False

    def isOn(self):
        return self.on

    def setOn(self, on):
        self.on = on
        self.update()

    def paintEvent(self, paintEvent):
        if self.on:
            color = QtCore.Qt.green
        else:
            color = QtCore.Qt.yellow

        size = self.height()

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(color)
        painter.drawEllipse(size / 4, size / 4, size / 2, size / 2)


class doubleSelector(QtWidgets.QWidget):

    newValue = QtCore.pyqtSignal(float)

    def __init__(self, valuesrange, initValue, isLog=False):
        self.isLog = isLog
        self.factor = 1
        valuesrange = np.asarray(valuesrange)
        amin, amax = valuesrange

        if self.isLog:
            amin, amax = np.log((amin, amax))
        if amax - amin < 100:
            self.factor = 100 / (amax - amin)

        super().__init__()
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider = slider
        slider.setRange(*(self.factor * np.array((amin, amax))))
        slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                             QtWidgets.QSizePolicy.Preferred)

        self.setSliderValue(initValue)

        lineInput = QtWidgets.QLineEdit()
        self.lineInput = lineInput

        def getValue():
            try:
                return float(lineInput.text())
            except ValueError:
                return np.nan

        def myfixup(string):
            val = getValue()
            if np.isnan(val):
                lineInput.setText('')
                return
            if val < valuesrange[0]:
                val = valuesrange[0]
            elif val > valuesrange[1]:
                val = valuesrange[1]
            self.setInputValue(val)
            lineInput.editingFinished.emit()

        validator = QtGui.QDoubleValidator(*valuesrange, 3)
        validator.setNotation(QtGui.QDoubleValidator.StandardNotation)
        validator.fixup = myfixup
        lineInput.setValidator(validator)
        self.setInputValue(initValue)
        lineInput.setMaximumWidth(80)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(slider)
        layout.addWidget(lineInput)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        def updateLineInput(value):
            if value == int(getValue() * self.factor):
                return
            value = value / self.factor
            if self.isLog:
                value = np.exp(value)
            self.setInputValue(value)

        slider.valueChanged.connect(updateLineInput)
        lineInput.editingFinished.connect(lambda:
                                          self.setSliderValue(getValue()))

        def sendNewValue(): return self.newValue.emit(getValue())

        slider.sliderReleased.connect(sendNewValue)
        lineInput.editingFinished.connect(sendNewValue)

        self.validator = validator

    def getValue(self):
        return float(self.lineInput.text())

    def setValue(self, value):
        self.setSliderValue(value)
        self.setInputValue(value)

    def setSliderValue(self, val):
        if self.isLog:
            val = np.log(val)
        self.slider.setValue(self.factor * val)

    def setInputValue(self, val):
        if np.abs(val) < .1 and val != 0:
            self.lineInput.setText('{:.3e}'.format(val))
        else:
            self.lineInput.setText('{:g}'.format(val))

    def setRange(self, minimum, maximum, decimals):
        self.validator.setRange(minimum, maximum, decimals)
        self.lineInput.setValidator(self.validator)
        self.slider.setRange(*(self.factor * np.array((minimum, maximum))))
