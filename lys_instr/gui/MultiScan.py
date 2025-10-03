import numpy as np
from lys.Qt import QtWidgets, QtCore, QtGui


class _ScanRangeRow(QtWidgets.QWidget):
    def __init__(self, title, scannerNames):
        super().__init__()
        self._initLayout(title, scannerNames)
        self._scanMode.currentTextChanged.connect(self._scanModeChanged)

    def _initLayout(self, title, scannerNames):
        self._title = QtWidgets.QLabel(title)
        self._scanAxis = QtWidgets.QComboBox(objectName="ScanRange_scanAxis_" + title)
        self._scanAxis.addItems(list(scannerNames) + ["None"])
        self._scanAxis.currentTextChanged.connect(self._scanAxisChanged)
        self._scanMode = QtWidgets.QComboBox(objectName="ScanRange_scanMode_" + title)
        self._scanMode.addItems(["Linear", "Free"])
        self._from = QtWidgets.QDoubleSpinBox(objectName="ScanRange_from_" + title)
        self._from.setRange(-np.inf, np.inf)
        self._from.setDecimals(4)
        self._step = QtWidgets.QDoubleSpinBox(objectName="ScanRange_step_" + title)
        self._step.setRange(-np.inf, np.inf)
        self._step.setDecimals(4)
        self._numSteps = QtWidgets.QSpinBox(objectName="ScanRange_numSteps_" + title)
        self._numSteps.setRange(1, 100000)
        self._freeExpr = QtWidgets.QLineEdit(objectName="ScanRange_freeExpr_" + title)
        self._fromLabel = QtWidgets.QLabel("From")
        self._stepLabel = QtWidgets.QLabel("Step")
        self._numStepsLabel = QtWidgets.QLabel("Number of steps")
        self._freeExprLabel = QtWidgets.QLabel("Expression")

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self._title, 0, 0)
        layout.addWidget(QtWidgets.QLabel("Mode"), 0, 1)
        layout.addWidget(self._fromLabel, 0, 2)
        layout.addWidget(self._stepLabel, 0, 3)
        layout.addWidget(self._numStepsLabel, 0, 4)
        layout.addWidget(self._freeExprLabel, 0, 5)
        layout.addWidget(self._scanAxis, 1, 0)
        layout.addWidget(self._scanMode, 1, 1)
        layout.addWidget(self._from, 1, 2)
        layout.addWidget(self._step, 1, 3)
        layout.addWidget(self._numSteps, 1, 4)
        layout.addWidget(self._freeExpr, 1, 5)

        self._freeExpr.hide()
        self._freeExprLabel.hide()
        self.setLayout(layout)

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
    
    def setIndex(self, index):
        self._title.setText("Scan " + str(index))
    
    def save(self):
        mode = self._scanMode.currentText()
        if mode == "Linear":
            r = (self._from.value(), self._step.value(), self._numSteps.value())
        else:
            r = self._freeExpr.text()
        return {"name": self._scanAxis.currentText(), "mode": mode, "range": r}
    
    def load(self, d):
        self._scanAxis.setCurrentText(d["name"])
        mode =d["mode"]
        self._scanMode.setCurrentText(mode)
        if mode == "Linear":
            values = d["range"]
            self._from.setValue(values[0])
            self._step.setValue(values[1])
            self._numSteps.setValue(values[2])


class _ScanList(QtWidgets.QListWidget):
    _path = ".lys/instr/scanlist.dic"
    def __init__(self, scanner):
        super().__init__()
        self._scanner = scanner
        self._scans = []
        self.customContextMenuRequested.connect(self._buildMenu)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

    def _buildMenu(self):
        menu = QtWidgets.QMenu()

        add = QtWidgets.QAction('Add new scan', triggered=lambda: self._add())
        menu.addAction(add)
        if len(self.selectedItems()) > 0:
            up = QtWidgets.QAction('Move up', triggered=lambda: self._move(-1))
            down = QtWidgets.QAction('Move down', triggered=lambda: self._move(1))
            del_ = QtWidgets.QAction('Remove', triggered=lambda: self._del())
            menu.addAction(up)
            menu.addAction(down)
            menu.addAction(del_)

        cp = QtWidgets.QAction('Copy', triggered=lambda: self._copy())
        pst = QtWidgets.QAction('Paste', triggered=lambda: self._paste())
        cls = QtWidgets.QAction('Clear', triggered=lambda: self._clear())
        menu.addSeparator()
        menu.addAction(cp)
        menu.addAction(pst)
        menu.addAction(cls)
        menu.exec_(QtGui.QCursor.pos())

    def _add(self, index=None, data=None):
        if index == None:
            index = len(self._scans)
        scan=_ScanRangeRow("Scan" + str(len(self._scans)+1), self._scanner.keys())
        if data is not None:
            scan.load(data)
        self._scans.insert(index, scan)

        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(scan.sizeHint())
        self.insertItem(index, item)        
        self.setItemWidget(item, scan)
        self._refresh()

    def _del(self, index=None):
        if index is None:
            index = self.row(self.selectedItems()[0])
        self._scans.pop(index)
        item = self.item(index)
        widget = self.itemWidget(item)
        self.removeItemWidget(item)
        if widget is not None:
            widget.deleteLater()
        self.takeItem(index)
        self._refresh()

    def _move(self, direction):
        index = self.row(self.selectedItems()[0])
        item = self._scans[index]
        self._del(index)
        self._add(index+direction, item.save())
        self._refresh()

    def _clear(self):
        while len(self._scans) > 0:
            self._del(0)

    def _copy(self):
        d = self.save()
        with open(self._path, "w") as f:
            f.write(str(d))
    
    def _paste(self):
        with open(self._path, "r") as f:
            d = eval(f.read())
        self.load(d)

    def _refresh(self):
        for i, scan in enumerate(self._scans):
            scan.setIndex(i)

    def __iter__(self):
        return self._scans.__iter__()

    def save(self):
        return {"Scan" + str(i): scan.save() for i, scan in enumerate(self._scans)}
    
    def load(self, d):
        self._clear()
        i = 0
        while "Scan" + str(i) in d:
            self._add(i, d["Scan" + str(i)])
            i += 1


class ScanWidget(QtWidgets.QWidget):
    def __init__(self, storage, motors, detectors, numScans=1):
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
        self._detectors = detectors
        self._numScans = numScans
        self._initLayout(self._scanners, self._detectors)

    def _initScanners(self, motors):
        scanners = {"loop": _Loop()}        # Dummy loop as the first scanner
        for motor in motors:
            scanners.update({axis: motor for axis in motor.nameList})
        return scanners
    
    def _initLayout(self, scanners, process):
        self._statusLabel = QtWidgets.QLabel("[Status] Idle.")

        self._list = ScanList(self._scanners)

        processBox = self.__detectorBox(process, scanners)

        self._startBtn = QtWidgets.QPushButton("Start", clicked=self._start)
        self._stopBtn = QtWidgets.QPushButton("Stop", clicked=self._stop)
        self._stopBtn.setEnabled(False)

        btnsLayout = QtWidgets.QHBoxLayout()
        btnsLayout.addWidget(self._startBtn)
        btnsLayout.addWidget(self._stopBtn)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._statusLabel)
        layout.addWidget(self._list)
        layout.addWidget(processBox)
        layout.addLayout(btnsLayout)
        layout.addStretch()

        self.setLayout(layout)
    
    def __detectorBox(self, detectors, scanners):
        self._detectorsBox = QtWidgets.QComboBox(objectName="ScanTab_detectors")
        self._detectorsBox.addItems(detectors.keys())

        self._exposure = QtWidgets.QDoubleSpinBox(objectName="ScanTab_exposure")
        self._exposure.setRange(0, np.inf)
        self._exposure.setDecimals(5)

        self._combo_ref = QtWidgets.QComboBox(objectName="ScanTab_combo_ref")
        self._combo_ref.addItems(scanners.keys())
        self._combo_ref.setEnabled(False)
        self._value_ref = QtWidgets.QDoubleSpinBox(objectName="ScanTab_value_ref")
        self._value_ref.setEnabled(False)
        self._check_ref = QtWidgets.QCheckBox("Reference", objectName="ScanTab_reference")
        self._check_ref.toggled.connect(self._combo_ref.setEnabled)
        self._check_ref.toggled.connect(self._value_ref.setEnabled)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel("Detectors"), 0, 0)
        layout.addWidget(self._detectorsBox, 0, 1, 1, 2)
        layout.addWidget(QtWidgets.QLabel("Exposure"), 1, 0)
        layout.addWidget(self._exposure, 1, 1, 1, 2)
        layout.addWidget(self._check_ref, 2, 0)
        layout.addWidget(self._combo_ref, 2, 1)
        layout.addWidget(self._value_ref, 2, 2)

        processBox = QtWidgets.QGroupBox("Process")
        processBox.setLayout(layout)
        return processBox
        
    def _start(self):
        process = _DetectorProcess(self._detectors[self._detectorsBox.currentText()], self._exposure.value(), **self.__getRefInfo())
        for i, s in enumerate([s for s in self._list]):
            process = _ScanProcess(s.scanName, self._scanners[s.scanName], s.scanRange, process, addFolder=(i != 0), addName=(i == 0))
        process.statusUpdated.connect(lambda s: self._statusLabel.setText("[Scanning...] " + s))

        self._statusLabel.setText("[Status] Starting...")
        self._storage.numbered = False
        self._storage.enabled = True
        self._storage.tagRequest.connect(self._setScanNames)

        self._thread = _Executor(process, self._storage)
        self._thread.finished.connect(self._scanFinished)

        self._startBtn.setEnabled(False)
        self._stopBtn.setEnabled(True)
        self._oldFolder = self._storage.folder
        self._oldName = self._storage.name
        self._thread.start()

    def __getRefInfo(self):
        if self._check_ref.isChecked():
            ref = self._combo_ref.currentText()
            value = self._value_ref.value()
            controller = self._scanners[self._combo_ref.currentText()]
            return {"ref": ref, "value": value, "controller": controller}
        else:
            return {}

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


class _Executor(QtCore.QThread):
    def __init__(self, process, storage):
        super().__init__()
        self.process = process
        self.storage = storage

    def run(self):
        self.process.execute(self.storage)

    def kill(self):
        self.process.stop()


class _DetectorProcess(QtCore.QObject):
    statusUpdated = QtCore.pyqtSignal(str)
    quitRequested = QtCore.pyqtSignal()

    def __init__(self, detector, exposure, ref=None, controller=None, value=None):
        super().__init__()
        self._detector = detector
        self._exposure = exposure
        self._ref = ref
        self._controller = controller
        self._value = value

    def execute(self, storage):
        oldFolder = storage.folder
        storage.folder = oldFolder + "/pump"
        
        if self._detector.exposure is not None:
            self._detector.exposure = self._exposure
        self._acquire()
        if self._ref is not None:
            oldValue = self._controller.get()[self._ref]
            storage.folder = oldFolder + "/probe"
            self._controller.set(**{self._ref: self._value}, wait=True)
            self._acquire()
            self._controller.set(**{self._ref: oldValue}, wait=True)
        self.statusUpdated.emit(f"[Executing] Folder: {storage.folder} | Name: {storage.name}")
        
        storage.folder = oldFolder

    def _acquire(self):
        loop = QtCore.QEventLoop()
        self.quitRequested.connect(loop.quit)
        self._detector.busyStateChanged.connect(self._onFinished)
        self._detector.startAcq()
        loop.exec_()
        self._detector.busyStateChanged.disconnect(self._onFinished)
        self.quitRequested.disconnect(loop.quit)

    def _onFinished(self, busy):
        if not busy:
            self.quitRequested.emit()

    def stop(self):
        pass


class _ScanProcess(QtCore.QObject):
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
            self._obj.set(**{self._name: value}, wait=True)
            if self._addFolder:
                currentFolder = f"{oldFolder}/{self._name}{str(i).zfill(len(str(len(self._values))))}"
                storage.folder = currentFolder
            else:
                storage.folder = currentFolder
            if self._addName:
                storage.name = f"{oldName}_{self._name}{i}"
            self._process.execute(storage)

        storage.folder = oldFolder
        storage.name = oldName

    def stop(self):
        with QtCore.QMutexLocker(self._mutex):
            self._shouldStop = True
        self._process.stop()

    def _statusUpdated(self, text):
        values = self._obj.get()
        value = values.get(self._name, None)
        value = 0 if np.isclose(value, 0, atol=1e-15) else value
        status = f"{self._name}: {value:.5g}, {text}"
        self.statusUpdated.emit(status)