# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 13:30:56 2017

@author: quentinpeter
"""
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib
cmap = matplotlib.cm.get_cmap('plasma')
# ==============================================================================
# Plot canevas
# ==============================================================================


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

        self.toolbar = NavigationToolbar(self, parent, False)

        def notify_axes_change(fig):
            # This will be called whenever the current axes is changed
            if self.toolbar is not None:
                self.toolbar.update()
        self.figure.add_axobserver(notify_axes_change)

    def compute_initial_figure(self):
        pass
