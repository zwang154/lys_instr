from lys_instr import DataStorage, gui, dummy
from lys.Qt import QtWidgets
from lys.widgets import LysSubWindow


class Window(LysSubWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hands-on GUI")
        self._storage = DataStorage()
        self._detector = dummy.MultiDetectorDummy(indexShape=(), frameShape=(128, 128), exposure=0.1)
        self._motor = dummy.MultiMotorDummy("E")
        self._storage.connect(self._detector)
        self._initLayout()
        self.setSettingFile("template0.dic")
        self.adjustSize()

    def _initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _motorGUI = gui.MultiMotorGUI(self._motor)
        _detectorGUI = gui.MultiDetectorGUI(self._detector)
        _scanGUI = gui.ScanWidget(self._storage, [self._motor], [], {"MultiDetectorDummy": self._detector})
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