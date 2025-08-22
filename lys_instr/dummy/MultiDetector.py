import numpy as np
import time

from lys_instr.MultiDetector import MultiDetectorInterface
from lys.Qt import QtWidgets, QtCore


class MultiDetectorDummy(MultiDetectorInterface):
    """
    Dummy implementation of ``MultiDetectorInterface``.

    This class simulates a detector controller for indexed/arrayed data acquisition and error injection for testing purposes.
    """
    def __init__(self, indexDim=None, frameDim=None, frameTime=None, **kwargs):
        """
        Initializes the dummy multi-detector with the given parameters.

        Args:
            indexDim (tuple of int, optional): Dimensions of the index grid.
            frameDim (tuple of int, optional): Dimensions of each data frame.
            frameTime (float, optional): Time per frame in seconds.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(indexDim=indexDim, **kwargs)
        self._data = {}
        self._frameDim = frameDim
        self._frameTime = frameTime
        self._error = False
        self.start()

    def _run(self, streaming):
        """
        Runs the acquisition thread associated with the ``MultiDetectorInterface``, simulating indexed/arrayed data frame acquisition.

        This method generates random data frames at the specified frame time, updates the acquired indices, and emits an update signal after each frame is acquired.
        """
        self._acquiredIndices = []
        startNum = 0
        endNum = None if streaming else startNum + np.product(self.indexDim)

        self._shouldStop = False

        i = startNum
        while not self._shouldStop and (endNum is None or i < endNum):
            time.sleep(self._frameTime)
            idx = (i // np.product(self.indexDim), i % np.product(self.indexDim) % self.indexDim[0], i % np.product(self.indexDim) // self.indexDim[0])
            self._data[idx] = np.random.rand(*self._frameDim)
            self._acquiredIndices.append(idx)
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
    def dataShape(self):
        """
        Returns the shape of the data that the detector would return.

        The shape is a combination of the index dimensions and the frame dimensions.

        Returns:
            tuple: Shape of the data.
        """
        return (*self.indexDim, *self._frameDim)
    
    def settingWidget(self):
        return _GeneralPanel(self)


class _GeneralPanel(QtWidgets.QWidget):
    def __init__(self, obj):
        super().__init__()
        self.setWindowTitle("Settings")
        self._obj = obj
        self._initLayout()

    def _initLayout(self):
        self._switch = QtWidgets.QPushButton("Change", clicked=self._toggleAlive)

        aliveLayout = QtWidgets.QVBoxLayout()
        aliveLayout.addWidget(self._switch, alignment=QtCore.Qt.AlignCenter)

        # Combine layouts
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(aliveLayout)
        self.setLayout(mainLayout)
        
    def _toggleAlive(self):
        backend = self._obj
        backend._error = not backend._error
        if (data := backend._get()):
            backend.dataAcquired.emit(data)
        backend.aliveStateChanged.emit(backend.isAlive)
