import numpy as np
import time
import itertools

from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, gui, dummy
from lys_instr.gui.Scan import ScanWidget


class DetectorEx1(dummy.MultiDetectorDummy):
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
                self._data[idx] = y
                self.axes = [x]
                self.updated.emit()
            i += 1
            self._count += 1

    @staticmethod
    def _gauss1d(x, A, x0, sigma, offset):
        return A * np.exp(-(x - x0) ** 2 / (2 * sigma ** 2)) + offset

    @property
    def axes(self):
        return [np.linspace(0, 1, s) for s in self.dataShape]
    
    @axes.setter
    def axes(self, axes):
        self._axes = axes


class DetectorEx1GUI(gui.MultiDetectorGUI):
    def _update(self):
        if hasattr(self, "_data"):
            self._data.axes = [self._obj.axes[0]]
            self._mcut.cui.setRawWave(self._data)


class window(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Example #1")
        self._detector = DetectorEx1(indexShape=(1,), frameShape=(256,), exposure=0.1)
        self._motor = dummy.MultiMotorDummy("x")
        self._storage = DataStorage()
        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("Ex1.dic")
        self.adjustSize()

    def _initLayout(self):
        _detectorGUI = DetectorEx1GUI(self._detector)
        _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesJoggable=(), axisNamesOffsettable=("x"))
        _storageGUI = gui.DataStorageGUI(self._storage)

        _scanGUI = ScanWidget(self._storage, [self._motor], {"DetectorEx1": self._detector})

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



        # Adapt multicut for 1D array display
        mcut = _detectorGUI._mcut
        graph = mcut.cui._children.addWave([1])
        # axes = list(range(len(self._detector.dataShape)))[-self._detector.frameDim:]
        # graph = mcut.cui._children.addWave(axes)
        mcut.display(graph, type="grid", pos=(0, 0), wid=(4, 4))