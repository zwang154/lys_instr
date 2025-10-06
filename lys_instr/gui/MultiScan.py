import numpy as np
from lys.Qt import QtWidgets, QtCore, QtGui


class _ScanRangeRow(QtWidgets.QWidget):
    def __init__(self, title, scanners):
        super().__init__()
        self._scanners = scanners
        self._initLayout(title, scanners.keys())
        self._scanMode.currentTextChanged.connect(self._scanModeChanged)

    def _initLayout(self, title, scannerNames):
        self._title = QtWidgets.QLabel(title)
        self._scanAxis = QtWidgets.QComboBox(objectName="ScanRange_scanAxis_" + title)
        self._scanAxis.addItems(scannerNames)
        self._scanAxis.currentTextChanged.connect(self._scanAxisChanged)
        self._scanMode = QtWidgets.QComboBox(objectName="ScanRange_scanMode_" + title)
        self._scanMode.addItems(["Linear", "Free"])
        self._scanMode.setEnabled(False)
        self._from = QtWidgets.QDoubleSpinBox(objectName="ScanRange_from_" + title)
        self._from.setRange(-np.inf, np.inf)
        self._from.setDecimals(4)
        self._from.setEnabled(False)
        self._step = QtWidgets.QDoubleSpinBox(objectName="ScanRange_step_" + title)
        self._step.setRange(-np.inf, np.inf)
        self._step.setDecimals(4)
        self._step.setEnabled(False)
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
        b = text not in ["loop"]
        if text == "loop":
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
    def scanObj(self):
        return self._scanners[self.scanName]

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
        return {"type": "scan", "name": self._scanAxis.currentText(), "mode": mode, "range": r}
    
    def load(self, d):
        self._scanAxis.setCurrentText(d["name"])
        mode =d["mode"]
        self._scanMode.setCurrentText(mode)
        if mode == "Linear":
            values = d["range"]
            self._from.setValue(values[0])
            self._step.setValue(values[1])
            self._numSteps.setValue(values[2])


class _ScanSwitchRow(QtWidgets.QWidget):
    def __init__(self, title, switches):
        super().__init__()
        self._switches = switches
        self._initLayout(title, switches.keys())

    def _initLayout(self, title, scannerNames):
        self._title = QtWidgets.QLabel(title)
        self._scanAxis = QtWidgets.QComboBox(objectName="ScanRange_scanAxis_" + title)
        self._scanAxis.addItems(scannerNames)
        self._scanMode = QtWidgets.QComboBox(objectName="ScanRange_scanMode_" + title)
        self._scanMode.addItems(["Iteration", "Free"])
        self._scanMode.currentTextChanged.connect(self._scanModeChanged)
        self._freeExpr = QtWidgets.QLineEdit(objectName="ScanRange_freeExpr_" + title)
        self._freeExprLabel = QtWidgets.QLabel("Expression")

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self._title, 0, 0)
        layout.addWidget(QtWidgets.QLabel("Mode"), 0, 1)
        layout.addWidget(self._freeExprLabel, 0, 2)
        layout.addWidget(self._scanAxis, 1, 0)
        layout.addWidget(self._scanMode, 1, 1)
        layout.addWidget(self._freeExpr, 1, 2)
        self.setLayout(layout)
        self._scanModeChanged("Iteration")

    def _scanModeChanged(self, text):
        self._freeExpr.setEnabled(text!="Iteration")
        if text == "Iteration" and len(self._freeExpr.text()) == 0:
            sw = self._switches[self._scanAxis.currentText()]
            self._freeExpr.setText(", ".join(sw.labelNames))

    @property
    def scanName(self):
        return self._scanAxis.currentText()

    @property
    def scanObj(self):
        return self._switches[self.scanName]

    @property
    def scanRange(self):
        if self._scanMode.currentText() == "Iteration":
            sw = self._switches[self._scanAxis.currentText()]
            values = sw.labelNames
        elif self._scanMode.currentText() == "Free":
            values = self._freeExpr.text().replace(" ", "").split(",")
        return values
    
    def setIndex(self, index):
        self._title.setText("Scan " + str(index))
    
    def save(self):
        return {"type": "switch", "name": self._scanAxis.currentText(), "mode": self._scanMode.currentText(), "range": self._freeExpr.text()}
    
    def load(self, d):
        self._scanAxis.setCurrentText(d["name"])
        self._scanMode.setCurrentText(d["mode"])
        self._freeExpr.setText(d["range"])


class _ScanList(QtWidgets.QListWidget):
    _path = ".lys/instr/scanlist.dic"
    def __init__(self, scanner, switches):
        super().__init__()
        self._scanner = scanner
        self._switches = switches
        self._scans = []
        self.customContextMenuRequested.connect(self._buildMenu)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

    def _buildMenu(self):
        menu = QtWidgets.QMenu()

        add = QtWidgets.QAction('Add new scan', triggered=lambda: self._add(type="scan"))
        switch = QtWidgets.QAction('Add new switch', triggered=lambda: self._add(type="switch"))
        menu.addAction(add)
        menu.addAction(switch)
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

    def _add(self, index=None, data=None, type="scan"):
        if index == None:
            index = len(self._scans)
        if type == "scan":
            scan=_ScanRangeRow("Scan" + str(len(self._scans)+1), self._scanner)
        else:
            scan=_ScanSwitchRow("Scan" + str(len(self._scans)+1), self._switches)
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
        saved = item.save()
        self._add(index+direction, saved, type=saved["type"])
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
            scan.setIndex(i+1)

    def __iter__(self):
        return self._scans.__iter__()
    
    def __len__(self):
        return len(self._scans)
    
    def __getitem__(self, index):
        return self._scans[index]
    
    def save(self):
        return {"Scan" + str(i+1): scan.save() for i, scan in enumerate(self._scans)}
    
    def load(self, d):
        self._clear()
        i = 0
        while "Scan" + str(i+1) in d:
            self._add(i, d["Scan" + str(i+1)], type=d["Scan" + str(i+1)]["type"])
            i += 1


class _FileNameBox(QtWidgets.QGroupBox):
    def __init__(self, scans):
        super().__init__("Filename")
        self.__initLayout()
        self._scans = scans

    def __initLayout(self):
        self._name = QtWidgets.QLineEdit(objectName="scan_filename")
        self._check = QtWidgets.QCheckBox("Default", toggled=self._toggled, objectName="scan_default")

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self._name, 0, 1)
        layout.addWidget(self._check, 0, 2)

        v = QtWidgets.QVBoxLayout()
        v.addLayout(layout)
        v.addWidget(QtWidgets.QLabel("{1}: the first scan param, {2}: the second scan param, ..."))
        v.addWidget(QtWidgets.QLabel("[1]: the first scan index, [2]: the second scan index, ..."))
        self.setLayout(v)

    def _toggled(self):
        self._name.setEnabled(not self._check.isChecked())
        if self._check.isChecked():
            strings = [self._scans[i].scanName+"_["+str(i+1)+"]" for i in reversed(range(len(self._scans)))]              
            self._name.setText("/".join(strings))

    @property
    def text(self):
        return self._name.text()


class ScanWidget(QtWidgets.QWidget):
    def __init__(self, storage, motors, switches, detectors, numScans=1):
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
        self._switches = self._initSwitches(switches)
        self._detectors = detectors
        self._numScans = numScans
        self._initLayout(self._scanners, self._switches, self._detectors)

    def _initScanners(self, motors):
        scanners = {"loop": _Loop()}        # Dummy loop as the first scanner
        for motor in motors:
            scanners.update({axis: motor for axis in motor.nameList})
        return scanners

    def _initSwitches(self, switches):
        scanners = {}        
        for sw in switches:
            scanners.update({axis: sw for axis in sw.nameList})
        return scanners

    def _initLayout(self, scanners, switches, process):
        self._statusLabel = QtWidgets.QLabel("[Status] Idle.")

        self._list = _ScanList(scanners, switches)
        self._nameBox = _FileNameBox(self._list)

        processBox = self.__detectorBox(process)

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
        layout.addWidget(self._nameBox)
        layout.addLayout(btnsLayout)
        layout.addStretch()

        self.setLayout(layout)
    
    def __detectorBox(self, detectors):
        self._detectorsBox = QtWidgets.QComboBox(objectName="ScanTab_detectors")
        self._detectorsBox.addItems(detectors.keys())

        self._exposure = QtWidgets.QDoubleSpinBox(objectName="ScanTab_exposure")
        self._exposure.setRange(0, np.inf)
        self._exposure.setDecimals(5)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel("Detectors"), 0, 0)
        layout.addWidget(self._detectorsBox, 0, 1, 1, 2)
        layout.addWidget(QtWidgets.QLabel("Exposure"), 1, 0)
        layout.addWidget(self._exposure, 1, 1, 1, 2)

        processBox = QtWidgets.QGroupBox("Process")
        processBox.setLayout(layout)
        return processBox
        
    def _start(self):
        process = _DetectorProcess(self._detectors[self._detectorsBox.currentText()], self._exposure.value())
        for s in self._list:
            process = _ScanProcess(s.scanName, s.scanObj, s.scanRange, process)
        process.beforeAcquisition.connect(self._updateName)

        self._statusLabel.setText("[Status] Starting...")
        self._storage.numbered = False
        self._storage.enabled = True
        self._storage.tagRequest.connect(self._setScanNames)
        self._name = self._nameBox.text

        self._thread = _Executor(process)
        self._thread.finished.connect(self._scanFinished)

        self._startBtn.setEnabled(False)
        self._stopBtn.setEnabled(True)
        self._oldName = self._storage.name
        self._thread.start()

    def _scanFinished(self):
        self._startBtn.setEnabled(True)
        self._stopBtn.setEnabled(False)
        self._storage.name = self._oldName
        self._storage.numbered = True
        self._statusLabel.setText("[Status] Finished.")

    def _updateName(self):
        name = str(self._name)
        for i, scan in enumerate(self._list):
            value = scan.scanObj.get()[scan.scanName]
            index = np.argmin(abs(np.array(scan.scanRange) - value))
            name = name.replace("{"+str(i+1)+"}", f"{value:.5g}")
            name = name.replace("["+str(i+1)+"]", str(index))
        self._storage.name = name

    def _stop(self):
        self._thread.kill()

    def _setScanNames(self, scanNamesDict):
        scanNamesDict["scanNames"] = [s.scanName for s in self._list]


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
    def __init__(self, process):
        super().__init__()
        self.process = process

    def run(self):
        self.process.execute()

    def kill(self):
        self.process.stop()


class _DetectorProcess(QtCore.QObject):
    beforeAcquisition = QtCore.pyqtSignal()

    def __init__(self, detector, exposure):
        super().__init__()
        self._detector = detector
        self._exposure = exposure

    def execute(self):        
        if self._detector.exposure is not None:
            self._detector.exposure = self._exposure
        self.beforeAcquisition.emit()
        self._detector.startAcq(wait=True)
        
    def stop(self):
        self._detector.stop()


class _ScanProcess(QtCore.QObject):
    beforeAcquisition = QtCore.pyqtSignal()

    def __init__(self, name, obj, values, process):
        super().__init__()
        self._name = name
        self._obj = obj
        self._values = values
        self._process = process
        self._process.beforeAcquisition.connect(self.beforeAcquisition.emit)
        self._shouldStop = False
        self._mutex = QtCore.QMutex()

    def execute(self):
        for value in self._values:
            if self._shouldStop:
                return
            self._obj.set(**{self._name: value}, wait=True)
            self._process.execute()

    def stop(self):
        with QtCore.QMutexLocker(self._mutex):
            self._shouldStop = True
        self._process.stop()
