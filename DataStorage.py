from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QLineEdit, QSpinBox


class DataStorage(QObject):
    pathChanged = pyqtSignal(QObject)
    stateChanged = pyqtSignal(str)
    tagRequest = pyqtSignal(dict)
    root = "\\\\192.168.12.203\\smb\\data2\\"

    def __init__(self):
        super().__init__()
        self._base = ""
        self._folder = ""
        self._filename = ""

    def setBaseFolder(self, folder):
        self._base = folder
        self.pathChanged.emit(self)

    def getBaseFolder(self):
        return self._base

    def setFolder(self, folder):
        self._folder = folder
        self.pathChanged.emit(self)

    def getFolder(self):
        return self._folder

    def setFilename(self, name):
        self._filename = name
        self.pathChanged.emit(self)

    def getFilename(self):
        return self._filename

    def getNumber(self):
        return 0

    def state(self):
        return "test"


class DataStorageGUI(QGroupBox):
    def __init__(self, obj):
        super().__init__("Data Storage")
        self._flg = False
        self._obj = obj
        self.__initlayout()
        self._obj.pathChanged.connect(self._pathChanged)

    def __initlayout(self):
        self._status = QLabel("Status: Waiting")
        self._base = QLineEdit(textChanged=self._editPath)
        self._folder = QLineEdit(textChanged=self._editPath)
        self._name = QLineEdit(textChanged=self._editPath)
        self._number = QSpinBox()
        self._number.setEnabled(False)
        g = QGridLayout()
        g.addWidget(QLabel("Base Folder"), 0, 0)
        g.addWidget(QLabel("Data Folder"), 0, 1)
        g.addWidget(QLabel("Filename"), 0, 2)
        g.addWidget(QLabel("Number"), 0, 3)
        g.addWidget(self._base, 1, 0)
        g.addWidget(self._folder, 1, 1)
        g.addWidget(self._name, 1, 2)
        g.addWidget(self._number, 1, 3)
        g.addWidget(self._status, 2, 0, 1, 3)
        self.setLayout(g)

    def _editPath(self):
        if self._flg:
            return
        self._flg = True
        self._obj.setBaseFolder(self._base.text())
        self._obj.setFolder(self._folder.text())
        self._obj.setFilename(self._name.text())
        self._flg = False

    def _pathChanged(self):
        if self._flg:
            return
        self._base.setText(self._obj.getBaseFolder())
        self._folder.setText(self._obj.getFolder())
        self._name.setText(self._obj.getFilename())
        self._number.setValue(self._obj.getNumber())
