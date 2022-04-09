import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox, QHBoxLayout, QPushButton, QGroupBox
from PyQt5.QtCore import QThread, QMutex, QMutexLocker, pyqtSignal, QObject


class ScanRangeLayout(QGridLayout):
    def __init__(self, title, items):
        super().__init__()
        self.__initlayout(title, items)
        self._scan.currentTextChanged.connect(self._changeScan)

    def __initlayout(self, title, items):
        self._type = QComboBox(objectName="ScanRange_type_" + title)
        self._type.addItems(list(items) + ["None"])
        self._type.currentTextChanged.connect(self._changeType)
        self._scan = QComboBox(objectName="ScanRange_scan_" + title)
        self._scan.addItems(["Linear", "Free"])
        self._from = QDoubleSpinBox(objectName="ScanRange_from_" + title)
        self._step = QDoubleSpinBox(objectName="ScanRange_step_" + title)
        self._loop = QSpinBox(objectName="ScanRange_loop_" + title)
        self._from.setRange(-np.inf, np.inf)
        self._step.setRange(-np.inf, np.inf)
        self._from.setDecimals(4)
        self._step.setDecimals(4)
        self._loop.setRange(1, 100000)
        self._free = QLineEdit(objectName="ScanRange_free_" + title)

        self._fromLabel = QLabel("From")
        self._stepLabel = QLabel("Step")
        self._loopLabel = QLabel("Loop")
        self._freeLabel = QLabel("Expression")

        self.addWidget(QLabel(title), 0, 0)
        self.addWidget(QLabel("Type"), 0, 1)
        self.addWidget(self._fromLabel, 0, 2)
        self.addWidget(self._stepLabel, 0, 3)
        self.addWidget(self._loopLabel, 0, 4)
        self.addWidget(self._freeLabel, 0, 5)
        self.addWidget(self._type, 1, 0)
        self.addWidget(self._scan, 1, 1)
        self.addWidget(self._from, 1, 2)
        self.addWidget(self._step, 1, 3)
        self.addWidget(self._loop, 1, 4)
        self.addWidget(self._free, 1, 5)

        self._free.hide()
        self._freeLabel.hide()

    def _changeType(self, text):
        b = text != "None"
        self._scan.setEnabled(b)
        self._from.setEnabled(b)
        self._step.setEnabled(b)
        self._loop.setEnabled(b)
        self._free.setEnabled(b)

    def _changeScan(self, text):
        if text == "Linear":
            self._free.hide()
            self._freeLabel.hide()
            self._from.show()
            self._fromLabel.show()
            self._step.show()
            self._stepLabel.show()
            self._loop.show()
            self._loopLabel.show()
        else:
            self._free.show()
            self._freeLabel.show()
            self._from.hide()
            self._fromLabel.hide()
            self._step.hide()
            self._stepLabel.hide()
            self._loop.hide()
            self._loopLabel.hide()

    def getScanName(self):
        return self._type.currentText()

    def getScanRange(self):
        if self._scan.currentText() == "Linear":
            values = [self._from.value() + i * self._step.value() for i in range(self._loop.value())]
        elif self._Scan.currenText() == "Free":
            values = eval(self._free.text())
        return values


class ScanTab(QWidget):
    def __init__(self, storage, scan, process):
        super().__init__()
        self._storage = storage
        self._scan = scan
        self._process = process
        self.__initlayout(scan, process)

    def __initlayout(self, scan, process):
        self._text = QLabel("[Status] Waiting...")

        self._scans = [ScanRangeLayout("Scan " + str(i), scan.keys()) for i in range(2)]
        v1 = QVBoxLayout()
        for s in self._scans:
            v1.addLayout(s)
        g1 = QGroupBox("Scan")
        g1.setLayout(v1)

        self._type = QComboBox(objectName="ScanTab_type")
        self._type.addItems(process.keys())
        self._type.currentTextChanged.connect(self._changeProcess)
        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Type"))
        v2.addWidget(self._type)
        for item in process.values():
            v2.addWidget(item)
        g2 = QGroupBox("Process")
        g2.setLayout(v2)

        buttons = QHBoxLayout()
        self.__start = QPushButton('Start', clicked=self.__startscan)
        self.__stop = QPushButton('Stop', clicked=self.__stopscan)
        buttons.addWidget(self.__start)
        buttons.addWidget(self.__stop)

        layout = QVBoxLayout()
        layout.addWidget(self._text)
        layout.addWidget(g1)
        layout.addWidget(g2)
        layout.addStretch()
        layout.addLayout(buttons)

        self.setLayout(layout)

    def _changeProcess(self, text):
        for key, item in self._process.items():
            item.setVisible(key == text)

    def __startscan(self):
        scans = [s for s in self._scans if s.getScanName() != "None"]
        process = self._process[self._type.currentText()].getProcess()
        for i, s in enumerate(reversed(scans)):
            process = Scanner(s.getScanName(), self._scan[s.getScanName()], s.getScanRange(), process, addFolder=i != 0, addName=i == 0)
        process.updated.connect(lambda s: self._text.setText("[Scanning...] " + s))
        self._text.setText("[Status] Staring...")
        self._storage.useNumber(False)
        self._storage.setEnabled(True)
        self.thread = Executor(process, self._storage)
        self.thread.finished.connect(self.__finishscan)
        self.__start.setEnabled(False)
        self.__oldFolder = self._storage.getFolder()
        self.__oldFilename = self._storage.getFilename()
        self.thread.start()

    def __stopscan(self):
        self.thread.kill()

    def __finishscan(self):
        self.__start.setEnabled(True)
        self._storage.setFolder(self.__oldFolder)
        self._storage.setFilename(self.__oldFilename)
        self._storage.useNumber(True)
        self._text.setText("[Status] Finished. Waiting...")


class Scanner(QObject):
    updated = pyqtSignal(str)

    def __init__(self, name, obj, values, process, addFolder=False, addName=False):
        super().__init__()
        self._name = name
        self._obj = obj
        self._values = values
        self._addFolder = addFolder
        self._addName = addName
        self._process = process
        self._process.updated.connect(self._update)
        self._stopped = False
        self.mutex = QMutex()

    def execute(self, storage):
        folder_old, name_old = storage.getFolder(), storage.getFilename()
        for i, value in enumerate(self._values):
            if self._stopped:
                return
            self._obj.set(value, wait=True)
            if self._addFolder:
                storage.setFolder(folder_old + "/" + self._name + str(i))
            if self._addName:
                storage.setFilename(name_old + "_" + self._name + str(i))
            self._process.execute(storage)
        storage.setFolder(folder_old)
        storage.setFilename(name_old)

    def stop(self):
        with QMutexLocker(self.mutex):
            self._stopped = True
        self._process.stop()

    def _update(self, text):
        state = self._name + ": " + str(self._obj.get()) + ", " + text
        self.updated.emit(state)


class DummyProcess(QObject):
    updated = pyqtSignal(str)

    def execute(self, storage):
        self.updated.emit("execute: " + storage.getFolder() + " " + storage.getFilename())

    def stop(self):
        pass


class Executor(QThread):
    def __init__(self, process, storage):
        super().__init__()
        self.process = process
        self.storage = storage

    def run(self):
        self.process.execute(self.storage)

    def kill(self):
        self.process.stop()
