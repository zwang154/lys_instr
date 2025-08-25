import numpy as np
import qtawesome as qta
import os
import json

from lys.Qt import QtWidgets, QtCore
from lys.widgets import LysSubWindow


class _MultiMotorSpecifics:
    """
    Provides feature management for a multi-axis motor, including settable, joggable, and offsettable axes.

    This class acts as a wrapper around a motor object, filtering and managing which axes can be set, jogged, or offset.
    """
    def __init__(self, motor, wait=None, axisNamesSettable=None, axisNamesJoggable=None, axisNamesOffsettable=None):
        """
        Initializes MultiMotorSpecifics with axis feature sets.

        Args:
            motor: The motor object to wrap.
            axisNamesSettable (iterable, optional): Names of axes that can be set. Defaults to all axes.
            axisNamesJoggable (iterable, optional): Names of axes that can be jogged. Defaults to all axes.
            axisNamesOffsettable (iterable, optional): Names of axes that can be offset. Defaults to all axes.
        """
        self._motor = motor
        self._allNames = self._motor.nameList
        self._wait = wait

        # Settable
        self._settableNameList = list(axisNamesSettable) if axisNamesSettable else list(self._allNames)
        self._SettableIndices = [self._allNames.index(name) for name in self._settableNameList]

        # Joggable
        self._joggableNameList = axisNamesJoggable if axisNamesJoggable is not None else self._motor.nameList

        # Offsettable
        self._offsettableNameList = axisNamesOffsettable if axisNamesOffsettable is not None else self._motor.nameList
        self._offsetDict = {name: 0 for name in self._offsettableNameList}

    def __getattr__(self, name):
        """
        Delegates attribute access to the underlying motor object.

        Args:
            name (str): Attribute name.

        Returns:
            Any: Attribute value from the motor object.
        """
        return getattr(self._motor, name)

    def set(self, *args, wait=None, **kwargs):
        """
        Sets target values for settable axes.

        Accepts values as a dict, sequence, or keyword arguments, and only applies to axes marked as settable.

        Args:
            *args: Values to set, as a dict, sequence, or positional arguments.
            wait (bool, optional): Whether to wait for the operation to complete.
            **kwargs: Axis-value pairs to set.

        Raises:
            ValueError: If the number of values does not match the number of settable axes.
            TypeError: If the argument type is unsupported.
        """
        if wait is None:
            wait = self._wait

        if args:
            if isinstance(args[0], dict):
                filtered = {name: value for name, value in args[0].items() if name in self._settableNameList}
                self._motor.set(filtered, wait=self._wait)
            elif isinstance(args[0], (list, tuple, np.ndarray)):
                if len(args[0]) != len(self._settableNameList):
                    raise ValueError(f"Length of values ({len(args[0])}) does not match number of Settable axes ({len(self._settableNameList)})")
                filtered = dict(zip(self._settableNameList, args[0]))
                self._motor.set(filtered, wait=self._wait)
            elif len(args) == len(self._settableNameList):
                filtered = dict(zip(self._settableNameList, args))
                self._motor.set(filtered, wait=self._wait)
            else:
                raise TypeError(f"Unsupported argument type or wrong number of values for set(): {args}")
        else:
            filtered = {name: value for name, value in kwargs.items() if name in self._settableNameList}
            self._motor.set(wait=self._wait, **filtered)
    
    def setOffset(self, *args, toCurrent=True, **kwargs):
        """
        Sets the offset for offsettable axes.

        Args:
            toCurrent (bool, optional): If True, set offsets to the current motor positions. Defaults to True.
        """
        if toCurrent:
            self._offsetDict = {name: self._motor.get()[name] for name in self._offsetDict}
        self._motor.valueChanged.emit(self._motor.get())

    def clearOffset(self):
        """
        Clears all offsets for offsettable axes and emit a valueChanged signal.
        """
        self._offsetDict = {name: 0 for name in self._offsettableNameList}
        self._motor.valueChanged.emit(self._motor.get())

    def setNamesSettable(self, settableNameList):
        """
        Sets the list of axes that are settable.

        Args:
            settableNameList (iterable): Names of settable axes.
        """
        self._settableNameList = list(settableNameList)

    def getNamesSettable(self):
        """
        Gets the list of settable axes.

        Returns:
            list: Names of settable axes.
        """
        return self._settableNameList

    def setNamesJoggable(self, joggableNameList):
        """
        Sets the list of axes that are joggable.

        Args:
            joggableNameList (iterable): Names of joggable axes.
        """
        self._joggableNameList = list(joggableNameList)
    
    def getNamesJoggable(self):
        """
        Gets the list of joggable axes.

        Returns:
            list: Names of joggable axes.
        """
        return self._joggableNameList

    def setNamesOffsettable(self, offsettableNameList):
        """
        Sets the list of axes that are offsettable.

        Args:
            offsettableNameList (iterable): Names of offsettable axes.
        """
        self._offsettableNameList = list(offsettableNameList)

    def getNamesOffsettable(self):
        """
        Gets the list of offsettable axes.

        Returns:
            list: Names of offsettable axes.
        """
        return self._offsettableNameList


class MultiMotorGUI(QtWidgets.QWidget):
    """
    GUI widget for controlling and monitoring a multi-axis motor.

    Provides controls for moving, jogging, offsetting, and saving/loading positions for multiple axes.
    """
    def __init__(self, obj, wait=None, axisNamesSettable=None, axisNamesJoggable=None, axisNamesOffsettable=None):
        """
        Initializes the MultiMotorGUI widget.

        Args:
            obj: The motor's features object to control.
            axisNamesSettable (iterable, optional): Names of axes that can be set. Defaults to all axes.
            axisNamesJoggable (iterable, optional): Names of axes that can be jogged. Defaults to all axes.
            axisNamesOffsettable (iterable, optional): Names of axes that can be offset. Defaults to all axes.
        """
        super().__init__()
        self._obj = _MultiMotorSpecifics(obj, wait=wait, axisNamesSettable=axisNamesSettable, axisNamesJoggable=axisNamesJoggable, axisNamesOffsettable=axisNamesOffsettable)
        self._obj.valueChanged.connect(self._valueChanged)
        self._obj.busyStateChanged.connect(self._busyStateChanged)
        self._obj.aliveStateChanged.connect(self._aliveStateChanged)
        
        # Load memory file
        dir = os.path.join(".lys_instr", "GUI", "MultiMotor")
        os.makedirs(dir, exist_ok=True)
        self._path = os.path.join(dir, "position_positionList.lst")

        self._savedPositions = []
        if os.path.exists(self._path):
            with open(self._path, "r") as f:
                self._savedPositions = json.load(f)
        
        # Initialize GUI layout
        self._initLayout()

    def _getNamesSettable(self):
        """
        Gets the list of settable axes from the features object.

        Returns:
            list: Names of settable axes.
        """
        if hasattr(self._obj, "getNamesSettable"):
            return self._obj.getNamesSettable()
        else:
            return self._obj.nameList

    def _getNamesJoggable(self):
        """
        Get the list of joggable axes from the features object.

        Returns:
            list: Names of joggable axes.
        """
        if hasattr(self._obj, "getNamesJoggable"):
            return self._obj.getNamesJoggable()
        else:
            return self._obj.nameList

    def _initLayout(self):
        """
        Initializes the GUI layout and widgets for the multi-motor control panel.
        """
        # self.setStyleSheet("QLineEdit {font-size: 14pt}"
        #                    "QDoubleSpinBox {font-size: 14pt}"
        #                    "QPushButton {font-size: 12pt}"
        #                    "QLabel {font-size: 12pt}")

        # Create main panel
        self._axisNames = {name: QtWidgets.QLabel(name) for name in self._obj.nameList}
        for lbl in self._axisNames.values():
            lbl.setAlignment(QtCore.Qt.AlignCenter)
        axisNameText = QtWidgets.QLabel("Axis")

        self._nowAt = {name: QtWidgets.QDoubleSpinBox() for name in self._obj.nameList}
        for dsb in self._nowAt.values():
            dsb.setRange(-np.inf, np.inf)
            dsb.setReadOnly(True)
            dsb.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
            dsb.setDecimals(3)
            dsb.setStyleSheet("background-color: #f0f0f0;")
        nowAtText = QtWidgets.QLabel("Now at")

        self._moveTo = {name: QtWidgets.QLineEdit() for name in self._getNamesSettable()}
        moveToText = QtWidgets.QLabel("Move to")

        jogText = QtWidgets.QLabel("Jog")

        self._jogNega = {name: QtWidgets.QPushButton(qta.icon("ri.arrow-left-fill"), "", clicked=self._nega) for name in self._getNamesJoggable()}
        for btn in self._jogNega.values():
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self._jogNegaReversed = {btn: name for name, btn in self._jogNega.items()}

        self._jogPosi = {name: QtWidgets.QPushButton(qta.icon("ri.arrow-right-fill"), "", clicked=self._posi) for name in self._getNamesJoggable()}
        for btn in self._jogPosi.values():
            btn.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self._jogPosiReversed = {btn: name for name, btn in self._jogPosi.items()}

        self._jogStep = {name: QtWidgets.QDoubleSpinBox() for name in self._getNamesJoggable()}
        for dsb in self._jogStep.values():
            dsb.setRange(0, np.inf)
            dsb.setDecimals(2)
        jogStepText = QtWidgets.QLabel("Step")

        self._execute = QtWidgets.QPushButton("Go", clicked=self._setMoveToValue)
        self._execute.setEnabled(True)

        self._interrupt = QtWidgets.QPushButton("Stop", clicked=self._obj.stop)
        self._interrupt.setEnabled(False)

        self._aliveIndicator = {name: QtWidgets.QLabel() for name in self._obj.nameList}
        for name, lbl in self._aliveIndicator.items():
            alive = self._obj.isAlive[name]
            icon = qta.icon("ri.checkbox-circle-fill", color="green") if alive else qta.icon("ri.close-circle-fill", color="red")
            lbl.setPixmap(icon.pixmap(24, 24))
            lbl.setAlignment(QtCore.Qt.AlignCenter)

        settings = QtWidgets.QPushButton(qta.icon("ri.settings-5-fill"), "", clicked=self._showSettings)
        settings.setToolTip("Settings")
        settings.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        settings.setIconSize(QtCore.QSize(20, 24))

        # Create collapsible panel
        self._collapsible = QtWidgets.QWidget()

        self._expandBtn = QtWidgets.QToolButton()
        self._expandBtn.setArrowType(QtCore.Qt.RightArrow)
        self._expandBtn.setCheckable(True)
        self._expandBtn.setChecked(False)
        self._expandBtn.setAutoRaise(True)
        self._expandBtn.setIconSize(QtCore.QSize(14, 14))
        self._expandBtn.toggled.connect(self._toggleMemoryTree)

        expanderLine = QtWidgets.QFrame()
        expanderLine.setFrameShape(QtWidgets.QFrame.HLine)
        expanderLine.setStyleSheet("color: lightgray;")

        collapsibleLayout = QtWidgets.QHBoxLayout(self._collapsible)
        collapsibleLayout.setContentsMargins(0, 0, 0, 0)
        collapsibleLayout.addWidget(self._expandBtn)
        collapsibleLayout.addWidget(expanderLine)
        collapsibleLayout.setStretch(1, 1)

        # Create memory panel
        self._memoryPanel = QtWidgets.QWidget()
        memoryPanelText = QtWidgets.QLabel("Memory")

        self._positionList = QtWidgets.QTreeWidget()
        self._positionList.setColumnCount(3)
        self._positionList.setHeaderLabels(["Label", "Position", "Memo"])
        self._positionList.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._positionList.itemSelectionChanged.connect(lambda: self._updateMemoryBtns(load, delete))
        self._positionList.setIndentation(0)
        self._positionList.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.SelectedClicked)
        self._positionList.itemChanged.connect(self._memoEdited)
        self._positionList.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self._positionList.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self._positionList.header().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self._positionList.setItemDelegateForColumn(0, _NoEditDelegate(self._positionList))
        self._positionList.setItemDelegateForColumn(1, _NoEditDelegate(self._positionList))

        save = QtWidgets.QPushButton("Save", clicked=self._save)
        save.setEnabled(True)
        
        load = QtWidgets.QPushButton("Load", clicked=self._load)
        load.setEnabled(False)

        delete = QtWidgets.QPushButton("Delete", clicked=self._delete)
        delete.setEnabled(False)

        # Main panel layout
        gl = QtWidgets.QGridLayout()
        gl.addWidget(axisNameText, 0, 1)
        gl.addWidget(nowAtText, 0, 2)
        gl.addWidget(moveToText, 0, 3)
        gl.addWidget(jogText, 0, 4)
        gl.addWidget(jogStepText, 0, 6)
        for i, name in enumerate(self._obj.nameList):
            gl.addWidget(self._aliveIndicator[name], 1 + i, 0, alignment=QtCore.Qt.AlignCenter)
            gl.addWidget(self._axisNames[name], 1 + i, 1)
            gl.addWidget(self._nowAt[name], 1 + i, 2)
            if name in self._getNamesSettable():
                gl.addWidget(self._moveTo[name], 1 + i, 3)
                if name in self._getNamesJoggable():
                    gl.addWidget(self._jogNega[name], 1 + i, 4)
                    gl.addWidget(self._jogPosi[name], 1 + i, 5)
                    gl.addWidget(self._jogStep[name], 1 + i, 6)
        gl.addWidget(self._interrupt, 1 + len(self._nowAt), 2)
        gl.addWidget(self._execute, 1 + len(self._nowAt), 3)
        gl.addWidget(settings, 1 + len(self._nowAt), 0, alignment=QtCore.Qt.AlignCenter)

        # Collapsible and memory panel layout
        gl.addWidget(self._collapsible, 2 + len(self._nowAt), 0, 1, 7)
        gl.addWidget(self._memoryPanel, 3 + len(self._nowAt), 0, len(self._obj.nameList), 7)

        # Main layout
        self.setLayout(gl)

        # Collapsible panel layout
        btnGroup = QtWidgets.QHBoxLayout()
        btnGroup.addWidget(save)
        btnGroup.addWidget(load)
        btnGroup.addWidget(delete)

        # Memory panel layout
        memoryPanelLayout = QtWidgets.QVBoxLayout(self._memoryPanel)
        memoryPanelLayout.setContentsMargins(0, 0, 0, 0)
        memoryPanelLayout.addWidget(memoryPanelText)
        memoryPanelLayout.addWidget(self._positionList)
        memoryPanelLayout.addLayout(btnGroup)
        self._memoryPanel.setVisible(False)

        # Show latest saved positions
        self._updateMemory()

    def _setMoveToValue(self):
        """
        Sets target positions for axes based on user input in the GUI.
        """
        current = self._obj.get()
        targetDict = {}
        for name in self._moveTo:
            text = self._moveTo[name].text()
            try:
                value = float(text)
            except ValueError:
                continue
            target = value + self._obj._offsetDict.get(name, 0)
            if not np.isnan(target) and not np.isclose(target, current[name]):
                targetDict[name] = target
        if targetDict:
            self._obj.set(**targetDict)

    def _valueChanged(self, valueList):
        """
        Updates the displayed axis positions in the GUI.

        Args:
            valueList (dict): Mapping of axis names to their new values.
        """
        for key, value in valueList.items():
            self._nowAt[key].setValue(value - self._obj._offsetDict.get(key, 0))

    def _busyStateChanged(self, busy):
        """
        Updates the GUI based on the busy state of the axes.

        Disables jog buttons, nowAt spin boxes, and moveTo line edits for axes that are busy, and enables them for axes that are idle.

        Args:
            busy (dict): Mapping of axis names to their busy state (bool).
        """
        anyBusy = bool(any(busy.values()))
        allAlive = all(self._obj.isAlive.values())
        self._execute.setEnabled(not anyBusy and allAlive)
        self._interrupt.setEnabled(anyBusy)
        for btn in self._jogNega.values():
            btn.setEnabled(not anyBusy and allAlive)
        for btn in self._jogPosi.values():
            btn.setEnabled(not anyBusy and allAlive)
        self._execute.setText("Moving" if anyBusy else "Go")

    def _aliveStateChanged(self, alive):
        """
        Updates the GUI controls based on the alive state of the axes.

        Disable jog buttons, nowAt spin box and moveTo line edits when dead and enable them when alive.

        Args:
            alive (dict): Mapping of axis names to alive state (bool).
        """
        busy = self._obj.isBusy
        anyBusy = any(busy.values())
        allAlive = all(alive.values())
        self._execute.setEnabled(not anyBusy and allAlive)
        self._interrupt.setEnabled(anyBusy)
        for name in alive:
            axisAlive = alive[name]
            self._nowAt[name].setEnabled(axisAlive)
            if name in self._getNamesSettable():
                self._moveTo[name].setEnabled(not busy[name] and axisAlive)
            if name in self._getNamesJoggable():
                self._jogNega[name].setEnabled(not busy[name] and axisAlive)
                self._jogPosi[name].setEnabled(not busy[name] and axisAlive)
            icon = qta.icon("ri.checkbox-circle-fill", color="green") if axisAlive else qta.icon("ri.close-circle-fill", color="red")
            self._aliveIndicator[name].setPixmap(icon.pixmap(24, 24))

    def _nega(self):
        """
        Handles negative jog button press for an axis.
        """
        name = self._jogNegaReversed.get(self.sender())
        if name is None:
            return
        target = self._obj.get()[name] - self._jogStep[name].value()
        self._obj.set(**{name: target})
        self._moveTo[name].setText(f"{target - self._obj._offsetDict[name]:.3f}")

    def _posi(self):
        """
        Handles positive jog button press for an axis.
        """
        name = self._jogPosiReversed.get(self.sender())
        if name is None:
            return
        target = self._obj.get()[name] + self._jogStep[name].value()
        self._obj.set(**{name: target})
        self._moveTo[name].setText(f"{target - self._obj._offsetDict[name]:.3f}")

    def _toggleMemoryTree(self, checked):
        """
        Shows or hides the memory panel in the GUI.

        Args:
            checked (bool): Whether the memory panel should be visible.
        """
        self._memoryPanel.setVisible(checked)
        self._expandBtn.setArrowType(QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow)
        self.adjustSize()

    def _save(self):
        """
        Saves the current axis positions to the memory file.
        """
        labels = {item["label"] for item in self._savedPositions}
        i = 1
        while f"{i}" in labels:
            i += 1
        newlabel = f"{i}"
        newPosition = [self._obj.get()[name] for name in self._obj.nameList]
        newMemo = ""
        self._savedPositions.append({"label": newlabel, "position": newPosition, "memo": newMemo})
        with open(self._path, "w") as f:
            json.dump(self._savedPositions, f)
        self._updateMemory()

    def _load(self):
        """
        Loads a selected saved axis position item from the memory file and set the axes accordingly.
        """
        selections = self._positionList.selectedItems()
        if not selections:
            return
        selectedlabel = selections[0].text(0)
        itemDict = next(item for item in self._savedPositions if item["label"] == selectedlabel)
        loadedValues = itemDict["position"]
        settableNames = self._getNamesSettable()
        valueDict = {name: loadedValues[self._obj.nameList.index(name)] for name in settableNames}
        self._obj.set(**valueDict)

    def _delete(self):
        """
        Deletes selected saved positions from the memory file.
        """
        selectedlabels = {i.text(0) for i in self._positionList.selectedItems()}
        self._savedPositions = [item for item in self._savedPositions if item["label"] not in selectedlabels]
        with open(self._path, "w") as f:
            json.dump(self._savedPositions, f)
        self._updateMemory()

    def _updateMemory(self):
        """
        Updates the memory panel with the latest saved positions.
        """
        self._positionList.clear()
        for itemDict in self._savedPositions:
            label = itemDict["label"]
            position = itemDict["position"]
            memo = itemDict["memo"]
            displayedPosition = ", ".join(f"{v:.3f}" for v in position)
            item = QtWidgets.QTreeWidgetItem([label, displayedPosition, memo])

            # Protect columns 0 and 1 from editing
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self._positionList.addTopLevelItem(item)

        for col in range(self._positionList.columnCount()):
            self._positionList.resizeColumnToContents(col)

    def _memoEdited(self, item, column):
        """
        Handles edits to the memo field in the memory panel.

        Args:
            item (QTreeWidgetItem): The edited item.
            column (int): The column index that was edited.
        """
        if column == 2:  # The memo column
            label = item.text(0)
            memo = item.text(2)
            for idx, pos in enumerate(self._savedPositions):
                if pos["label"] == label:
                    self._savedPositions[idx]["memo"] = memo
                    with open(self._path, "w") as f:
                        json.dump(self._savedPositions, f)
                    break

    def _updateMemoryBtns(self, loadBtn, deleteBtn):
        """
        Enables or disables memory panel buttons based on selection.

        Args:
            loadBtn (QPushButton): The load button.
            deleteBtn (QPushButton): The delete button.
        """
        selected = len(self._positionList.selectedItems()) > 0
        loadBtn.setEnabled(selected)
        deleteBtn.setEnabled(selected)

    # def _showSettings(self):
    #     """
    #     Opens the settings dialog for the device.
    #     """
    #     dialog = self.settingsWidget(parent=self)
    #     if hasattr(dialog, "offsetChanged"):
    #         dialog.offsetChanged.connect(self._clearMoveToFields)
    #     dialog.open()

    def _showSettings(self):
        """
        Opens the settings window for the device as a LysSubWindow.
        """
        panel = SettingsPanel(self._obj, parent=self)
        settingsWindow = LysSubWindow()
        settingsWindow.setWidget(panel)
        settingsWindow.setWindowTitle("Motor Settings")
        if hasattr(panel, "offsetChanged"):
            panel.offsetChanged.connect(self._clearMoveToFields)
        settingsWindow.adjustSize()
        settingsWindow.show()

    def _clearMoveToFields(self):
        """
        Clears all move-to input fields in the GUI.
        """
        for le in self._moveTo.values():
            le.clear()

    # def settingsWidget(self, parent=None):
    #     """
    #     Returns a settings dialog for the device.

    #     Args:
    #         parent (QWidget, optional): Parent widget for the dialog.

    #     Returns:
    #         QDialog: The settings dialog for the device.
    #     """
    #     return _settingsDialog(self._obj, parent)


class _NoEditDelegate(QtWidgets.QStyledItemDelegate):
    """
    Delegate to prevent editing of certain columns in a QTreeWidget.
    """
    def createEditor(self, parent, option, index):
        """
        Prevents editing by always returning None.

        Returns:
            None
        """
        return None


class SettingsPanel(QtWidgets.QDialog):
    """
    Settings panel for a multi-axis motor device.

    Allows viewing and toggling the alive/dead status and managing offsets for each axis.
    """
    offsetChanged = QtCore.pyqtSignal()

    def __init__(self, obj, parent=None):
        super().__init__(parent)
        self._obj = obj
        self._obj.aliveStateChanged.connect(self._updateAliveState)
        self._initLayout()

    def _initLayout(self):
        """
        Creates and initializes all GUI components of the settings dialog, and connects signals to their respective slots.
        """
        # Create alive panel
        aliveLayout = QtWidgets.QGridLayout()
        self._switch = {name: QtWidgets.QPushButton("Change", clicked=lambda checked, n=name: self._toggleAlive(n)) for name in self._obj.nameList}
        self._aliveLineEdit = {name: QtWidgets.QLineEdit("Alive") for name in self._obj.nameList}
        for le in self._aliveLineEdit.values():
            le.setAlignment(QtCore.Qt.AlignCenter)
        for i, name in enumerate(self._obj.nameList):
            aliveLayout.addWidget(self._aliveLineEdit[name], i, 0, alignment=QtCore.Qt.AlignCenter)
            aliveLayout.addWidget(self._switch[name], i, 1, alignment=QtCore.Qt.AlignCenter)

        # Create offset panel        
        if hasattr(self._obj, "_offsetDict"):
            line = QtWidgets.QFrame()
            line.setFrameShape(QtWidgets.QFrame.HLine)
            line.setStyleSheet("color: lightgray;")

            offsetLayout = QtWidgets.QGridLayout()

            self._offsetBtns = {name: QtWidgets.QPushButton("Offset", clicked=lambda checked, n=name: self._offsetAxis(n)) for name in self._obj._offsetDict}
            self._unsetBtns = {name: QtWidgets.QPushButton("Unset", clicked=lambda checked, n=name: self._unsetAxis(n)) for name in self._obj._offsetDict}
            self._offsetLbls = {name: QtWidgets.QLabel(name) for name in self._obj._offsetDict}
            self._offsetEdits = {name: QtWidgets.QDoubleSpinBox() for name in self._obj._offsetDict}

            for name in self._obj._offsetDict:
                self._offsetLbls[name].setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
                self._offsetEdits[name].setRange(-np.inf, np.inf)
                self._offsetEdits[name].setReadOnly(True)
                self._offsetEdits[name].setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
                self._offsetEdits[name].setDecimals(3)
                self._offsetEdits[name].setValue(self._obj._offsetDict[name])
                self._offsetEdits[name].setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
                self._unsetBtns[name].setEnabled(False)

            for i, name in enumerate(self._obj._offsetDict):
                offsetLayout.addWidget(self._offsetLbls[name], i, 0)
                offsetLayout.addWidget(self._offsetEdits[name], i, 1)
                offsetLayout.addWidget(self._offsetBtns[name], i, 2)
                offsetLayout.addWidget(self._unsetBtns[name], i, 3)

        # Combine layouts
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(aliveLayout)
        mainLayout.addWidget(line)
        mainLayout.addLayout(offsetLayout)    
        self.setLayout(mainLayout)

        # Initialize alive state  
        self._updateAliveState()

    def _offsetAxis(self, name):
        """
        Sets the offset for a specific axis to its current value.

        Args:
            name (str): The axis name.
        """
        self._unsetBtns[name].setEnabled(True)
        self._obj._offsetDict[name] = self._obj.get()[name]
        self._offsetEdits[name].setValue(self._obj._offsetDict[name])
        self.offsetChanged.emit()
        self._obj.valueChanged.emit(self._obj.get())

    def _unsetAxis(self, name):
        """
        Clears the offset for a specific axis.

        Args:
            name (str): The axis name.
        """
        self._unsetBtns[name].setEnabled(False)
        self._obj._offsetDict[name] = 0
        self._offsetEdits[name].setValue(0)
        self.offsetChanged.emit()
        self._obj.valueChanged.emit(self._obj.get())

    def _toggleAlive(self, name):
        """
        Toggles the alive/dead state of the specified axis and emit the corresponding signal.

        Args:
            name (str): The axis name.
        """
        self._obj._error[self._obj.nameList.index(name)] = not self._obj._error[self._obj.nameList.index(name)]
        self._obj.valueChanged.emit(self._obj.get())
        self._obj.aliveStateChanged.emit({name: self._obj._info[name].alive})
        
    def _updateAliveState(self):
        """
        Updates the displayed alive/dead status for each axis in the dialog.
        """
        for idx, name in enumerate(self._obj.nameList):
            if self._obj.isAlive[name]:
                self._aliveLineEdit[name].setText("Alive")
                self._aliveLineEdit[name].setStyleSheet("background-color: #adff2f; color: #000000")
            else:
                self._aliveLineEdit[name].setText("Dead")
                self._aliveLineEdit[name].setStyleSheet("background-color: #ff0000; color: #ffffff")



# class _settingsDialog(QtWidgets.QDialog):
#     """
#     Settings dialog for a multi-axis motor device.

#     Allows viewing and toggling the alive/dead status and managing offsets for each axis.
#     """
#     offsetChanged = QtCore.pyqtSignal()

#     def __init__(self, obj, parent):
#         """
#         Initializes the settings dialog.

#         Args:
#             obj: The motor object whose settings are being managed.
#             parent (QWidget): The parent widget for this dialog.
#         """
#         super().__init__(parent=parent)
#         self.setWindowTitle("Settings")
#         self._obj = obj
#         self._obj.aliveStateChanged.connect(self._updateAliveState)
#         self._initLayout()

#     def _initLayout(self):
#         """
#         Creates and initializes all GUI components of the settings dialog, and connects signals to their respective slots.
#         """
#         # self.setStyleSheet("QLineEdit {font-size: 14pt}"
#         #                    "QLineEdit {border-radius: 12px}"
#         #                    "QDoubleSpinBox {font-size: 14pt}"
#         #                    "QPushButton {font-size: 12pt}"
#         #                    "QLabel {font-size: 12pt}")
        
#         # Create alive panel
#         aliveLayout = QtWidgets.QGridLayout()
#         self._switch = {name: QtWidgets.QPushButton("Change", clicked=lambda checked, n=name: self._toggleAlive(n)) for name in self._obj.nameList}
#         self._aliveLineEdit = {name: QtWidgets.QLineEdit("Alive") for name in self._obj.nameList}
#         for le in self._aliveLineEdit.values():
#             le.setAlignment(QtCore.Qt.AlignCenter)
#         for i, name in enumerate(self._obj.nameList):
#             aliveLayout.addWidget(self._aliveLineEdit[name], i, 0, alignment=QtCore.Qt.AlignCenter)
#             aliveLayout.addWidget(self._switch[name], i, 1, alignment=QtCore.Qt.AlignCenter)

#         # Create offset panel        
#         if hasattr(self._obj, "_offsetDict"):
#             line = QtWidgets.QFrame()
#             line.setFrameShape(QtWidgets.QFrame.HLine)
#             line.setStyleSheet("color: lightgray;")

#             offsetLayout = QtWidgets.QGridLayout()

#             self._offsetBtns = {name: QtWidgets.QPushButton("Offset", clicked=lambda checked, n=name: self._offsetAxis(n)) for name in self._obj._offsetDict}
#             self._unsetBtns = {name: QtWidgets.QPushButton("Unset", clicked=lambda checked, n=name: self._unsetAxis(n)) for name in self._obj._offsetDict}
#             self._offsetLbls = {name: QtWidgets.QLabel(name) for name in self._obj._offsetDict}
#             self._offsetEdits = {name: QtWidgets.QDoubleSpinBox() for name in self._obj._offsetDict}

#             for name in self._obj._offsetDict:
#                 self._offsetLbls[name].setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
#                 self._offsetEdits[name].setRange(-np.inf, np.inf)
#                 self._offsetEdits[name].setReadOnly(True)
#                 self._offsetEdits[name].setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
#                 self._offsetEdits[name].setDecimals(3)
#                 self._offsetEdits[name].setValue(self._obj._offsetDict[name])
#                 self._offsetEdits[name].setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
#                 self._unsetBtns[name].setEnabled(False)

#             for i, name in enumerate(self._obj._offsetDict):
#                 offsetLayout.addWidget(self._offsetLbls[name], i, 0)
#                 offsetLayout.addWidget(self._offsetEdits[name], i, 1)
#                 offsetLayout.addWidget(self._offsetBtns[name], i, 2)
#                 offsetLayout.addWidget(self._unsetBtns[name], i, 3)

#         # Combine layouts
#         mainLayout = QtWidgets.QVBoxLayout()
#         mainLayout.addLayout(aliveLayout)
#         mainLayout.addWidget(line)
#         mainLayout.addLayout(offsetLayout)    
#         self.setLayout(mainLayout)

#         # Initialize alive state  
#         self._updateAliveState()

#     def _offsetAxis(self, name):
#         """
#         Sets the offset for a specific axis to its current value.

#         Args:
#             name (str): The axis name.
#         """
#         self._unsetBtns[name].setEnabled(True)
#         self._obj._offsetDict[name] = self._obj.get()[name]
#         self._offsetEdits[name].setValue(self._obj._offsetDict[name])
#         self.offsetChanged.emit()
#         self._obj.valueChanged.emit(self._obj.get())

#     def _unsetAxis(self, name):
#         """
#         Clears the offset for a specific axis.

#         Args:
#             name (str): The axis name.
#         """
#         self._unsetBtns[name].setEnabled(False)
#         self._obj._offsetDict[name] = 0
#         self._offsetEdits[name].setValue(0)
#         self.offsetChanged.emit()
#         self._obj.valueChanged.emit(self._obj.get())

#     def _toggleAlive(self, name):
#         """
#         Toggles the alive/dead state of the specified axis and emit the corresponding signal.

#         Args:
#             name (str): The axis name.
#         """
#         self._obj._error[self._obj.nameList.index(name)] = not self._obj._error[self._obj.nameList.index(name)]
#         self._obj.valueChanged.emit(self._obj.get())
#         self._obj.aliveStateChanged.emit({name: self._obj._info[name].alive})
        
#     def _updateAliveState(self):
#         """
#         Updates the displayed alive/dead status for each axis in the dialog.
#         """
#         for idx, name in enumerate(self._obj.nameList):
#             if self._obj.isAlive[name]:
#                 self._aliveLineEdit[name].setText("Alive")
#                 self._aliveLineEdit[name].setStyleSheet("background-color: #adff2f; color: #000000")
#             else:
#                 self._aliveLineEdit[name].setText("Dead")
#                 self._aliveLineEdit[name].setStyleSheet("background-color: #ff0000; color: #ffffff")





# To Test the GUI run in the src\python: python -m lys_instr.gui.MultiMotorGUI
if __name__ == "__main__":
    import sys
    from fstem.lys_instr.dummy.MultiMotor import MultiMotorDummy
    from lys.Qt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    motor = MultiMotorDummy("y", "z", "α", "x", "β", "γ")
    gui = MultiMotorGUI(motor,
                        wait=False,
                        axisNamesSettable=("z", "α", "y"),
                        axisNamesJoggable=("z"),
                        axisNamesOffsettable=("y", "z"))
    gui.show()
    sys.exit(app.exec_())
