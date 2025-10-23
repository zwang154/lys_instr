from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, gui, dummy


class TemplateWindow(LysSubWindow):
    def __init__(self, motor=None, detector=None, detectorName="Detector 1", numScans=3):
        super().__init__()
        self.setWindowTitle("template4")
        self._storage = DataStorage()
        self._detector = detector if detector else dummy.MultiDetectorDummy(indexShape=(9, 9), frameShape=(256, 256))
        self._motor = motor if motor else dummy.MultiMotorDummy("t")
        self._storage.connect(self._detector)
        self._detectorName = detectorName
        self._numScans = numScans
        self._initLayout()
        self.setSettingFile("template4.dic")
        self.adjustSize()

    def _initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _motorGUI = gui.MultiMotorGUI(self._motor)
        _detectorGUI = gui.MultiDetectorGUI(self._detector)
        _scanGUI = gui.MultiScan.ScanWidget(self._storage, [self._motor], [], {self._detectorName: self._detector}, numScans=self._numScans)

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

        # # Set multicut display style
        # mcut = _detectorGUI._mcut
        # wave1 = mcut.cui._children.addWave([0, 1])
        # canvas1 = mcut.display(wave1, type="grid", pos=(0, 0), wid=(4, 2))
        # wave2 = mcut.cui._children.addWave([2, 3])
        # canvas2 = mcut.display(wave2, type="grid", pos=(0, 2), wid=(4, 2))
        # mcut._can.addRect(canvas1)
        # rect = canvas1.getRectAnnotations()[0]
        # rect.setRegion([[0.4, 0.6], [0.4, 0.6]])
        # canvas1.update()

