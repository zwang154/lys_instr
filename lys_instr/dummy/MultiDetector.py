import time

from lys_instr.MultiDetector import MultiDetectorInterface
from lys.Qt import QtWidgets, QtCore

from .detectorData import RandomData, RamanData


class MultiDetectorDummy(MultiDetectorInterface):
    """
    Dummy implementation of ``MultiDetectorInterface``.

    This class simulates a detector controller for indexed/arrayed data acquisition and error injection for testing purposes.
    """

    def __init__(self, data=None, indexShape=(), frameShape=(100, 100), exposure=None, **kwargs):
        """
        Initializes the dummy multi-detector with the given parameters.

        Args:
            data (DummyDataInterface): The data to be used as dummy. If not specified, random data will be used based on indexShape and frameShape.
            indexShape (tuple of int): Shape of the index grid for random data. This argument will be ignored when data is not None.
            frameShape (tuple of int): Shape of each data frame for random data. This argument will be ignored when data is not None.
            exposure (float, optional): Time per frame in seconds.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(**kwargs)
        self.setData(data, indexShape, frameShape)
        self.exposure = exposure
        self.error = False
        self.start()

    def _run(self, iter=1):
        """
        Runs the acquisition thread associated with the ``MultiDetectorInterface``, simulating indexed/arrayed data frame acquisition.

        This method generates random data frames at the specified frame time, updates the acquired indices, and emits an update signal after each frame is acquired.
        """
        self._shouldStop = False
        
        i = 0
        while i != iter:
            for idx, data in self._obj:
                if self._shouldStop:
                    return
                time.sleep(self.exposure * self._obj.nframes)
                self._data[idx] = data
                self.updated.emit()
            i += 1

    def _stop(self):
        """
        Stops the acquisition thread.
        """
        self._shouldStop = True

    def _get(self):
        """
        Retrieves and clears the acquired data.

        Returns:
            dict: A copy of the acquired data, indexed by frame indices.
        """
        data = self._data.copy()
        self._data.clear()
        return data

    def _isAlive(self):
        """
        Gets the alive state of the simulated detector.

        Returns:
            bool: True if the detector is alive, False if it is dead.
        """
        return not self.error

    @property
    def frameShape(self):
        """
        Shape of each data frame acquired by the detector.

        Returns:
            tuple of int: The shape of each data frame.
        """
        return self._obj.frameShape

    @property
    def indexShape(self):
        """
        Shape of the index grid for data acquisition.

        Returns:
            tuple of int: The shape of the index grid.
        """
        return self._obj.indexShape

    @property
    def axes(self):
        """
        Coordinate axes for each dimension of the data.

        Returns:
            list[numpy.ndarray]: Coordinate axes for each dimension of the data.
        """
        return self._obj.axes

    def settingsWidget(self):
        """
        Returns a QWidget for optional settings.

        Returns:
            QtWidgets.QWidget: The optional settings panel.
        """
        return _OptionalPanel(self)

    def setData(self, data=None, indexShape=None, frameShape=None):
        if data is None:
            self._obj = RandomData(indexShape, frameShape)
        else:
            self._obj = data
        self._data = {}


class _OptionalPanel(QtWidgets.QWidget):
    """
    Optional settings panel for ``MultiDetectorDummy``.

    Provides a button to toggle the simulated detector's alive state.
    """

    def __init__(self, obj):
        """
        Initializes the optional settings panel with a reference to the backend object.

        Args:
            obj: The backend detector object.
        """
        super().__init__()
        self.setWindowTitle("Settings")
        self._obj = obj
        self._initLayout()

    def _initLayout(self):
        """
        Initializes and arranges the widgets in the optional settings panel.
        """
        self._switch = QtWidgets.QPushButton("Change", clicked=self._toggleAlive)
        aliveLayout = QtWidgets.QHBoxLayout()
        aliveLayout.addWidget(QtWidgets.QLabel("Alive State:"), alignment=QtCore.Qt.AlignCenter)
        aliveLayout.addWidget(self._switch, alignment=QtCore.Qt.AlignCenter)

        dummyOptionsLayout = QtWidgets.QHBoxLayout()
        dummyOptions = {"Raman": RamanData(scanLevel=0), "Random": RandomData((), (600,))}
        dummySelector = _DummySelector(self._obj, dummyOptions)
        dummySelector.setCurrentByValue(self._obj._obj)
        # dummySelector.changed.connect(self._obj.refreshGUI.emit)
        dummyOptionsLayout.addWidget(QtWidgets.QLabel("Dummy Data:"), alignment=QtCore.Qt.AlignCenter)
        dummyOptionsLayout.addWidget(dummySelector, alignment=QtCore.Qt.AlignCenter)

        panelLayout = QtWidgets.QVBoxLayout()
        panelLayout.addLayout(aliveLayout)
        panelLayout.addLayout(dummyOptionsLayout)

        self.setLayout(panelLayout)

    def _toggleAlive(self):
        """
        Toggles the alive state of the backend detector and emits relevant signals.
        """
        backend = self._obj
        backend.error = not backend.error
        data = backend._get()
        if data:
            backend.dataAcquired.emit(data)
        backend.aliveStateChanged.emit(backend.isAlive)


class _DummySelector(QtWidgets.QComboBox):

    changed = QtCore.pyqtSignal(str)

    def __init__(self, detector, dummyData):
        super().__init__()
        self._detector = detector
        self._dummyData = dummyData
        self._initLayout()
        self.setObjectName("Dummy_options")

    def _initLayout(self):
        self.addItems(self._dummyData.keys())
        self.currentTextChanged.connect(self._changed)

    def _changed(self, text):
        selected = self._dummyData[text]
        self._detector.setData(data=selected)
        self.changed.emit(text)

    def setCurrentByValue(self, value):
        for key, val in self._dummyData.items():
            if type(val) == type(value):
                self.setCurrentText(key)
                break