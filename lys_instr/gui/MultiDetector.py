import numpy as np

from lys import multicut
from lys.Qt import QtWidgets, QtCore

from .widgets import AliveIndicator, SettingButton


class MultiDetectorGUI(QtWidgets.QWidget):
    """
    GUI for MultiDetectorInterface.
    Only for implementation in lys.
    """

    def __init__(self, obj, wait=False, interval=1):
        super().__init__()
        self._obj = obj
        self._params = {"wait": wait, "interval": interval}

        self._obj.busyStateChanged.connect(self._setButtonState)
        self._obj.aliveStateChanged.connect(self._setButtonState)
        self._obj.dataAcquired.connect(self._dataAcquired)

        self._initLayout()

    def _initLayout(self):
        # Data display widget
        self._mcut = multicut(np.random.rand(*self._obj._frameDim), returnInstance=True, subWindow=False)
        self._mcut.widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

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
        imageLayout.addWidget(self._mcut.widget)

        controlsLayout = QtWidgets.QHBoxLayout()
        controlsLayout.addWidget(AliveIndicator(self._obj))
        if self._obj.exposure is not None:
            controlsLayout.addWidget(exposeLabel)
            controlsLayout.addWidget(expTime)
        controlsLayout.addWidget(self._acquire)
        controlsLayout.addWidget(self._stream)
        controlsLayout.addWidget(self._stop)
        controlsLayout.addWidget(SettingButton(clicked=self._showSettings))

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(imageLayout, stretch=1)
        mainLayout.addLayout(controlsLayout, stretch=0)
        
        self.setLayout(mainLayout)

    def _update(self):
        self._mcut.cui.setRawWave(self._data)

    def _dataAcquired(self, data):
        if data:
            for idx, frame in data.items():
                self._data[idx[-frame.ndim:]] = frame
            self._frameCount += 1

            # Update frame display every N frames or on last frame
            if self._frameCount == np.prod(self._obj.indexDim):
                update = True
            else:
                update = False if self._params["interval"] is None else self._frameCount % self._params["interval"] == 0

            if update:
                self._update()

    def _onAcquire(self, mode="acquire"):
        self._frameCount = 0
        self._data = np.zeros(self._obj.dataShape)
        self._mcut.cui.setRawWave(self._data)
        if mode == "acquire":
            self._obj.startAcq(wait=self._params["wait"])
        else:
            self._obj.startAcq(streaming=True)

    def _setButtonState(self):
        alive = self._obj.isAlive
        if not alive:
            self._acquire.setEnabled(False)
            self._stream.setEnabled(False)
            self._stop.setEnabled(False)
        elif self._obj.isBusy:
            self._acquire.setEnabled(False)
            self._stream.setEnabled(False)
            self._stop.setEnabled(True)
            self._acquire.setText("Acquire")
            self._stream.setText("Stream")
        else:
            self._acquire.setEnabled(True)
            self._stream.setEnabled(True)
            self._stop.setEnabled(False)
            self._acquire.setText("Acquire")
            self._stream.setText("Stream")

    def _showSettings(self):
        settingsWindow = _SettingDialog(self, self._obj, self._params)
        settingsWindow.updated.connect(self._update)
        settingsWindow.exec_()


class _SettingDialog(QtWidgets.QDialog):
    updated = QtCore.pyqtSignal()

    def __init__(self, parent, obj, params):
        super().__init__(parent)
        self.setWindowTitle("Detector Settings")

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(_GeneralPanel(params, updated=self.updated.emit), "General")
        tabWidget.addTab(obj.settingWidget(), "Options")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tabWidget)
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
        self._scheduledUpdateCheck = QtWidgets.QCheckBox("Update every", checked=interval is not None, toggled=self._changeInterval)
        self._updateInterval = QtWidgets.QSpinBox()
        self._updateInterval.setRange(1, 2**31 - 1)
        self._updateInterval.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._updateInterval.valueChanged.connect(self._changeInterval)
        if interval is None:
            self._updateInterval.setEnabled(False)
        else:
            self._updateInterval.setValue(interval)

        def setWait(value):
            self._params["wait"] = value
        updateBtn = QtWidgets.QPushButton("Update", clicked=self.updated.emit)
        waitCheck = QtWidgets.QCheckBox("Wait for acquisition to finish", checked=self._params["wait"], toggled=setWait)

        self._scheduledUpdateCheck.stateChanged.connect(self._updateInterval.setEnabled)

        updateLayout = QtWidgets.QHBoxLayout()
        updateLayout.addWidget(self._scheduledUpdateCheck)
        updateLayout.addWidget(self._updateInterval)
        updateLayout.addWidget(QtWidgets.QLabel("frames"))
        updateLayout.addWidget(updateBtn)

        waitLayout = QtWidgets.QHBoxLayout()
        waitLayout.addWidget(waitCheck)

        optionsLayout = QtWidgets.QVBoxLayout(self)
        optionsLayout.addLayout(updateLayout)
        optionsLayout.addLayout(waitLayout)

    def _changeInterval(self):
        if self._scheduledUpdateCheck.isChecked():
            self._params["interval"] = self._updateInterval.value()
        else:
            self._params["interval"] = None         
