import os

from lys.Qt import QtCore, QtWidgets


class DataStorage(QtCore.QObject):
    pathChanged = QtCore.pyqtSignal(QtCore.QObject)
    stateChanged = QtCore.pyqtSignal(str)
    tagRequest = QtCore.pyqtSignal(dict)

    def __init__(self, root):
        super().__init__()
        self._root = root
        self._base = ""
        self._folder = ""
        self._filename = ""
        self._enabled = True
        self._useNumber = True
        self._threads = []
        self._tags = []
        self._paths = []

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

    def useNumber(self, b):
        self._useNumber = b
        self.pathChanged.emit(self)

    def setEnabled(self, b):
        self._enabled = b
        self.pathChanged.emit(self)

    def enabled(self):
        return self._enabled

    def getNumber(self):
        if self._useNumber:
            i = 0
            f = self.__getPath()
            reserved = [t.path for t in self._threads] + self._paths
            while os.path.exists(f + "/" + self.getFilename() + str(i) + ".npz") or f + "/" + self.getFilename() + str(i) + ".npz" in reserved:
                i += 1
            return i
        else:
            return None

    def reserve(self):
        if self._enabled:
            d = {}
            self.tagRequest.emit(d)
            folder = self.__getPath()
            if self.getNumber() is not None:
                path = folder + "/" + self.getFilename() + str(self.getNumber()) + ".npz"
            else:
                path = folder + "/" + self.getFilename() + ".npz"
            self._tags.append(d)
            self._paths.append(path)
            os.makedirs(folder, exist_ok=True)
        self.stateChanged.emit(self.state())

    def saveImage(self, wave):
        if self._enabled and len(self._paths) > 0:
            wave.note = self._tags[0]
            path = self._paths[0]
            self._tags.pop(0)
            self._paths.pop(0)
            t = _saveThread(wave, path)
            t.finished.connect(self._finished)
            self._threads.append(t)
            t.start()
            self.pathChanged.emit(self)
            self.stateChanged.emit(self.state())

    def _finished(self):
        for i in reversed(range(len(self._threads))):
            if not self._threads[i].isRunning():
                self._threads.remove(self._threads[i])
        self.stateChanged.emit(self.state())

    def __getPath(self):
        folder = self._root + "/" + self.getBaseFolder() + "/" + self.getFolder()
        if not (folder.endswith("pump") or folder.endswith("probe")):
            folder += "/pump"
        return folder

    def state(self):
        if len(self._threads) == 0 and len(self._paths) == 0:
            return "Status: Waiting"
        else:
            return "Status: " + str(len(self._paths)) + " files reserved, " + str(len(self._threads)) + " files being saved"


class _saveThread(QtCore.QThread):
    def __init__(self, wave, path):
        super().__init__()
        self.wave = wave
        self.path = path

    def run(self):
        self.wave.export(self.path)


class DataStorageGUI(QtWidgets.QGroupBox):
    def __init__(self, obj):
        super().__init__("Data Storage")
        self._flg = False
        self._obj = obj
        self.__initlayout()
        self._obj.pathChanged.connect(self._pathChanged)
        self._obj.stateChanged.connect(self._status.setText)

    def __initlayout(self):
        self._status = QtWidgets.QLabel("Status: Waiting")
        self._base = QtWidgets.QLineEdit(textChanged=self._editPath, objectName="DataStorage_base")
        self._folder = QtWidgets.QLineEdit(textChanged=self._editPath, objectName="DataStorage_folder")
        self._name = QtWidgets.QLineEdit(textChanged=self._editPath, objectName="DataStorage_name")
        self._number = QtWidgets.QSpinBox()
        self._number.setEnabled(False)
        self._useNumber = QtWidgets.QCheckBox("Number", toggled=self._editPath, objectName="DataStorage_useNumber")
        self._enabled = QtWidgets.QCheckBox("Enabled", toggled=self._editPath, objectName="DataStrage_enabled")
        g = QtWidgets.QGridLayout()
        g.addWidget(QtWidgets.QLabel("Base Folder"), 0, 0)
        g.addWidget(QtWidgets.QLabel("Data Folder"), 0, 1)
        g.addWidget(QtWidgets.QLabel("Filename"), 0, 2)
        g.addWidget(self._useNumber, 0, 3)
        g.addWidget(self._base, 1, 0)
        g.addWidget(self._folder, 1, 1)
        g.addWidget(self._name, 1, 2)
        g.addWidget(self._number, 1, 3)
        g.addWidget(self._status, 2, 0, 1, 3)
        g.addWidget(self._enabled, 2, 3)
        self.setLayout(g)

    def _editPath(self):
        if self._flg:
            return
        self._flg = True
        self._obj.setBaseFolder(self._base.text())
        self._obj.setFolder(self._folder.text())
        self._obj.setFilename(self._name.text())
        self._obj.useNumber(self._useNumber.isChecked())
        self._obj.setEnabled(self._enabled.isChecked())
        if self._obj.getNumber() is not None:
            self._number.setValue(self._obj.getNumber())
        self._flg = False

    def _pathChanged(self):
        if self._flg:
            return
        self._flg = True
        self._base.setText(self._obj.getBaseFolder())
        self._folder.setText(self._obj.getFolder())
        self._name.setText(self._obj.getFilename())
        self._enabled.setChecked(self._obj.enabled())
        if self._obj.getNumber() is None:
            self._useNumber.setChecked(False)
        else:
            self._useNumber.setChecked(True)
            self._number.setValue(self._obj.getNumber())
        self._flg = False
