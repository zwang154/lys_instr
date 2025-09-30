from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, gui, dummy
from lys_instr.dummy.detectorData import RamanData


class AppWindow(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Example #1-1")
        self._storage = DataStorage()
        self._detector = dummy.MultiDetectorDummy(data=RamanData(scanLevel=0), exposure=0.1)
        self._motor = dummy.MultiMotorDummy("x", "y", "phi")
        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("AdvEx1_1.dic")
        self.adjustSize()

    def _initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _detectorGUI = gui.MultiDetectorGUI(self._detector)
        _motorGUI = gui.MultiMotorGUI(self._motor)
        _scanGUI = gui.MultiScan.ScanWidget(self._storage, [self._motor], {"MultiDetectorDummy": self._detector}, numScans=3)

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

        # Enable exposure time setting in scan GUI and disable it in detector GUI
        _scanGUI._exposure.setValue(0.1)
        # _detectorGUI._expTime.setValue(0)
        # _detectorGUI._expTime.setEnabled(False)
