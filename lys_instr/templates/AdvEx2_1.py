from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, PreCorrector, gui, dummy
from lys_instr.gui.MultiScan import ScanWidget


class AppWindow(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Example #2-1")
        self._storage = DataStorage()
        self._detector = dummy.MultiDetectorDummy(indexShape=(8, 8), frameShape=(256, 256), exposure=0.1)
        self._motor = dummy.MultiMotorDummy("x", "y", "t")
        self._pre = PreCorrector([self._motor])
        self._switch = dummy.MultiSwitchDummy("A")
        self._storage.connect(self._detector)
        self.setSettingFile("AdvEx2_1.dic")
        self._initLayout()
        
        self.adjustSize()

    def _initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesSettable=("x", "y", "t"), axisNamesJoggable=("t"), axisNamesOffsettable=("x", "y", "t"))
        _switchGUI = gui.MultiSwitchGUI(self._switch)
        _detectorGUI = gui.MultiDetectorGUI(self._detector)
        _correctorGUI = gui.PreCorrectorGUI(self._pre)
        _scanGUI = ScanWidget(self._storage, [self._switch, self._motor], {"MultiDetectorDummy": self._detector}, numScans=2)

        self._tab = QtWidgets.QTabWidget()
        self._tab.addTab(_motorGUI, "Motor")
        self._tab.addTab(_switchGUI, "Switch")
        self._tab.addTab(_scanGUI, "Scan")
        self._tab.addTab(_correctorGUI, "PreCorr")

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
        wave1 = mcut.cui._children.addWave([0, 1])
        canvas1 = mcut.display(wave1, type="grid", pos=(0, 0), wid=(4, 2))
        wave2 = mcut.cui._children.addWave([2, 3])
        canvas2 = mcut.display(wave2, type="grid", pos=(0, 2), wid=(4, 2))
        mcut._can.addRect(canvas1)
        rect = canvas1.getRectAnnotations()[0]
        rect.setRegion([[0.4, 0.6], [0.4, 0.6]])
        canvas1.update()

