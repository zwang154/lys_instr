# Start on lys

from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets
from lys_instr import DataStorage, gui, dummy
from lys_instr.gui.MultiScan import ScanWidget


class window(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Example 1")
        self._storage = DataStorage()
        self._detector = dummy.MultiDetectorDummy((4, 4), (32, 32), exposure=0.1)
        self._motor = dummy.MultiMotorDummy("x", "y", "z", "α", "β", "γ")
        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("Example1.dic")
        self.adjustSize()

    def _initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesSettable=("x", "y", "z"), axisNamesJoggable=("z"), axisNamesOffsettable=("y", "z"))
        _detectorGUI = gui.MultiDetectorGUI(self._detector)
        _scanGUI = ScanWidget(self._storage, [self._motor], {"MultiDetectorDummy": self._detector})

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

