import numpy as np
import pyqtgraph as pg

from lys.Qt import QtWidgets, QtCore
from .Widgets import AliveIndicator, SettingsButton
from lys_instr.gui.MultiDetector_SA1 import MultiDetectorGUI


class MultiSpectrometerGUI(MultiDetectorGUI):
    def __init__(self, obj, wait=False, interval=1, iter=1):
        super().__init__(obj, wait, interval, iter)

    def _initLayout(self):
        # Data display widget
        self._indexView = pg.ImageView()
        self._indexView.ui.menuBtn.hide()
        self._indexView.ui.roiBtn.hide()
        self._indexView.setMinimumSize(500, 400)
        # self._indexView.ui.histogram.hide()

        self._frameView = pg.PlotWidget()
        self._frameView.setMinimumSize(500, 400)

        # Acquisition control widgets
        if self._obj.exposure is not None:
            def setExposure(value):
                self._obj.exposure = value
            expTime = QtWidgets.QDoubleSpinBox()
            expTime.setValue(self._obj.exposure)
            expTime.setRange(0, np.infty)
            expTime.setDecimals(3)
            expTime.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            expTime.valueChanged.connect(setExposure)

            exposeLabel = QtWidgets.QLabel("Exp. (s)")
            exposeLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        # Buttons
        self._acquire = QtWidgets.QPushButton("Acquire", clicked=lambda: self._onAcquire("acquire"))
        self._stream = QtWidgets.QPushButton("Stream", clicked=lambda: self._onAcquire("stream"))
        self._stop = QtWidgets.QPushButton("Stop", clicked=self._obj.stop)
        self._stop.setEnabled(False)

        # Layout setup
        imageLayout = QtWidgets.QHBoxLayout()
        imageLayout.addWidget(self._indexView, stretch=1)
        imageLayout.addWidget(self._frameView, stretch=1)

        controlsLayout = QtWidgets.QHBoxLayout()
        controlsLayout.addWidget(AliveIndicator(self._obj))
        if self._obj.exposure is not None:
            controlsLayout.addWidget(exposeLabel)
            controlsLayout.addWidget(expTime)
        controlsLayout.addWidget(self._acquire)
        controlsLayout.addWidget(self._stream)
        controlsLayout.addWidget(self._stop)
        controlsLayout.addWidget(SettingsButton(clicked=self._showSettings))

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(imageLayout, stretch=1)
        mainLayout.addLayout(controlsLayout, stretch=0)
        
        self.setLayout(mainLayout)

    # def _update(self):
    #     if hasattr(self, "_data"):
    #         if len(self._obj.data) == len(self._obj.frameShape):
    #             frame = self._obj.data
    #         else:
    #             frame = self._obj._data[-1]
    #         self._frameView.plot(frame[0], frame[1], clear=True)

    def _dataAcquired(self, data):
        busy = self._obj.isBusy
        alive = self._obj.isAlive
        self._stream.setEnabled(not busy and alive)
        self._acquire.setEnabled(not busy and alive)
        self._stop.setEnabled(busy)

        # Display logic: update image array with new frames
        if data:
            for idx, frame in data.items():
                self._map[idx[-frame.ndim:]] = self._indexDisplay(frame)
            self._frameCount += 1

            # Update frame display every N frames or on last frame
            updateInterval = self._params["interval"]
            if self._frameCount % updateInterval == 0 or self._frameCount == len(data):
                self._frameView.plot(frame[0], frame[1], clear=True)
       
        self._indexView.setImage(self._map)

    def _showSettings(self):
        settingsWindow = _SettingsDialog(self, self._obj, self._params)
        settingsWindow.updated.connect(self._update)
        settingsWindow.exec_()

    def _indexDisplay(self, data):
        return np.mean(data) 
    
    # def _frameDisplay(self, frame):
    #     return frame


class _SettingsDialog(QtWidgets.QDialog):
    updated = QtCore.pyqtSignal()

    def __init__(self, parent, obj, params):
        super().__init__(parent)
        self.setWindowTitle("Detector Settings")

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(_GeneralPanel(params, updated=self.updated.emit), "General")
        tabs.addTab(obj.settingsWidget(), "Optional")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tabs)
        self.setLayout(layout)


class _GeneralPanel(QtWidgets.QWidget):
    updated = QtCore.pyqtSignal()
 
    def __init__(self, params, updated=None):
        super().__init__()
        self._params = params
        self.__initLayout(params["interval"])
        if updated is not None:
            self.updated.connect(updated)

    def __initLayout(self, interval):
        self._iter = QtWidgets.QSpinBox()
        self._iter.setRange(1, 2**31 - 1)
        self._iter.valueChanged.connect(self._changeInterval)

        # self._updateInterval = QtWidgets.QSpinBox()
        # self._updateInterval.setRange(1, 2**31 - 1)
        # self._updateInterval.valueChanged.connect(self._changeInterval)
        # if interval is None:
        #     self._updateInterval.setEnabled(False)
        # else:
        #     self._updateInterval.setValue(interval)

        # self._scheduledUpdateCheck = QtWidgets.QCheckBox("Update every", checked=interval is not None, toggled=self._changeInterval)
        # self._scheduledUpdateCheck.stateChanged.connect(self._updateInterval.setEnabled)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Repeat"), 0, 0)
        grid.addWidget(self._iter, 0, 1)
        grid.addWidget(QtWidgets.QLabel("times"), 0, 2)

        # grid.addWidget(self._scheduledUpdateCheck, 1, 0)
        # grid.addWidget(self._updateInterval, 1, 1)
        # grid.addWidget(QtWidgets.QLabel("frames"), 1, 2)
        # grid.addWidget(QtWidgets.QPushButton("Update", clicked=self.updated.emit), 1, 3)
        self.setLayout(grid)

    def _changeInterval(self):
        # if self._scheduledUpdateCheck.isChecked():
        #     self._params["interval"] = self._updateInterval.value()
        # else:
        #     self._params["interval"] = None         
        self._params["iter"] = self._iter.value()


# To Test the GUI run in the src\python: python -m lys_instr.gui.MultiDetector_SA2
if __name__ == "__main__":
    import sys
    from lys_instr.dummy.MultiDetector import MultiDetectorDummy
    from lys.Qt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    detector = MultiDetectorDummy(indexShape=(5, 5), frameShape=(2, 256), exposure=0.1)
    gui = MultiSpectrometerGUI(detector, wait=False, interval=1, iter=1)
    gui.show()
    sys.exit(app.exec_())