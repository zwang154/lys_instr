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

        i = 0
        while i != iter:
            for idx in itertools.product(*[range(i) for i in self.indexShape]):
                if self._shouldStop:
                    return
                time.sleep(self.exposure)
                self._data[idx] = np.random.rand(*self.frameShape)
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
        return self._frameShape
        
    @property
    def indexShape(self):
        return self._indexShape
    
    @property
    def axes(self):
        return [np.linspace(0, 1, s) for s in self.dataShape]

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
