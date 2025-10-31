import numpy as np

from lys import multicut, Wave
from lys.Qt import QtWidgets, QtCore

from .widgets import AliveIndicator, SettingsButton


class MultiDetectorGUI(QtWidgets.QWidget):
    """
    GUI widget providing acquisition controls and a ``multicut`` display for a multi-dimensional detector.

    Accepts a ``MultiDetectorInterface`` instance supplying data and signals.
    Listens to the detector's ``busyStateChanged``, ``aliveStateChanged``, and ``dataAcquired`` signals to update the GUI.
    """

    def __init__(self, obj, wait=False, interval=1, iter=1):
        """
        Initialize the detector GUI.

        Args:
            obj (MultiDetectorInterface): Detector instance supplying data and signals.
            wait (bool): If True, block until acquisition completes when using one-shot acquire.
            interval (int | None): Number of frames between display updates, or ``None`` to disable periodic updates.
            iter (int): Number of acquisition iterations to run in acquire mode.
        """
        super().__init__()
        self._obj = obj
        self._params = {"wait": wait, "interval": interval, "iter": iter}
        self._frameCount = None

        # Signals from the detector
        self._obj.busyStateChanged.connect(self._setButtonState)
        self._obj.aliveStateChanged.connect(self._setButtonState)
        self._obj.dataAcquired.connect(self._dataAcquired)
        self._obj.busyStateChanged.connect(self._onAcqFinished)

        self._initLayout()

    def _initLayout(self):
        """
        Create and arrange the widgets for acquisition control and data display.
        """
        # Data display widget
        self._mcut = multicut(Wave(np.random.rand(*self._obj.dataShape), *self._obj.axes), returnInstance=True, subWindow=False)
        self._mcut.widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self._mcut.loadDefaultTemplate()
        self._mcut.cui.dimensionChanged.connect(lambda: self._mcut.loadDefaultTemplate())

        # Acquisition control widgets
        if self._obj.exposure is not None:
            def setExposure(value):
                self._obj.exposure = value
            expTime = QtWidgets.QDoubleSpinBox()
            expTime.setValue(self._obj.exposure)
            expTime.setRange(0, np.infty)
            expTime.setDecimals(5)
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
        controlsLayout.addWidget(SettingsButton(clicked=self._showSettings))

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(imageLayout, stretch=1)
        mainLayout.addLayout(controlsLayout, stretch=0)

        self.setLayout(mainLayout)

    def _update(self):
        """
        Update the ``multicut`` display during acquisition.

        Called periodically or on frame batches.
        """
        if self._frameCount is not None:
            self._mcut.cui.updateRawWave(axes=self._obj.axes)

    def _dataAcquired(self, data):
        """
        Handle incoming acquired data frame.

        Args:
            data (dict[tuple, numpy.ndarray] | None): Mapping of index tuples to acquired frames; ``None`` or empty mappings are ignored.
        """
        if data:
            if self._frameCount is None:
                self._frameCount = 0
                d = Wave(np.zeros(self._obj.dataShape), *self._obj.axes)
                self._mcut.cui.setRawWave(d)

            self._mcut.cui.updateRawWave(data, update=False)
            self._frameCount += 1

            # Update frame display every N frames or on last frame
            if self._frameCount == np.prod(self._obj.indexShape):
                update = True
            else:
                update = False if self._params["interval"] is None else self._frameCount % self._params["interval"] == 0

            if update:
                self._update()

    def _onAcqFinished(self, b):
        """
        Reset internal acquisition state when acquisition finishes.

        Args:
            b (bool): Busy flag emitted by the controller; when False the acquisition has finished and the frame counter is cleared.
        """
        if b is False:
            self._frameCount = None

    def _onAcquire(self, mode="acquire"):
        """
        Start acquisition in the given mode.

        Args:
            mode (str): "acquire" for a finite run or "stream" for continuous streaming (iter = -1).
        """
        if mode == "acquire":
            self._obj.startAcq(wait=self._params["wait"], iter=self._params["iter"])
        else:
            self._obj.startAcq(iter=-1)

    def _setButtonState(self):
        """
        Enable or disable acquisition control buttons according to detector state.
        """
        if not self._obj.isAlive:
            self._acquire.setEnabled(False)
            self._stream.setEnabled(False)
            self._stop.setEnabled(False)
        elif self._obj.isBusy:
            self._acquire.setEnabled(False)
            self._stream.setEnabled(False)
            self._stop.setEnabled(True)
        else:
            self._acquire.setEnabled(True)
            self._stream.setEnabled(True)
            self._stop.setEnabled(False)

    def _showSettings(self):
        """
        Show the settings dialog.

        Connect the dialog's ``updated`` signal (emitted when the user applies changes) to refresh the display.
        """
        settingsWindow = _SettingsDialog(self, self._obj, self._params)
        settingsWindow.updated.connect(self._update)
        settingsWindow.exec_()


class _SettingsDialog(QtWidgets.QDialog):

    #: Signal emitted when acquisition parameters are updated.
    updated = QtCore.pyqtSignal()

    def __init__(self, parent, obj, params):
        """
        Create the detector settings dialog with general and optional tabs.

        Args:
            parent (QWidget): Parent widget (the main ``MultiDetectorGUI`` instance).
            obj (MultiDetectorInterface): Detector used to populate optional tabs.
            params (dict): Acquisition parameters that the general panel edits (``interval``, ``iter``, etc.).
        """
        super().__init__(parent)
        self.setWindowTitle("Detector Settings")

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(_GeneralPanel(params, updated=self.updated.emit), "General")
        tabs.addTab(obj.settingsWidget(), "Optional")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tabs)
        self.setLayout(layout)


class _GeneralPanel(QtWidgets.QWidget):

    #: Signal emitted when acquisition parameters are updated.
    updated = QtCore.pyqtSignal()

    def __init__(self, params, updated=None):
        """
        Initialize the general settings panel.

        Args:
            params (dict): Acquisition parameters.
            updated (callable | None): Optional callback to connect to this panel's ``updated`` signal.
        """
        super().__init__()
        self._params = params
        self.__initLayout(params["interval"])
        if updated is not None:
            self.updated.connect(updated)

    def __initLayout(self, interval):
        """
        Create GUI components of the dialog and connect signals to respective slots.
        """
        self._iter = QtWidgets.QSpinBox()
        self._iter.setRange(1, 2**31 - 1)

        self._updateInterval = QtWidgets.QSpinBox()
        self._updateInterval.setRange(1, 2**31 - 1)
        if interval is None:
            self._updateInterval.setEnabled(False)
        else:
            self._updateInterval.setValue(interval)

        self._scheduledUpdateCheck = QtWidgets.QCheckBox("Update every", checked=interval is not None, toggled=self._changeInterval)

        self._iter.valueChanged.connect(self._changeInterval)
        self._updateInterval.valueChanged.connect(self._changeInterval)
        self._scheduledUpdateCheck.stateChanged.connect(self._updateInterval.setEnabled)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Repeat"), 0, 0)
        grid.addWidget(self._iter, 0, 1)
        grid.addWidget(QtWidgets.QLabel("times"), 0, 2)

        grid.addWidget(self._scheduledUpdateCheck, 1, 0)
        grid.addWidget(self._updateInterval, 1, 1)
        grid.addWidget(QtWidgets.QLabel("frames"), 1, 2)
        grid.addWidget(QtWidgets.QPushButton("Update", clicked=self.updated.emit), 1, 3)
        self.setLayout(grid)

    def _changeInterval(self):
        """
        Synchronize scheduled-update GUI to acquisition parameters.
        """
        if self._scheduledUpdateCheck.isChecked():
            self._params["interval"] = self._updateInterval.value()
        else:
            self._params["interval"] = None
        self._params["iter"] = self._iter.value()
