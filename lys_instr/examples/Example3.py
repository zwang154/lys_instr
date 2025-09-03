import time
import itertools
from lys_instr.resources import sampleRamanData

from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, gui, dummy
from lys_instr.gui.MultiScan import ScanWidget


class SpectrometerDummy(dummy.MultiDetectorDummy):
    def __init__(self, indexShape=(36,), frameShape=(600,), exposure=0.1, **kwargs):
        super().__init__(indexShape, frameShape, exposure=exposure, **kwargs)

    def _run(self, iter=1):
        self._shouldStop = False

        data = sampleRamanData()[:, :, :, 1, :]
        shape = data.shape[:3]  # (11, 21, 36)
        allIndices = list(itertools.product(*(range(s) for s in shape)))  # List of (i, j, k)
        totalFrames = len(allIndices)

        i = 0
        while i != iter:
            for idx in range(self.indexShape[0]):
                if self._shouldStop:
                    return
                time.sleep(self.exposure)
                ijk = allIndices[(i * self.indexShape[0] + idx) % totalFrames]
                self._data[(idx,)] = data[ijk[0], ijk[1], ijk[2], :]
                self.updated.emit()
            i += 1


class window(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Example 1")
        self._storage = DataStorage()
        self._detector = SpectrometerDummy(indexShape=(36,), frameShape=(600,))
        self._motor = dummy.MultiMotorDummy("x", "y")
        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("Example3.dic")
        self.adjustSize()

    def _initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesSettable=("x", "y"), axisNamesJoggable=("x", "y"), axisNamesOffsettable=("x", "y"))
        _detectorGUI = gui.MultiDetectorGUI(self._detector)
        _scanGUI = ScanWidget(self._storage, [self._motor], {"SpectrometerDummy": self._detector})

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
        self.setWidget(w)       # cannot set layout

        # self.adjustSize()

