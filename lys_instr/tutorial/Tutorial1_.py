import numpy as np
import time
import itertools

from lys import Wave
from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, gui, dummy
from lys_instr.gui.Scan import ScanWidget


class DetectorT1(dummy.MultiDetectorDummy):
    def __init__(self, indexShape, frameShape, **kwargs):
        super().__init__(indexShape, frameShape, **kwargs)
        self._count = 0

    def _run(self, iter=1):
        self._shouldStop = False

        i = 0
        while i != iter:
            for idx in itertools.product(*(range(s) for s in self.indexShape)):
                if self._shouldStop:
                    return
                time.sleep(self.exposure)
                x = np.linspace(0, 255, 256)
                x0 = (128 + 8 * self._count) % 256
                y = self._gauss1d(x, 1, x0, 32, 0)
                self._data[idx] = np.array([x, y])
                self.updated.emit()
            i += 1
            self._count += 1

    @staticmethod
    def _gauss1d(x, A, x0, sigma, offset):
        return A * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2)) + offset


class DetectorT1GUI(gui.MultiDetectorGUI):
    def _update(self):
        if hasattr(self, "_data"):
            frame = self._data.data[self._lastIdx[-self._obj.frameDim:]]
            self._mcut.display(Wave(frame[1], frame[0]), type="grid", pos=(0, 0), wid=(4, 4))

    def _dataAcquired(self, data):
        if not hasattr(self, "_data"):
            self._frameCount = 0
            self._data = Wave(np.zeros(self._obj.dataShape), *self._obj.axes)            

        if data:
            for idx, frame in data.items():
                self._data.data[idx[-frame.ndim:]] = frame
                # Added to track last acquired index
                self._lastIdx = idx
            self._frameCount += 1

            # Update frame display every N frames or on last frame
            if self._frameCount == np.prod(self._obj.indexShape):
                update = True
            else:
                update = False if self._params["interval"] is None else self._frameCount % self._params["interval"] == 0

            if update:
                self._update()


class window(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tutorial 1")
        self._detector = DetectorT1(indexShape=(1,), frameShape=(2, 256), exposure=0.1)
        self._motor = dummy.MultiMotorDummy("x")
        self._storage = DataStorage()
        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("Tutorial1.dic")
        self.adjustSize()

    def _initLayout(self):
        _detectorGUI = DetectorT1GUI(self._detector)
        _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesJoggable=(), axisNamesOffsettable=("x"))
        _storageGUI = gui.DataStorageGUI(self._storage)

        _scanGUI = ScanWidget(self._storage, [self._motor], {"DetectorT1": self._detector})

        self._tab = QtWidgets.QTabWidget()
        self._tab.addTab(_motorGUI, "Motor")
        self._tab.addTab(_scanGUI, "Scan")

        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(_storageGUI)
        VBox.addWidget(self._tab)

        HBox = QtWidgets.QHBoxLayout()
        HBox.addLayout(VBox)
        HBox.addWidget(_detectorGUI)
        
        w = QtWidgets.QWidget()
        w.setLayout(HBox)
        self.setWidget(w)



