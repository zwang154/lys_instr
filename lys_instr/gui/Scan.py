import numpy as np
from lys.Qt import QtWidgets, QtCore


class _ScanRangeRow(QtWidgets.QGridLayout):
    def __init__(self, title, scannerNames):
        super().__init__()
        self._initLayout(title, scannerNames)
        self._scanMode.currentTextChanged.connect(self._scanModeChanged)

    def _initLayout(self, title, scannerNames):
        self._scanAxis = QtWidgets.QComboBox(objectName="ScanRange_scanAxis_" + title)
        self._scanAxis.addItems(list(scannerNames) + ["None"])
        self._scanAxis.currentTextChanged.connect(self._scanAxisChanged)
        self._scanMode = QtWidgets.QComboBox(objectName="ScanRange_scan_" + title)
        self._scanMode.addItems(["Linear", "Free"])
        self._from = QtWidgets.QDoubleSpinBox(objectName="ScanRange_from_" + title)
        self._step = QtWidgets.QDoubleSpinBox(objectName="ScanRange_step_" + title)
        self._numSteps = QtWidgets.QSpinBox(objectName="ScanRange_numSteps_" + title)
        self._from.setRange(-np.inf, np.inf)
        self._step.setRange(-np.inf, np.inf)
        self._from.setDecimals(4)
        self._step.setDecimals(4)
        self._numSteps.setRange(1, 100000)
        self._freeExpr = QtWidgets.QLineEdit(objectName="ScanRange_freeExpr_" + title)

        self._fromLabel = QtWidgets.QLabel("From")
        self._stepLabel = QtWidgets.QLabel("Step")
        self._numStepsLabel = QtWidgets.QLabel("Number of steps")
        self._freeExprLabel = QtWidgets.QLabel("Expression")

        self.addWidget(QtWidgets.QLabel(title), 0, 0)
        self.addWidget(QtWidgets.QLabel("Mode"), 0, 1)
        self.addWidget(self._fromLabel, 0, 2)
        self.addWidget(self._stepLabel, 0, 3)
        self.addWidget(self._numStepsLabel, 0, 4)
        self.addWidget(self._freeExprLabel, 0, 5)
        self.addWidget(self._scanAxis, 1, 0)
        self.addWidget(self._scanMode, 1, 1)
        self.addWidget(self._from, 1, 2)
        self.addWidget(self._step, 1, 3)
        self.addWidget(self._numSteps, 1, 4)
        self.addWidget(self._freeExpr, 1, 5)

        self._freeExpr.hide()
        self._freeExprLabel.hide()

    def _scanAxisChanged(self, text):
        b = text not in ["None", "loop"]
        if text == "None":
            self._numSteps.setEnabled(False)
        elif text == "loop":
            self._scanMode.setCurrentIndex(0)
            self._from.setValue(0)
            self._step.setValue(1)
            self._numSteps.setEnabled(True)
        else:
            self._numSteps.setEnabled(True)
        self._scanMode.setEnabled(b)
        self._from.setEnabled(b)
        self._step.setEnabled(b)
        self._freeExpr.setEnabled(b)

    def _scanModeChanged(self, text):
        if text == "Linear":
            self._freeExpr.hide()
            self._freeExprLabel.hide()
            self._from.show()
            self._fromLabel.show()
            self._step.show()
            self._stepLabel.show()
            self._numSteps.show()
            self._numStepsLabel.show()
        else:
            self._freeExpr.show()
            self._freeExprLabel.show()
            self._from.hide()
            self._fromLabel.hide()
            self._step.hide()
            self._stepLabel.hide()
            self._numSteps.hide()
            self._numStepsLabel.hide()

    @property
    def scanName(self):
        return self._scanAxis.currentText()

    @property
    def scanRange(self):
        if self._scanMode.currentText() == "Linear":
            values = [self._from.value() + i * self._step.value() for i in range(self._numSteps.value())]
        elif self._scanMode.currentText() == "Free":
            values = eval(self._freeExpr.text())
        return values


class ScanWidget(QtWidgets.QWidget):
    def __init__(self, storage, motors, detectors):
        """
        Initializes the ScanTab with storage, motors, and detectors.
        Args:
            storage (DataStorage): The data storage object.
            motors (list of MultiMotor): List of motor objects.
            detectors (dict of MultiDetector): Dictionary of detector objects whose key is used to identify them.
        """
        super().__init__()
        self._storage = storage
        self._scanners = self._initScanners(motors)
        self._detectors = detectors         # Dictionary of detector objects
        self._process = {key: BaseProcess(detector) for key, detector in detectors.items()}
        self._initLayout(self._scanners, self._process)

    def _initScanners(self, motors):
        scanners = {"loop": _Loop()}        # Dummy loop as the first scanner
        for motor in motors:
            scanners.update({axis: motor for axis in motor.nameList})
        return scanners
    
    def _initLayout(self, scanners, process):
        self._statusLabel = QtWidgets.QLabel("[Status] Idle.")
        self._scanRangeRows = [_ScanRangeRow(f"Scan {i}", scanners.keys()) for i in range(3)]

        scansBox = QtWidgets.QGroupBox("Scan")
        scansLayout = QtWidgets.QVBoxLayout()
        for s in self._scanRangeRows:
            scansLayout.addLayout(s)
        scansBox.setLayout(scansLayout)

        processBox = QtWidgets.QGroupBox("Process")
        self._detectorsBox = QtWidgets.QComboBox(objectName="ScanTab_detectors")
        self._detectorsBox.addItems(process.keys())
        self._detectorsBox.currentTextChanged.connect(self._processChanged)
        detectorsLayout = QtWidgets.QFormLayout()
        detectorsLayout.addRow("Detectors", self._detectorsBox)
        processBox.setLayout(detectorsLayout)

        btnsLayout = QtWidgets.QHBoxLayout()
        self._startBtn = QtWidgets.QPushButton("Start", clicked=self._start)
        self._stopBtn = QtWidgets.QPushButton("Stop", clicked=self._stop)
        self._stopBtn.setEnabled(False)
        btnsLayout.addWidget(self._startBtn)
        btnsLayout.addWidget(self._stopBtn)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._statusLabel)
        layout.addWidget(scansBox)
        layout.addWidget(processBox)
        layout.addLayout(btnsLayout)
        layout.addStretch()

        self.setLayout(layout)

    def _processChanged(self, text):
        for key, item in self._process.items():
            item.setVisible(key == text)

    def _start(self):
        scans = [s for s in self._scanRangeRows if s.scanName != "None"]      # self._scanRangeRows are _ScanRangePanel instances
        process = self._process[self._detectorsBox.currentText()]
        for i, s in enumerate(scans):
            process = ScanProcess(s.scanName, self._scanners[s.scanName], s.scanRange, process, addFolder=(i != 0), addName=(i == 0))

        process.statusUpdated.connect(lambda s: self._statusLabel.setText("[Scanning...] " + s))

        self._statusLabel.setText("[Status] Starting...")
        self._storage.numbered = False
        self._storage.enabled = True
        self._storage.tagRequest.connect(self._setScanNames)

        self._thread = Executor(process, self._storage)
        self._thread.finished.connect(self._scanFinished)

        self._startBtn.setEnabled(False)
        self._stopBtn.setEnabled(True)
        self._oldFolder = self._storage.folder
        self._oldName = self._storage.name
        self._thread.start()

    def _stop(self):
        self._thread.kill()

    def _scanFinished(self):
        self._startBtn.setEnabled(True)
        self._stopBtn.setEnabled(False)
        self._storage.folder = self._oldFolder
        self._storage.name = self._oldName
        self._storage.numbered = True
        self._statusLabel.setText("[Status] Finished.")

    def _setScanNames(self, scanNamesDict):
        scanNamesDict["scanNames"] = [s.scanName for s in self._scanRangeRows if s.scanName != "None"]


class _Loop(QtCore.QObject):
    def __init__(self, name="loop"):
        super().__init__()
        self._name = name
        self._value = None

    def set(self, *args, **kwargs):
        if args:
            self._value = args[0]
        elif kwargs:
            self._value = next(iter(kwargs.values()))
        else:
            raise ValueError("No value provided to _Loop.set()")

    def get(self):
        return {self._name: self._value}


class Executor(QtCore.QThread):
    def __init__(self, process, storage):
        super().__init__()
        self.process = process
        self.storage = storage

    def run(self):
        self.process.execute(self.storage)

    def kill(self):
        self.process.stop()


class ProcessInterface(QtCore.QObject):
    def execute(self, storage):
        raise NotImplementedError("Subclasses should implement this method.")

    def stop(self):
        pass


class DummyProcess(ProcessInterface):
    statusUpdated = QtCore.pyqtSignal(str)

    def execute(self, storage):
        self.statusUpdated.emit(f"[Executing] Folder: {storage.folder} | Name: {storage.name}")

    def stop(self):
        pass


class BaseProcess(ProcessInterface):
    statusUpdated = QtCore.pyqtSignal(str)
    quitRequested = QtCore.pyqtSignal()

    def __init__(self, detector):
        super().__init__()
        self._detector = detector

    def execute(self, storage):
        loop = QtCore.QEventLoop()
        self.quitRequested.connect(loop.quit)

        def onFinished(busy):
            if not busy:
                self.quitRequested.emit()

        self._detector.busyStateChanged.connect(onFinished)
        self._detector.startAcq()
        loop.exec_()
        self._detector.busyStateChanged.disconnect(onFinished)
        self.quitRequested.disconnect(loop.quit)
        self.statusUpdated.emit(f"[Executing] Folder: {storage.folder} | Name: {storage.name}")

    def stop(self):
        pass


class ScanProcess(ProcessInterface):
    statusUpdated = QtCore.pyqtSignal(str)

    def __init__(self, name, obj, values, process, addFolder=False, addName=False):
        super().__init__()
        self._name = name
        self._obj = obj
        self._values = values
        self._addFolder = addFolder
        self._addName = addName
        self._process = process
        self._process.statusUpdated.connect(self._statusUpdated)
        self._shouldStop = False
        self._mutex = QtCore.QMutex()

    def execute(self, storage):
        oldFolder = storage.folder
        oldName = storage.name
        currentFolder = oldFolder

        for i, value in enumerate(self._values):
            if self._shouldStop:
                return
            self._obj.set(**{self._name: value}, wait=True)      # obj is a MultiMotor instance or a Loop instance
            if self._addFolder:
                currentFolder = f"{oldFolder}/{self._name}{str(i).zfill(len(str(len(self._values))))}"
                storage.folder = currentFolder
            else:
                storage.folder = currentFolder
            if self._addName:
                storage.name = f"{oldName}_{self._name}{i}"
            self._process.execute(storage)          # At the beginning of execution (-> statusUpdated.emit -> _statusUpdated() -> self._obj.get()), the motor has already started moving.

        storage.folder = oldFolder
        storage.name = oldName

    def stop(self):
        with QtCore.QMutexLocker(self._mutex):
            self._shouldStop = True
        self._process.stop()

    def _statusUpdated(self, text):
        value = self._obj.get()         # obj is a MultiMotor instance or a Loop instance
        value = value.get(self._name, None)
        value = 0 if np.isclose(value, 0, atol=1e-15) else value
        status = f"{self._name}: {value:.5g}, {text}"
        self.statusUpdated.emit(status)
