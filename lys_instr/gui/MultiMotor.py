import numpy as np
import qtawesome as qta
import os
import json

from lys.Qt import QtWidgets, QtCore
from .widgets import AliveIndicator, SettingsButton


class _MultiMotorSpecifics(QtCore.QObject):
    """
    Provides feature management for a multi-axis motor, including settable, joggable, and offsettable axes.

    This class acts as a wrapper around a motor object, filtering and managing which axes can be set, jogged, or offset.
    """
    valueChanged = QtCore.pyqtSignal(dict)

    def __init__(self, motor, axisNamesOffsettable=None):
        """
        Initializes MultiMotorSpecifics with axis feature sets.

        Args:
            motor: The motor object to wrap.
            axisNamesOffsettable (iterable, optional): Names of axes that can be offset. Defaults to all axes.
        """
        super().__init__()
        self._motor = motor
        offsettable = list(axisNamesOffsettable) if axisNamesOffsettable is not None else list(self._motor.nameList)
        self._offsetDict = {name: 0 for name in offsettable}
        self._motor.valueChanged.connect(self._valueChanged)

    def __getattr__(self, name):
        """
        Delegates attribute access to the underlying motor object.

        Args:
            name (str): Attribute name.

        Returns:
            Any: Attribute value from the motor object.
        """
        return getattr(self._motor, name)

    def set(self, **kwargs):
        """
        Sets target values for settable axes.
        """
        kwargs = {key: value + self.offset.get(key, 0) for key, value in kwargs.items()}
        self._motor.set(**kwargs)

    def get(self):
        """ Gets target values."""
        res = self._motor.get()
        return {key: value - self.offset.get(key, 0) for key, value in res.items()}

    def _valueChanged(self, res):
        self.valueChanged.emit({key: value - self.offset.get(key, 0) for key, value in res.items()})

    @property
    def offset(self):
        return self._offsetDict


class MultiMotorGUI(QtWidgets.QWidget):
    """
    GUI widget for controlling and monitoring a multi-axis motor.

    Provides controls for moving, jogging, offsetting, and saving/loading positions for multiple axes.
    """

    def __init__(self, obj, axisNamesSettable=None, axisNamesJoggable=None, axisNamesOffsettable=None):
        """
        Initializes the MultiMotorGUI widget.

        Args:
            obj: The motor's features object to control.
            axisNamesSettable (iterable, optional): Names of axes that can be set. Defaults to all axes.
            axisNamesJoggable (iterable, optional): Names of axes that can be jogged. Defaults to all axes.
            axisNamesOffsettable (iterable, optional): Names of axes that can be offset. Defaults to all axes.
        """
        super().__init__()
        self._obj = _MultiMotorSpecifics(obj, axisNamesOffsettable=axisNamesOffsettable)

        # Initialize GUI layout
        joggable = list(obj.nameList) if axisNamesJoggable is None else list(axisNamesJoggable)
        settable = list(obj.nameList) if axisNamesSettable is None else list(axisNamesSettable)

        self._initLayout(settable, joggable)
        self._obj.busyStateChanged.connect(self._busyStateChanged)
        self._obj.aliveStateChanged.connect(self._aliveStateChanged)

    def _initLayout(self, settable, joggable):
        """
        Initializes the GUI layout and widgets for the multi-motor control panel.
        """
        self._items = {name: _MotorRowLayout(self._obj, name) for name in self._obj.nameList}

        self._execute = QtWidgets.QPushButton("Go", clicked=self._setMoveToValue)
        self._execute.setEnabled(True)

        self._interrupt = QtWidgets.QPushButton("Stop", clicked=self._obj.stop)
        self._interrupt.setEnabled(False)

        # Axis controls layout
        gl = QtWidgets.QGridLayout(self)
        gl.setAlignment(QtCore.Qt.AlignTop)
        gl.addWidget(QtWidgets.QLabel("Axis"), 0, 1)
        gl.addWidget(QtWidgets.QLabel("Now at"), 0, 2)
        gl.addWidget(QtWidgets.QLabel("Move to"), 0, 3)
        gl.addWidget(QtWidgets.QLabel("Jog"), 0, 4)
        gl.addWidget(QtWidgets.QLabel("Step"), 0, 6)

        for i, (key, item) in enumerate(self._items.items()):
            item.addTo(gl, i+1, key in settable, key in joggable)
        gl.addWidget(self._interrupt, 2 + len(self._items), 2)
        gl.addWidget(self._execute, 2 + len(self._items), 3)
        gl.addWidget(SettingsButton(clicked=self._showSettings), 2 + len(self._items), 0)

    def _setMoveToValue(self):
        """
        Sets target positions for axes based on user input in the GUI.
        """
        targetDict = {name: item.value() for name, item in self._items.items() if item.value() is not None}
        if len(targetDict) > 0:
            self._obj.set(**targetDict)

    def _busyStateChanged(self):
        """
        Updates the GUI based on the busy state of the axes.

        Disables jog buttons, nowAt spin boxes, and moveTo line edits for axes that are busy, and enables them for axes that are idle.

        Args:
            busy (dict): Mapping of axis names to their busy state (bool).
        """
        anyBusy = bool(any([item.busy for item in self._items.values()]))
        allAlive = all([item.alive for item in self._items.values()])

        self._execute.setText("Moving" if anyBusy else "Go")
        self._execute.setEnabled(not anyBusy and allAlive)
        self._interrupt.setEnabled(anyBusy)

    def _aliveStateChanged(self):
        """
        Updates the GUI controls based on the alive state of the axes.

        Disable jog buttons, nowAt spin box and moveTo line edits when dead and enable them when alive.

        Args:
            alive (dict): Mapping of axis names to alive state (bool).
        """
        anyBusy = bool(any([item.busy for item in self._items.values()]))
        allAlive = all([item.alive for item in self._items.values()])
        self._execute.setEnabled(not anyBusy and allAlive)
        self._interrupt.setEnabled(anyBusy)

    def _showSettings(self):
        settingsWindow = _SettingsDialog(self, self._obj)
        settingsWindow.exec_()

    def _clearMoveToFields(self):
        """
        Clears all move-to input fields in the GUI.
        """
        for item in self._items.values():
            item.clear()


class _MotorRowLayout(QtCore.QObject):
    def __init__(self, obj, label):
        super().__init__()
        self._obj = obj
        self._name = label
        self.busy = False
        self.alive = True
        self.__initLayout(obj, label)

        self._obj.valueChanged.connect(self._valueChanged)
        self._obj.busyStateChanged.connect(self._busyChanged)
        self._obj.aliveStateChanged.connect(self._aliveChanged)

    def __initLayout(self, obj, label):
        self._label = QtWidgets.QLabel(label)
        self._label.setAlignment(QtCore.Qt.AlignCenter)

        self._now = QtWidgets.QDoubleSpinBox()
        self._now.setRange(-np.inf, np.inf)
        self._now.setReadOnly(True)
        self._now.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
        self._now.setDecimals(3)
        self._now.setStyleSheet("background-color: #f0f0f0;")
        self._now.setValue(obj.get()[self._name])

        self._moveTo = QtWidgets.QLineEdit()
        self._jogNega = QtWidgets.QPushButton(qta.icon("ri.arrow-left-fill"), "", clicked=self._nega)
        self._jogPosi = QtWidgets.QPushButton(qta.icon("ri.arrow-right-fill"), "", clicked=self._posi)
        self._jogStep = QtWidgets.QDoubleSpinBox()
        self._jogStep.setRange(0, np.inf)
        self._jogStep.setDecimals(2)

        self._alive = AliveIndicator(obj, axis=label)

    def addTo(self, grid, i, settable=True, joggable=True):
        grid.addWidget(self._alive, 1 + i, 0, alignment=QtCore.Qt.AlignCenter)
        grid.addWidget(self._label, 1 + i, 1)
        grid.addWidget(self._now, 1 + i, 2)
        if settable:
            grid.addWidget(self._moveTo, 1 + i, 3)
            if joggable:
                grid.addWidget(self._jogNega, 1 + i, 4)
                grid.addWidget(self._jogPosi, 1 + i, 5)
                grid.addWidget(self._jogStep, 1 + i, 6)

    def _valueChanged(self, value):
        if self._name in value:
            self._now.setValue(value[self._name])

    def _busyChanged(self, busy):
        if self._name in busy:
            self.busy = busy[self._name]
            self._updateState()

    def _aliveChanged(self, alive):
        if self._name in alive:
            self.alive = alive[self._name]
            self._updateState()

    def _updateState(self):
        self._now.setEnabled(self.alive)
        self._moveTo.setEnabled(not self.busy and self.alive)
        self._jogNega.setEnabled(not self.busy and self.alive)
        self._jogPosi.setEnabled(not self.busy and self.alive)

    def value(self):
        try:
            return float(self._moveTo.text())
        except ValueError:
            return None

    def clear(self):
        self._moveTo.setText("")

    def _nega(self):
        """
        Handles negative jog button press for an axis.
        """
        target = self._obj.get()[self._name] - self._jogStep.value()
        self._obj.set(**{self._name: target})
        self._moveTo.setText(f"{target:.3f}")

    def _posi(self):
        """
        Handles positive jog button press for an axis.
        """
        target = self._obj.get()[self._name] + self._jogStep.value()
        self._obj.set(**{self._name: target})
        self._moveTo.setText(f"{target:.3f}")


class MotorMemory(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        self.__initLayout()

        # Load memory file
        dir = os.path.join(".lys_instr", "GUI", "MultiMotor")
        os.makedirs(dir, exist_ok=True)
        self._path = os.path.join(dir, "position_positionList.lst")

        self._savedPositions = []
        if os.path.exists(self._path):
            with open(self._path, "r") as f:
                self._savedPositions = json.load(f)
        self._updateMemory()

    def __initLayout(self):
        # Create memory panel
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

        # Collapsible panel layout
        save = QtWidgets.QPushButton("Save", clicked=self._save)
        save.setEnabled(True)
        load = QtWidgets.QPushButton("Load", clicked=self._load)
        load.setEnabled(False)
        delete = QtWidgets.QPushButton("Delete", clicked=self._delete)
        delete.setEnabled(False)

        self._memoryBtnsLayout = QtWidgets.QHBoxLayout()
        self._memoryBtnsLayout.addWidget(save)
        self._memoryBtnsLayout.addWidget(load)
        self._memoryBtnsLayout.addWidget(delete)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Memory"))
        layout.addWidget(self._positionList)
        layout.addLayout(self._memoryBtnsLayout)

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

    def _memoEdited(self, item, column):
        """
        Handles edits to the memo field in the memory panel.

        Args:
            item (QTreeWidgetItem): The edited item.
            column (int): The column index that was edited.
        """
        if column == 2:
            label = item.text(0)
            memo = item.text(2)
            for idx, pos in enumerate(self._savedPositions):
                if pos["label"] == label:
                    self._savedPositions[idx]["memo"] = memo
                    with open(self._path, "w") as f:
                        json.dump(self._savedPositions, f)
                    break

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


class _SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent, obj):
        super().__init__(parent)
        self.setWindowTitle("Motor Settings")

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(_GeneralPanel(obj), "General")
        tabWidget.addTab(obj.settingsWidget(), "Optional")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tabWidget)
        self.setLayout(layout)


class _GeneralPanel(QtWidgets.QWidget):
    """
    Settings panel for a multi-axis motor device.

    Allows viewing and toggling the alive/dead status and managing offsets for each axis.
    """

    def __init__(self, obj):
        super().__init__()
        self._obj = obj
        self._initLayout()

    def _initLayout(self):
        """
        Creates and initializes all GUI components of the settings dialog, and connects signals to their respective slots.
        """
        # Create offset panel
        self._offsetBtns = {name: QtWidgets.QPushButton("Offset", clicked=lambda checked, n=name: self._offsetAxis(n)) for name in self._obj.offset}
        self._unsetBtns = {name: QtWidgets.QPushButton("Unset", clicked=lambda checked, n=name: self._unsetAxis(n)) for name in self._obj.offset}
        self._offsetLbls = {name: QtWidgets.QLabel(name) for name in self._obj.offset}
        self._offsetEdits = {name: QtWidgets.QDoubleSpinBox() for name in self._obj.offset}

        for name in self._obj.offset:
            self._offsetLbls[name].setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
            self._offsetEdits[name].setRange(-np.inf, np.inf)
            self._offsetEdits[name].setReadOnly(True)
            self._offsetEdits[name].setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
            self._offsetEdits[name].setDecimals(3)
            self._offsetEdits[name].setValue(self._obj.offset[name])
            self._offsetEdits[name].setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            self._offsetEdits[name].setMinimumWidth(80)

        offsetLayout = QtWidgets.QGridLayout()
        for i, name in enumerate(self._obj.offset):
            offsetLayout.addWidget(self._offsetLbls[name], i, 0)
            offsetLayout.addWidget(self._offsetEdits[name], i, 1)
            offsetLayout.addWidget(self._offsetBtns[name], i, 2)
            offsetLayout.addWidget(self._unsetBtns[name], i, 3)

        # Combine layouts
        gl = QtWidgets.QVBoxLayout()
        gl.addLayout(offsetLayout)
        self.setLayout(gl)

    def _offsetAxis(self, name):
        """
        Sets the offset for a specific axis to its current value.

        Args:
            name (str): The axis name.
        """
        self._obj.offset[name] += self._obj.get()[name]
        self._offsetEdits[name].setValue(self._obj.offset[name])
        self._obj.valueChanged.emit(self._obj.get())

    def _unsetAxis(self, name):
        """
        Clears the offset for a specific axis.

        Args:
            name (str): The axis name.
        """
        self._obj.offset[name] = 0
        self._offsetEdits[name].setValue(0)
        self._obj.valueChanged.emit(self._obj.get())
