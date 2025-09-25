import pyqtgraph as pg
from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, gui, dummy


class DetectorAdvEx1GUI(gui.MultiDetectorGUI):
    def __init__(self, obj, wait=False, interval=1, iter=1):
        super().__init__(obj, wait=wait, interval=interval, iter=iter)
        if hasattr(self, "_expTime"):
            self._expTime.setValue(0)
            self._expTime.setEnabled(False)

    def _update(self):
        if hasattr(self, "_data"):
            self._data.axes = self._obj.axes[-2:]
            self._mcut.cui.setRawWave(self._data)
        if hasattr(self._obj, "_frame"):
            self._framePlot.clear()
            self._framePlot.plot(self._obj._frame[0], self._obj._frame[1])


class AppWindow(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Example #1")
        self._storage = DataStorage()
        self._detector = dummy.DetectorAdvEx1Dummy(indexShape=(36,), frameShape=(600,), exposure=0.1)
        self._motor = dummy.MultiMotorDummy("x", "y", "phi")
        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("AdvEx1.dic")
        self.adjustSize()

    def _initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _detectorGUI = DetectorAdvEx1GUI(self._detector)
        _motorGUI = gui.MultiMotorGUI(self._motor)
        _scanGUI = gui.MultiScan.ScanWidget(self._storage, [self._motor], {"DetectorAdvEx1Dummy": self._detector}, numScans=3)

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

        # Set multicut display style
        mcut = _detectorGUI._mcut
        graph1 = mcut.cui._children.addWave([1, 0])
        mcut.display(graph1, type="grid", pos=(0, 0), wid=(3, 4))

        # Add live frame display
        self._framePlot = pg.PlotWidget()
        mcut._grid.layout.addWidget(self._framePlot, 4, 0, 1, 4)
        _detectorGUI._framePlot = self._framePlot

        # Set scan parameters
        # Set scan axis 0 (first row) to 'phi', linear mode, from 0, step 10, 36 steps
        _scanGUI._scanRangeRows[0]._scanAxis.setCurrentText("phi")
        _scanGUI._scanRangeRows[0]._step.setValue(0.1)
        _scanGUI._scanRangeRows[0]._numSteps.setValue(9)
        # Set scan axis 1 (second row) to 'y', linear mode, from 0, step 0.1, 9 steps
        _scanGUI._scanRangeRows[0]._scanAxis.setCurrentText("y")
        _scanGUI._scanRangeRows[0]._step.setValue(0.1)
        _scanGUI._scanRangeRows[0]._numSteps.setValue(9)
        # Set scan axis 2 (third row) to 'x', linear mode, from 0, step 0.1, 8 steps
        _scanGUI._scanRangeRows[1]._scanAxis.setCurrentText("x")
        _scanGUI._scanRangeRows[1]._step.setValue(0.1)
        _scanGUI._scanRangeRows[1]._numSteps.setValue(8)
        _scanGUI._exposure.setValue(0.1)
