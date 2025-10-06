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
