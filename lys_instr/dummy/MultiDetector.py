import numpy as np
import time
import itertools

from lys_instr.MultiDetector import MultiDetectorInterface
from lys.Qt import QtWidgets, QtCore


class MultiDetectorDummy(MultiDetectorInterface):
    """
    Dummy implementation of ``MultiDetectorInterface``.

    This class simulates a detector controller for indexed/arrayed data acquisition and error injection for testing purposes.
    """

    def __init__(self, indexShape, frameShape, exposure=None, **kwargs):
        """
        Initializes the dummy multi-detector with the given parameters.

        Args:
            indexShape (tuple of int): Shape of the index grid.
            frameShape (tuple of int): Shape of each data frame.
            exposure (float, optional): Time per frame in seconds.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(**kwargs)
        self._data = {}
        self._frameShape = frameShape
        self._indexShape = indexShape
        self.exposure = exposure
        self._error = False
        self.start()

    def _run(self, iter=1):
        """
        Runs the acquisition thread associated with the ``MultiDetectorInterface``, simulating indexed/arrayed data frame acquisition.

        This method generates random data frames at the specified frame time, updates the acquired indices, and emits an update signal after each frame is acquired.
        """
        self._shouldStop = False

        # if self.frameDim == 2 and self.indexDim == 2:
        #     return self._run_2d_2d(iter)
        i = 0
        while i != iter:
            for idx in itertools.product(*[range(j) for j in self.indexShape]):
                if self._shouldStop:
                    return
                time.sleep(self.exposure)
                self._data[idx] = np.random.rand(*self.frameShape)
                self.updated.emit()
            i += 1

    def _run_2d_2d(self, iter=1):
        """
        _run method for 2D * 2D data.
        """
        i = 0
        while i != iter:
            for j in range(self.indexShape[0]):
                if self._shouldStop:
                    return
                time.sleep(self.exposure*self.indexShape[1])
                self._data[j] = np.random.rand(self.indexShape[1], *self.frameShape)
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
        return not self._error

    @property
    def frameShape(self):
        """
        Shape of each data frame acquired by the detector.

        Returns:
            tuple of int: The shape of each data frame.
        """
        return self._frameShape

    @property
    def indexShape(self):
        """
        Shape of the index grid for data acquisition.

        Returns:
            tuple of int: The shape of the index grid.
        """
        return self._indexShape

    @property
    def axes(self):
        """
        Coordinate axes for each dimension of the data.

        Returns:
            list[numpy.ndarray]: Coordinate axes for each dimension of the data.
        """
        return [np.linspace(0, 1, s) for s in self.dataShape]

    def settingsWidget(self):
        """
        Returns a QWidget for optional settings.

        Returns:
            QtWidgets.QWidget: The optional settings panel.
        """
        return _OptionalPanel(self)


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
        aliveLayout = QtWidgets.QVBoxLayout()
        aliveLayout.addWidget(self._switch, alignment=QtCore.Qt.AlignCenter)
        self.setLayout(aliveLayout)

    def _toggleAlive(self):
        """
        Toggles the alive state of the backend detector and emits relevant signals.
        """
        backend = self._obj
        backend._error = not backend._error
        data = backend._get()
        if data:
            backend.dataAcquired.emit(data)
        backend.aliveStateChanged.emit(backend.isAlive)
