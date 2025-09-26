from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, PreCorrector, gui, dummy
from lys_instr.gui.MultiScan import ScanWidget


class AppWindow(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setWindowTitle("Advanced Example 2")
        self._storage = DataStorage()
        self._detector = dummy.MultiDetectorDummy((5, 5), (256, 256), exposure=0.1)
        self._motor = dummy.MultiMotorDummy("x", "y", "t")
        self._pre = PreCorrector([self._motor])
        self._switch = dummy.MultiSwitchDummy("A")
        self._storage.connect(self._detector)
        # self.setSettingFile("AdvEx4.dic")
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
        graph1 = mcut.cui._children.addWave([0, 1])
        mcut.display(graph1, type="grid", pos=(0, 0), wid=(4, 2))
        graph2 = mcut.cui._children.addWave([2, 3])
        mcut.display(graph2, type="grid", pos=(0, 2), wid=(4, 2))

        # Set scan parameters
        _scanGUI._scanRangeRows[0]._scanAxis.setCurrentText("A")
        _scanGUI._scanRangeRows[0]._scanMode.setCurrentText("Free")
        _scanGUI._scanRangeRows[0]._freeExpr.setText(str([True,]))
        _scanGUI._scanRangeRows[1]._scanAxis.setCurrentText("t")
        _scanGUI._scanRangeRows[1]._step.setValue(0.1)
        _scanGUI._scanRangeRows[1]._numSteps.setValue(9)
        _scanGUI._check_ref.setChecked(True)
        _scanGUI._combo_ref.setCurrentText("A")      # Reference axis is "A"
        _scanGUI._value_ref.setValue(False)          # Reference value is pump OFF
