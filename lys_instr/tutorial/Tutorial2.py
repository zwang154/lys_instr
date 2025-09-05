import numpy as np
import time
import itertools

from lys import Wave
from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, gui, dummy
from lys_instr.gui.Scan import ScanWidget


class DetectorT2(dummy.MultiDetectorDummy):
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
                x0 = (128 + 8 * self._count) % 256
                x, y = np.meshgrid(np.linspace(0, 255, self.frameShape[1]), np.linspace(0, 255, self.frameShape[0]))
                self._data[idx] = self._gauss2d(x, y, 1, x0, 128, 32, 32, 0)
                self.updated.emit()
            i += 1
            self._count += 1

    @staticmethod
    def _gauss2d(x, y, A, x0, y0, sigma_x, sigma_y, offset):
        return A * np.exp(-((x - x0) ** 2 / (2 * sigma_x ** 2) + (y - y0) ** 2 / (2 * sigma_y ** 2))) + offset


class window(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tutorial 2")
        self._detector = DetectorT2(indexShape=(1,), frameShape=(256, 256), exposure=0.1)
        self._motor = dummy.MultiMotorDummy("x")
        self._storage = DataStorage()
        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("Tutorial2.dic")
        self.adjustSize()

    def _initLayout(self):
        _detectorGUI = gui.MultiDetectorGUI(self._detector)
        _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesJoggable=(), axisNamesOffsettable=("x"))
        _storageGUI = gui.DataStorageGUI(self._storage)

        _scanGUI = ScanWidget(self._storage, [self._motor], {"DetectorT2": self._detector})

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

        # Adapt multicut for 2D image display
        mcut = _detectorGUI._mcut
        # image = mcut.cui._children.addWave([1, 2])
        axes = list(range(len(self._detector.dataShape)))[-self._detector.frameDim:]
        image = mcut.cui._children.addWave(axes)
        mcut.display(image, type="grid", pos=(0, 0), wid=(4, 4))

