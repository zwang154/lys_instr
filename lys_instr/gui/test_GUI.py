# Start on lys

from lys.widgets import LysSubWindow
from lys.Qt import QtWidgets, QtCore
from lys_instr import DataStorage, gui, dummy


class test_window(LysSubWindow):
    _path = ".lys/instr/setting_test"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Test GUI")
        self._storage = DataStorage()
        self._detector = dummy.MultiDetectorDummy(indexDim=(5, 5), frameDim=(256, 256), frameTime=0.1)
        self._motor = dummy.MultiMotorDummy("y", "z", "α", "x", "β", "γ")
        self._storage.connect(self._detector)

        self.__initLayout()
        self.adjustSize()

        self.setSettingFile(self._path)

    def __initLayout(self):
        _storageGUI = gui.DataStorageGUI(self._storage)
        _motorGUI = gui.MultiMotorGUI(self._motor, axisNamesSettable=("z", "α", "y"), axisNamesJoggable=("z"), axisNamesOffsettable=("y", "z"))
        _detectorGUI = gui.MultiDetectorGUI(self._detector)

        #_scanGUI = gui.ScanWidget(self._storage, [self._motor], {"detector1": self._detector})

        self._tab = QtWidgets.QTabWidget()
        self._tab.addTab(_motorGUI, "Motor")
        #self._tab.addTab(_scanGUI, "Scan")

        VBox = QtWidgets.QVBoxLayout()
        VBox.addWidget(_storageGUI)
        VBox.addWidget(self._tab)

        HBox = QtWidgets.QHBoxLayout()
        HBox.addLayout(VBox)
        HBox.addWidget(_detectorGUI)
        

        w = QtWidgets.QWidget()
        w.setLayout(HBox)
        self.setWidget(w)       # cannot set layout
