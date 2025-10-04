import pyqtgraph as pg
from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, gui, dummy
from lys_instr.dummy.detectorData import RamanData


class DetectorAdvEx1GUI(gui.MultiDetectorGUI):
    def _update(self):
        if self._frameCount is not None:
            self._mcut.cui.updateRawWave(axes=self._obj.axes)
            i, j = divmod(self._frameCount - 1, self._obj.indexShape[0])
            data = self._mcut.cui.getRawWave()
            self._frameView.clear()
            self._frameView.plot(data.axes[-1], data.data[j])


class AppWindow(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Example #1-2")
        self._storage = DataStorage()
        self._detector = dummy.MultiDetectorDummy(data=RamanData(scanLevel=1), exposure=0.1)
        self._motor = dummy.MultiMotorDummy("x", "y")
        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("AdvEx1_2.dic")
        self.adjustSize()

    def _initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _detectorGUI = DetectorAdvEx1GUI(self._detector)
        _motorGUI = gui.MultiMotorGUI(self._motor)
        _scanGUI = gui.MultiScan.ScanWidget(self._storage, [self._motor], {"MultiDetectorDummy": self._detector}, numScans=2)

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
        mcut.cui._children.clear()
        graph1 = mcut.cui._children.addWave([1, 0])
        mcut.display(graph1, type="grid", pos=(0, 0), wid=(4, 4))

        # Add live frame display
        self._frameView = pg.PlotWidget()
        mcut._grid.layout.addWidget(self._frameView, 4, 0, 1, 4)
        _detectorGUI._frameView = self._frameView

