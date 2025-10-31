import time

from lys_instr.MultiDetector import MultiDetectorInterface
from lys.Qt import QtWidgets, QtCore

from .detectorData import RandomData, DummyDataSelector


class MultiDetectorDummy(MultiDetectorInterface):
    """
    Dummy implementation of ``MultiDetectorInterface``.

    This class simulates a detector that Produces indexed frames from a supplied data source or by generating random frames.
    Acquisition runs in a background loop (started by ``start()`` in ``__init__``) and populates an internal buffer.
    Signals ``updated``, ``dataAcquired``, and ``aliveStateChanged``, defined in ``MultiDetectorInterface``, are emitted as appropriate.
    """

    def __init__(self, data=None, indexShape=(), frameShape=(100, 100), exposure=0.1, **kwargs):
        """
        Initialize the dummy detector and start acquisition.

        Call ``start()`` to begin the acquisition thread.

        Args:
            data (Optional[DummyDataInterface]): Data source; if ``None``, random frames are generated.
            indexShape (Tuple[int, ...]): Shape of the index grid for generated data. Ignored if ``data`` is not None.
            frameShape (Tuple[int, ...]): Shape of each data frame for generated data. Ignored if ``data`` is not None.
            exposure (float): Time in seconds to wait per frame (frame exposure).
            **kwargs: Additional keyword arguments forwarded to the parent initializer.
        """
        super().__init__(**kwargs)
        self.setData(data, indexShape, frameShape)
        self.exposure = exposure
        self.error = False
        self.start()

    def _run(self, iter=1):
        """
        Run the background acquisition loop that simulates frame acquisition.

        For each iteration, walk the data source (``self._obj``) to acquire frames, sleep per frame according to exposure time (``self.exposure``),
        store acquired frames into the internal buffer (``self._data``), and emit the notification signal (``updated``) after each frame.
        Return early if the stop request flag (``self._shouldStop``) is set.
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
        Request the acquisition loop to stop.

        Set an internal stop request flag so the background thread will exit at the next check.
        """
        self._shouldStop = True

    def _get(self):
        """
        Retrieve and clear the accumulated data buffer.

        Returns:
            dict: Shallow copy of acquired frames keyed by index tuples.
        """
        data = self._data.copy()
        self._data.clear()
        return data

    def _isAlive(self):
        """
        Return the alive state of the simulated detector.

        Returns:
            bool: True if the detector is alive, False otherwise.
        """
        return not self.error

    @property
    def frameShape(self):
        """
        Shape of a single acquired data frame.

        Returns:
            tuple[int, ...]: Frame dimensions (height, width, ...) as provided by the data source.
        """
        return self._obj.frameShape

    @property
    def indexShape(self):
        """
        Shape of the index grid.

        Returns:
            tuple[int, ...]: Dimensions of the index grid used to iterate over frames.
        """
        return self._obj.indexShape

    @property
    def axes(self):
        """
        Axis coordinates for the full data.

        Returns:
            List[numpy.ndarray]: Coordinate arrays corresponding to each axis of the index grid.
        """
        return self._obj.axes

    def settingsWidget(self):
        """
        Create and return an optional settings QWidget.

        Returns:
            QtWidgets.QWidget: The settings panel widget.
        """
        return _OptionalPanel(self)

    def setData(self, data=None, indexShape=None, frameShape=None):
        """
        Configure the dummy data source.

        Args:
            data (Optional[DummyDataInterface]): Data source. If ``None``, a random-data generator (``RandomData``) is created.
            indexShape (Optional[Tuple[int, ...]]): Index-grid shape used by the random-data generator.
            frameShape (Optional[Tuple[int, ...]]): Frame shape used by the random-data generator.
        """
        if data is None:
            self._obj = RandomData(indexShape, frameShape)
        else:
            self._obj = data
        self._data = {}


class _OptionalPanel(QtWidgets.QWidget):
    """
    Optional settings panel.

    Provides GUI to toggle the simulated detector's alive state and to choose dummy data sources.
    """

    def __init__(self, obj):
        """
        Initialize the settings panel.

        Args:
            obj (MultiDetectorInterface): Backend detector object using the panel.
        """
        super().__init__()
        self.setWindowTitle("Settings")
        self._obj = obj
        self._initLayout()

    def _initLayout(self):
        """
        Build and arrange the panel's widgets.
        """
        self._switch = QtWidgets.QPushButton("Change", clicked=self._toggleAlive)
        aliveLayout = QtWidgets.QHBoxLayout()
        aliveLayout.addWidget(QtWidgets.QLabel("Alive State:"), alignment=QtCore.Qt.AlignCenter)
        aliveLayout.addWidget(self._switch, alignment=QtCore.Qt.AlignCenter)

        dummyOptionsLayout = QtWidgets.QHBoxLayout()
        dummySelector = DummyDataSelector(self._obj)
        dummySelector.changed.connect(lambda data: self._obj.setData(data))
        dummyOptionsLayout.addWidget(QtWidgets.QLabel("Dummy Data:"), alignment=QtCore.Qt.AlignCenter)
        dummyOptionsLayout.addWidget(dummySelector, alignment=QtCore.Qt.AlignCenter)

        panelLayout = QtWidgets.QVBoxLayout()
        panelLayout.addLayout(aliveLayout)
        panelLayout.addLayout(dummyOptionsLayout)

        self.setLayout(panelLayout)

    def _toggleAlive(self):
        """
        Toggle the backend detector's alive state and emit notification signals.
        """
        backend = self._obj
        backend.error = not backend.error
        data = backend._get()
        if data:
            backend.dataAcquired.emit(data)
        backend.aliveStateChanged.emit(backend.isAlive)


