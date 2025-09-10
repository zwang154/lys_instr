import time
import itertools
import numpy as np
import pyqtgraph as pg

from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, gui, dummy
from lys_instr.resources import sampleRamanData


class DetectorAdvEx2(dummy.MultiDetectorDummy):
    def __init__(self, indexShape, frameShape, **kwargs):
        super().__init__(indexShape, frameShape, **kwargs)
        self._count = 0

    def _run(self, iter=1):
        self._shouldStop = False

        data = sampleRamanData()     # shape: (8, 9, 36, 2, 600)
        allIndices = list(itertools.product(*(range(s) for s in (8, 9, 36))))
        totalFrames = len(allIndices)

        i = 0
        while i != iter:
            for idx in itertools.product(*(range(s) for s in self.indexShape)):
                if self._shouldStop:
                    return
                time.sleep(self.exposure)
                ijk = allIndices[(self._count * np.prod(self.indexShape) + np.ravel_multi_index(idx, self.indexShape)) % totalFrames]
                self._frame = data[ijk]
                self._data[idx] = data[ijk][1]
                self._axes = [np.linspace(0, 360, 36, endpoint=False), data[ijk][0]]
                self.updated.emit()
            i += 1
            self._count += 1

    @property
    def axes(self):
        if hasattr(self, "_axes"):
            return self._axes
        return [np.linspace(0, 1, s) for s in self.dataShape]


class DetectorAdvEx2GUI(gui.MultiDetectorGUI):
    def _update(self):
        if hasattr(self, "_data"):
            self._data.axes = self._obj.axes
            self._mcut.cui.setRawWave(self._data)
        if hasattr(self._obj, "_frame"):
            self._framePlot.clear()
            self._framePlot.plot(self._obj._frame[0], self._obj._frame[1])


class window(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Example #2")
        self._storage = DataStorage()
        self._detector = DetectorAdvEx2(indexShape=(36,), frameShape=(600,), exposure=0.1)
        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("AdvEx2.dic")
        self.adjustSize()

    def _initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _detectorGUI = DetectorAdvEx2GUI(self._detector)

        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(_storageGUI)
        VBox.addWidget(_detectorGUI)      

        w = QtWidgets.QWidget()
        w.setLayout(VBox)
        self.setWidget(w)
        

        # Set multicut display style
        mcut = _detectorGUI._mcut
        graph1 = mcut.cui._children.addWave([1, 0])
        mcut.display(graph1, type="grid", pos=(0, 0), wid=(3, 4))

        # Add live frame display
        self._framePlot = pg.PlotWidget()
        mcut._grid.layout.addWidget(self._framePlot, 4, 0, 1, 4)
        _detectorGUI._framePlot = self._framePlot


