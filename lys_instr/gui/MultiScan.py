import os
import numpy as np
from lys.Qt import QtWidgets, QtCore, QtGui


class _MotorScanRow(QtWidgets.QWidget):
    """
    Motor-scan row widget.

    Widget for selecting and configuring a scan range for a motor scanner.
    Supports linear ranges and free-expression ranges configured via the GUI.
    """

    def __init__(self, title, motorScanners):
        """
        Create the motor-scan row.

        Args:
            title (str): Row title shown in the GUI.
            motorScanners (dict[str, MultiMotorInterface | _Loop]): Motor scanner object (mapping from axis name to respective motor, or mapping from "loop" to the loop dummy).
        """
        super().__init__()
        self._motorScanners = motorScanners
        self._initLayout(title, motorScanners.keys())
        self._scanMode.currentTextChanged.connect(self._scanModeChanged)

    def _initLayout(self, title, scannerNames):
        """
        Create and arrange widgets for the row.

        Args:
            title (str): Row title shown in the GUI.
            scannerNames (Iterable[str]): Names of available motor scanners to populate the axis combobox.
        """
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
        """
        Enable or disable controls when the axis selection changes.

        Args:
            text (str): Newly selected axis name or 'loop' for the loop dummy.
        """
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
        """
        Show or hide widgets according to the selected scan mode.

        Args:
            text (str): Newly selected scan mode (either "Linear" or "Free").
        """
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
        """
        Scanner corresponding to the currently selected axis.

        Returns:
            object: Scanner object for the selected axis.
        """
        return self._motorScanners[self.scanName]

    @property
    def scanName(self):
        """
        Currently selected scan axis name.

        Returns:
            str: Name of the currently selected scan axis.
        """
        return self._scanAxis.currentText()

    @property
    def scanRange(self):
        """
        List of values that this row will iterate over when executed.

        Returns:
            list[float | str]: Sequence of numeric values (Linear mode) or expression strings (Free mode).
        """
        if self._scanMode.currentText() == "Linear":
            values = [self._from.value() + i * self._step.value() for i in range(self._numSteps.value())]
        elif self._scanMode.currentText() == "Free":
            values = eval(self._freeExpr.text())
        return values
    
    @property
    def scanIndex(self):
        """
        Index of the nearest value in the scan range.

        Returns:
            int: Index of the value in ``scanRange`` closest to the current scanner reading (motor-axis value).
        """
        value = self.scanObj.get()[self.scanName]
        return np.argmin(abs(np.array(self.scanRange) - value))

    def setIndex(self, index):
        """
        Set the index label for this scan row.

        Args:
            index (int): Index for this scan row.
        """
        self._title.setText("Scan " + str(index))
    
    def save(self):
        """
        Return a mapping representing this scan row for saving.

        Returns:
            dict[str, object]: Mapping with keys 'type', 'name', 'mode' and 'range'.
        """
        mode = self._scanMode.currentText()
        if mode == "Linear":
            r = (self._from.value(), self._step.value(), self._numSteps.value())
        else:
            r = self._freeExpr.text()
        return {"type": "motorScan", "name": self._scanAxis.currentText(), "mode": mode, "range": r}
    
    def load(self, d):
        """
        Load a saved row configuration into the row.

        Args:
            d (dict[str, object]): Mapping produced by ``save()``.
        """
        self._scanAxis.setCurrentText(d["name"])
        mode =d["mode"]
        self._scanMode.setCurrentText(mode)
        if mode == "Linear":
            values = d["range"]
            self._from.setValue(values[0])
            self._step.setValue(values[1])
            self._numSteps.setValue(values[2])


class _SwitchScanRow(QtWidgets.QWidget):
    """
    Switch-scan row widget.

    Widget for selecting and configuring a switch scan over a set of discrete labels.
    Supports iteration over available labels or a user-provided free list.
    """

    def __init__(self, title, switchScanners):
        """
        Create the switch-scan row.

        Args:
            title (str): Row title shown in the GUI.
            switchScanners (dict[str, MultiSwitchInterface]): Switch scanner object (mapping from axis name to respective switch).
        """
        super().__init__()
        self._switchScanners = switchScanners
        self._initLayout(title, switchScanners.keys())

    def _initLayout(self, title, scannerNames):
        """
        Create widgets for the switch-scan row.

        Args:
            title (str): Row title shown in the GUI.
            scannerNames (Iterable[str]): Names of available switch scanners to populate the axis combobox.
        """
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
        """
        Show or hide widgets according to the selected scan mode.

        Args:
            text (str): Newly selected scan mode (either 'Iteration' or 'Free').
        """
        self._freeExpr.setEnabled(text!="Iteration")
        if text == "Iteration" and len(self._freeExpr.text()) == 0:
            sw = self._switchScanners[self._scanAxis.currentText()]
            self._freeExpr.setText(", ".join(sw.labelNames))

    @property
    def scanName(self):
        """
        Currently selected scan axis name.

        Returns:
            str: Name of the currently selected scan axis.
        """
        return self._scanAxis.currentText()

    @property
    def scanObj(self):
        """
        Scanner corresponding to the currently selected axis.

        Returns:
            object: Scanner object for the selected axis.
        """
        return self._switchScanners[self.scanName]

    @property
    def scanRange(self):
        """
        List of labels that this row will iterate over when executed.

        Returns:
            list[str]: Sequence of label strings (Iteration mode) or expression strings (Free mode).
        """
        if self._scanMode.currentText() == "Iteration":
            sw = self._switchScanners[self._scanAxis.currentText()]
            values = sw.labelNames
        elif self._scanMode.currentText() == "Free":
            values = self._freeExpr.text().replace(" ", "").split(",")
        return values

    @property
    def scanIndex(self):
        """
        Index of the current switch state within the scan range.

        Returns:
            int: Index of the value in ``scanRange`` equal to the current scanner reading (switch-axis label).
        """
        value = self.scanObj.get()[self.scanName]
        return self.scanRange.index(value)

    def setIndex(self, index):
        """
        Set the index label for this scan row.

        Args:
            index (int): Index for this scan row.
        """
        self._title.setText("Scan " + str(index))
    
    def save(self):
        """
        Return a mapping representing this scan row for saving.

        Returns:
            dict[str, object]: Mapping with keys 'type', 'name', 'mode' and 'range'.
        """
        return {"type": "switchScan", "name": self._scanAxis.currentText(), "mode": self._scanMode.currentText(), "range": self._freeExpr.text()}
    
    def load(self, d):
        """
        Load a saved row configuration into the row.

        Args:
            d (dict[str, object]): Mapping produced by ``save()``.
        """
        self._scanAxis.setCurrentText(d["name"])
        self._scanMode.setCurrentText(d["mode"])
        self._freeExpr.setText(d["range"])


class _ScanList(QtWidgets.QListWidget):
    """
    List widget for scan rows.

    Holds a sequence of motor and switch scan-row widgets and provides operations to add, remove, reorder, copy/paste, and save/load the configured scan list.
    """
    _path = ".lys/instr/scanlist.dic"
    _savePath = ".lys/instr/scanSaveList.dic"

    def __init__(self, motorScanners, switchScanners):
        """
        List widget holding a sequence of scan rows (either motor-scan or switch-scan).

        Args:
            motorScanners (dict[str, MultiMotorInterface | _Loop]): Motor scanner object (mapping from axis name to respective motor, or mapping from "loop" to the loop dummy).
            switchScanners (dict[str, MultiSwitchInterface]): Switch scanner object (mapping from axis name to the respective switch).
        """
        super().__init__()
        self._motorScanners = motorScanners
        self._switchScanners = switchScanners
        self._scans = []
        self.customContextMenuRequested.connect(self._buildMenu)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        if os.path.exists(self._savePath):
            with open(self._savePath, "r") as f:
                d = eval(f.read())
            self.load(d)

    def _buildMenu(self):
        """
        Build and show the context menu for list operations.
        """
        menu = QtWidgets.QMenu()

        if self._motorScanners and len(self._motorScanners) > 0:
            addMotor = QtWidgets.QAction('Add motor scan', triggered=lambda: self._add(type="motorScan"))
            menu.addAction(addMotor)

        if self._switchScanners and len(self._switchScanners) > 0:
            addSwitch = QtWidgets.QAction('Add switch scan', triggered=lambda: self._add(type="switchScan"))
            menu.addAction(addSwitch)

        if len(self.selectedItems()) > 0:
            up = QtWidgets.QAction('Move up', triggered=lambda: self._move(-1))
            down = QtWidgets.QAction('Move down', triggered=lambda: self._move(1))
            del_ = QtWidgets.QAction('Remove', triggered=lambda: self._del())
            menu.addSeparator()
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

    def _add(self, index=None, data=None, type="motorScan"):
        """
        Insert a new scan row into the list.

        Args:
            index (int | None): Insertion index; append when ``None``.
            data (dict | None): Optional row mapping produced by a row's ``save()`` to load into the new row.
            type (str): Scan row type, either "motorScan" or "switchScan".
        """
        if index == None:
            index = len(self._scans)
        if type == "motorScan":
            scan = _MotorScanRow("Scan" + str(len(self._scans)+1), self._motorScanners)
        else:
            scan = _SwitchScanRow("Scan" + str(len(self._scans)+1), self._switchScanners)
        if data is not None:
            scan.load(data)
        self._scans.insert(index, scan)

        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(scan.sizeHint())
        self.insertItem(index, item)        
        self.setItemWidget(item, scan)
        self._refresh()

    def _del(self, index=None):
        """
        Remove a scan row from the list at the given index or the selected item.

        Args:
            index (int | None): Index to remove; if ``None``, remove the current selection.
        """
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
        """
        Move the selected scan up or down by one position.

        Args:
            direction (int): -1 to move up, +1 to move down.
        """
        index = self.row(self.selectedItems()[0])
        item = self._scans[index]
        self._del(index)
        saved = item.save()
        self._add(index+direction, saved, type=saved["type"])
        self._refresh()

    def _clear(self):
        """
        Remove all scan rows from the list.
        """
        while len(self._scans) > 0:
            self._del(0)
        self._refresh()

    def _copy(self):
        """
        Copy the current scan list to the temporary path for later pasting.
        """
        d = self.save()
        with open(self._path, "w") as f:
            f.write(str(d))
    
    def _paste(self):
        """
        Paste a previously copied scan list from the temporary path.
        """
        with open(self._path, "r") as f:
            d = eval(f.read())
        self.load(d)

    def _refresh(self):
        """
        Refresh the list widgets and save the current scan list to disk.
        """
        for i, scan in enumerate(self._scans):
            scan.setIndex(i+1)
        os.makedirs(os.path.dirname(self._savePath),exist_ok=True)
        with open(self._savePath, "w") as f:
            f.write(str(self.save()))

    def __iter__(self):
        return self._scans.__iter__()
    
    def __len__(self):
        return len(self._scans)
    
    def __getitem__(self, index):
        return self._scans[index]
    
    def save(self):
        """
        Return a mapping representing the current scan list for saving.

        Returns:
            dict[str, dict[str, object]]: Mapping where keys are 'Scan1', 'Scan2', ... and values are the per-row mappings produced by each row's ``save()``.
        """
        return {"Scan" + str(i+1): scan.save() for i, scan in enumerate(self._scans)}
    
    def load(self, d):
        """
        Load a saved scan-list mapping into the widget.

        Args:
            d (dict[str, dict[str, object]]): Mapping produced by ``save()`` where keys are 'Scan1', 'Scan2', ... and values are the per-row mappings produced by each row's ``save()``.
        """
        self._clear()
        i = 0
        while "Scan" + str(i+1) in d:
            self._add(i, d["Scan" + str(i+1)], type=d["Scan" + str(i+1)]["type"])
            i += 1


class _FileNameBox(QtWidgets.QGroupBox):
    """
    File name configuration widget.

    Provides a GUI for composing default filenames for scan runs.
    """

    def __init__(self, scans):
        """
        Create the file name configuration widget.

        Args:
            scans (Iterable[object]): Iterable of scan row objects used to compose default file names.
        """
        super().__init__("Filename")
        self.__initLayout()
        self._scans = scans

    def __initLayout(self):
        """
        Create file name widgets and helper labels.
        """
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
        """
        Update the file name field when the default toggle changes.

        Enable or disable the filename edit. 
        When the default toggle is checked, compose a default filename by joining each scan's ``scanName_[index]`` (from last to first) and set it in the line edit.
        """
        self._name.setEnabled(not self._check.isChecked())
        if self._check.isChecked():
            strings = [self._scans[i].scanName+"_["+str(i+1)+"]" for i in reversed(range(len(self._scans)))]              
            self._name.setText("/".join(strings))

    @property
    def text(self):
        """
        Return the current file name shown in the widget.

        Returns:
            str: Current file name.
        """
        return self._name.text()


class ScanWidget(QtWidgets.QWidget):
    """
    Scan configuration and execution panel.

    Provides a list-based GUI for composing a sequence of motor and switch scans, configuring detector/process settings, and starting/stopping scan execution.
    """

    def __init__(self, storage, motors, switches, detectors):
        """
        Initialize the Scan widget.

        Args:
            storage (DataStorage): The data storage object.
            motors (Iterable[MultiMotorInterface]): Motor controllers available for scanning.
            switches (Iterable[MultiSwitchInterface]): Switch controllers available for scanning.
            detectors (dict): Mapping of detector names to respective detector objects.
        """
        super().__init__()
        self._storage = storage
        self._motorScanners = self._initMotorScanners(motors)
        self._switchScanners = self._initSwitchScanners(switches)
        self._detectors = detectors
        self._initLayout(self._motorScanners, self._switchScanners, self._detectors)

    def _initMotorScanners(self, motors):
        """
        Create the mapping of scanner names to scanner objects (including a dummy loop).

        Returns:
            dict[str, object]: Mapping of axis name to scanner object (includes a "loop" dummy).
        """
        scanners = {"loop": _Loop()}
        for motor in motors:
            scanners.update({axis: motor for axis in motor.nameList})
        return scanners

    def _initSwitchScanners(self, switches):
        """
        Create the mapping of switch axis names to switch objects.

        Returns:
            dict[str, object]: Mapping of switch axis name to switch controller object.
        """
        scanners = {}
        for sw in switches:
            scanners.update({axis: sw for axis in sw.nameList})
        return scanners

    def _initLayout(self, motorScanners, switchScanners, process):
        """
        Construct the scan list GUI and control buttons.

        Args:
            motorScanners (dict[str, object]): Mapping of motor-axis name to motor objects.
            switchScanners (dict[str, object]): Mapping of switch-axis name to switch objects.
            process (dict): Detector/process mapping passed to the detector configuration box.
        """
        label = QtWidgets.QLabel("List of parameters (right click to edit)")

        self._list = _ScanList(motorScanners, switchScanners)
        self._nameBox = _FileNameBox(self._list)

        processBox = self.__detectorBox(process)

        self._startBtn = QtWidgets.QPushButton("Start", clicked=self._start)
        self._stopBtn = QtWidgets.QPushButton("Stop", clicked=self._stop)
        self._stopBtn.setEnabled(False)

        btnsLayout = QtWidgets.QHBoxLayout()
        btnsLayout.addWidget(self._startBtn)
        btnsLayout.addWidget(self._stopBtn)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(self._list)
        layout.addWidget(processBox)
        layout.addWidget(self._nameBox)
        layout.addLayout(btnsLayout)
        layout.addStretch()

        self.setLayout(layout)
    
    def __detectorBox(self, detectors):
        """
        Create detector selection and exposure controls.

        Args:
            detectors (dict): Mapping of detector names to detector objects.

        Returns:
            QtWidgets.QGroupBox: Group box containing detector selection and exposure controls.
        """
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
        """
        Start the configured scan run.

        Builds the nested process chain from the configured scan list and starts the executor thread.
        """
        process = _DetectorProcess(self._detectors[self._detectorsBox.currentText()], self._exposure.value())
        for s in self._list:
            process = _ScanProcess(s.scanName, s.scanObj, s.scanRange, process)
        process.beforeAcquisition.connect(self._updateName)

        self._storage.numbered = False
        self._storage.enabled = True
        self._storage.tagRequest.connect(self._setScanNames)
        self._name = self._nameBox.text

        self._loopCounts = {i: [0, 0] for i, _ in enumerate(self._list) if self._list[i].scanName == "loop"}

        self._thread = _Executor(process)
        self._thread.finished.connect(self._scanFinished)

        self._startBtn.setEnabled(False)
        self._stopBtn.setEnabled(True)
        self._oldName = self._storage.name
        self._thread.start()

    def _scanFinished(self):
        """
        Handle scan completion and restore GUI and storage state.
        """
        self._startBtn.setEnabled(True)
        self._stopBtn.setEnabled(False)
        self._storage.name = self._oldName
        self._storage.numbered = True

        if hasattr(self, "_loopCounts"):
            del self._loopCounts

    def _updateName(self):
        """
        Update the storage filename using current scan parameter values.
        """
        name = str(self._name)
        for i, scan in enumerate(self._list):
            if scan.scanName == "loop":
                num = int(self._loopCounts[i][0])
                value = num
                index = num
                n = np.prod([len(self._list[j].scanRange) for j in range(i)])
                self._loopCounts[i][1] += 1
                self._loopCounts[i][0] += self._loopCounts[i][1]//n
                self._loopCounts[i][0] %= len(scan.scanRange)
                self._loopCounts[i][1] %= n
            else:
                value = scan.scanObj.get()[scan.scanName]
                index = scan.scanIndex
            name = name.replace("{"+str(i+1)+"}", value) if type(value) == str else name.replace("{"+str(i+1)+"}", f"{value:.5g}")
            name = name.replace("["+str(i+1)+"]", str(index))
        self._storage.name = name

    def _stop(self):
        """
        Request the running scan to stop.
        """
        self._thread.kill()

    def _setScanNames(self, scanNamesDict):
        """
        Populate the provided mapping with the current scan axis names.

        Args:
            scanNamesDict (dict): Mutable mapping that will be updated by this method. The key ``'scanNames'`` is set to a list[str] containing the current scan axis names in order.
        """
        scanNamesDict["scanNames"] = [s.scanName for s in self._list]


class _Loop(QtCore.QObject):
    """
    Dummy loop scanner.
    """

    def __init__(self, name="loop"):
        """
        Create the loop object.

        Args:
            name (str, optional): Key used in mappings for the loop value. Defaults to "loop".
        """
        super().__init__()
        self._name = name
        self._value = None

    def set(self, *args, **kwargs):
        """
        Set the loop value.

        Args:
            *args: If provided, the first positional argument is used as the loop value.
            **kwargs: If no positional args are provided, the first keyword value is used.

        Raises:
            ValueError: If neither positional nor keyword arguments are provided.
        """
        if args:
            self._value = args[0]
        elif kwargs:
            self._value = next(iter(kwargs.values()))
        else:
            raise ValueError("No value provided to _Loop.set()")

    def get(self):
        """
        Return the current loop value as a mapping.

        Returns:
            dict[str, object]: Mapping of the loop names to respective current values.
        """
        return {self._name: self._value}


class _Executor(QtCore.QThread):
    """
    Thread wrapper for executing a scan process.
    """

    def __init__(self, process):
        """
        Create a new executor for the given process.

        Args:
            process (object): Object exposing ``execute()`` and ``stop()`` used by the executor.
        """
        super().__init__()
        self.process = process

    def run(self):
        """
        Run the wrapped process's ``execute()`` in this thread.
        """
        self.process.execute()

    def kill(self):
        """
        Request the running scan process to stop.
        """
        self.process.stop()


class _DetectorProcess(QtCore.QObject):
    """
    Detector process wrapper.

    Wraps a detector and exposure value and exposes ``execute()`` and ``stop()`` used by the scan executor.
    Emits ``beforeAcquisition`` before starting acquisition.
    """

    beforeAcquisition = QtCore.pyqtSignal()

    def __init__(self, detector, exposure):
        """
        Create a detector process wrapper.

        Args:
            detector (object): Detector object to control.
            exposure (float): Exposure time to apply before acquisition.
        """
        super().__init__()
        self._detector = detector
        self._exposure = exposure

    def execute(self):        
        """
        Execute the detector process.

        Configures exposure if provided, emits ``beforeAcquisition`` and starts the detector.
        """
        if self._detector.exposure is not None:
            self._detector.exposure = self._exposure
        self.beforeAcquisition.emit()
        self._detector.startAcq(wait=True)
        
    def stop(self):
        """
        Stop the wrapped detector acquisition.
        """
        self._detector.stop()


class _ScanProcess(QtCore.QObject):
    """
    Scan process wrapper.

    Iterates a sequence of values for a single scan axis and delegates to the nested process for acquisition at each value.
    Exposes ``execute()`` and ``stop()``.
    """

    #: Signal emitted before each acquisition.
    beforeAcquisition = QtCore.pyqtSignal()

    def __init__(self, name, obj, values, process):
        """
        Create a scan process for a single axis.

        Args:
            name (str): Axis name used in ``set()`` calls.
            obj (object): Controller exposing ``set(..., wait=True)`` and ``get()``.
            values (Iterable[float | str]): Sequence of values to iterate over (elements are numeric or label strings).
            process (object): Nested process exposing ``execute()`` and ``stop()``.
        """
        super().__init__()
        self._name = name
        self._obj = obj
        self._values = values
        self._process = process
        self._process.beforeAcquisition.connect(self.beforeAcquisition.emit)
        self._shouldStop = False
        self._mutex = QtCore.QMutex()

    def execute(self):
        """
        Iterate values, set the axis value and delegate to the nested process.
        """
        for value in self._values:
            if self._shouldStop:
                return
            self._obj.set(**{self._name: value}, wait=True)
            self._process.execute()

    def stop(self):
        """
        Request the scan to stop and stop the nested process.
        """
        with QtCore.QMutexLocker(self._mutex):
            self._shouldStop = True
        self._process.stop()
