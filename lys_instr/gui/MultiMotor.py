import numpy as np
import qtawesome as qta
import logging

from lys.Qt import QtWidgets, QtCore
from lys_instr import MultiMotorInterface

from .widgets import AliveIndicator, SettingsButton
from .Memory import ControllerMemory


class MultiMotorGUI(QtWidgets.QWidget):
    """
    GUI widget for controlling and monitoring a multi-axis motor.

    Provides controls for moving, jogging, offsetting, and saving/loading positions for multiple axes.
    Accepts a ``MultiMotorInterface`` instance or a sequence of such instances. 
    Listens to their ``busyStateChanged`` and ``aliveStateChanged`` signals to update the GUI.
    """

    def __init__(self, obj, axisNamesSettable=None, axisNamesJoggable=None, axisNamesOffsettable=None, memory=None, memoryPath=None):
        """
        Initialize the motor GUI.

        Args:
            obj (MultiMotorInterface | Sequence[MultiMotorInterface]): A single controller (motor) or a sequence of such objects.
            axisNamesSettable (Iterable[str] | None): Names of axes that can be set. Defaults to all axes.
            axisNamesJoggable (Iterable[str] | None): Names of axes that can be jogged. Defaults to all axes.
            axisNamesOffsettable (Iterable[str] | None): Names of axes that support offsets. Defaults to all axes.
            memory (str | None): Position of the memory widget; one of ``'bottom'``, ``'right'`` or ``None``.
            memoryPath (str | None): Path or name of the memory file used by the ``ControllerMemory`` widget.
        """
        super().__init__()

        if isinstance(obj, MultiMotorInterface):
            obj = [obj]
        self._objs = obj

        joggable = self.controllers.keys() if axisNamesJoggable is None else list(axisNamesJoggable)
        settable = self.controllers.keys() if axisNamesSettable is None else list(axisNamesSettable)
        self._offsettable = self.controllers.keys() if axisNamesOffsettable is None else list(axisNamesOffsettable)

        self._initLayout(settable, joggable, memory, memoryPath)
        for obj in self._objs:
            obj.busyStateChanged.connect(self._busyStateChanged)
            obj.aliveStateChanged.connect(self._aliveStateChanged)

    @property
    def controllers(self):
        """
        Mapping of axis names to respective controllers (motors).

        Returns:
            dict[str, MultiMotorInterface]: Mapping of axis names to controllers (later controllers overwrite earlier ones when axis names collide).
        """
        return {name: obj for obj in self._objs for name in obj.nameList}

    def _initLayout(self, settable, joggable, memory, path):
        """
        Create and arrange the widgets for the control panel.

        Args:
            settable (Iterable[str]): Names of axes that are settable from the GUI.
            joggable (Iterable[str]): Names of axes that are joggable from the GUI.
            memory (str | None): See constructor.
            path (str | None): Memory path passed to ``ControllerMemory``.
        """
        self._items = {name: _MotorRowLayout(c, name) for name, c in self.controllers.items()}

        self._execute = QtWidgets.QPushButton("Go", clicked=self._setMoveToValue)
        self._execute.setEnabled(True)

        self._interrupt = QtWidgets.QPushButton("Stop", clicked=self._stop)
        self._interrupt.setEnabled(False)

        # Axis controls layout
        gl = QtWidgets.QGridLayout()
        gl.setAlignment(QtCore.Qt.AlignTop)
        gl.addWidget(QtWidgets.QLabel("Axis"), 0, 1)
        gl.addWidget(QtWidgets.QLabel("Now at"), 0, 2)
        gl.addWidget(QtWidgets.QLabel("Move to"), 0, 3)
        if any(name in settable and name in joggable for name in self.controllers.keys()):
            gl.addWidget(QtWidgets.QLabel("Jog"), 0, 4)
            gl.addWidget(QtWidgets.QLabel("Step"), 0, 6)

        for i, (key, item) in enumerate(self._items.items()):
            item.addTo(gl, i+1, key in settable, key in joggable)
        gl.addWidget(self._interrupt, 2 + len(self._items), 2)
        gl.addWidget(self._execute, 2 + len(self._items), 3)
        gl.addWidget(SettingsButton(clicked=self._showSettings), 2 + len(self._items), 0)

        if memory is None:
            self.setLayout(gl)
        else:
            if memory == "bottom":
                box = QtWidgets.QVBoxLayout()
            else:
                box = QtWidgets.QHBoxLayout()
            box.addLayout(gl)
            box.addWidget(ControllerMemory(self._objs, path))
            self.setLayout(box)

    def _setMoveToValue(self):
        """
        Apply GUI-entered target positions to connected controllers (motors).
        """
        targetAll = {name: item.value() for name, item in self._items.items() if item.value() is not None}
        for obj in self._objs:
            targ = {name: value for name, value in targetAll.items() if name in obj.nameList}
            if len(targ) > 0:
                obj.set(**targ)

    def _busyStateChanged(self):
        """
        Update the GUI enabled state based on axis busy flags.
        """
        anyBusy = bool(any([item.busy for item in self._items.values()]))
        allAlive = all([item.alive for item in self._items.values()])

        self._execute.setText("Moving" if anyBusy else "Go")
        self._execute.setEnabled(not anyBusy and allAlive)
        self._interrupt.setEnabled(anyBusy)

    def _aliveStateChanged(self):
        """
        Update the GUI enabled state based on axis alive flags.
        """
        anyBusy = bool(any([item.busy for item in self._items.values()]))
        allAlive = all([item.alive for item in self._items.values()])
        self._execute.setEnabled(not anyBusy and allAlive)
        self._interrupt.setEnabled(anyBusy)

    def _stop(self):
        """
        Stop all active motions.
        """
        for obj in self._objs:
            obj.stop()

    def _showSettings(self):
        """
        Show the settings dialog.
        """
        settingsWindow = _SettingsDialog(self, self._objs, self._offsettable)
        settingsWindow.exec_()


class _MotorRowLayout(QtCore.QObject):
    """
    Helper to manage the widgets and state for a single motor-axis row.

    Each instance creates the label, current-value display, move-to input and jog controls for one axis.
    It listens to the controller's (motor's) signals to keep the row in sync.
    """

    def __init__(self, obj, label):
        """
        Initialize the motor-row helper.

        Args:
            obj (MultiMotorInterface): Controller (motor) owning this axis.
            label (str): Axis name used for labels and lookups.
        """
        super().__init__()
        self._obj = obj
        self._name = label
        self.busy = False
        self.alive = True
        self.__initLayout(obj, label)
        self.__initValues(obj)

        self._obj.valueChanged.connect(self._valueChanged)
        self._obj.busyStateChanged.connect(self._busyChanged)
        self._obj.aliveStateChanged.connect(self._aliveChanged)

        if self._name in getattr(self._obj, 'offset', {}):
            self._obj.offsetChanged.connect(self._updateMoveTo)

    def __initLayout(self, obj, label):
        """
        Create widgets for the axis row.

        Constructs the label, current-value display, move-to editor and jog controls for the axis but leaves layout placement to the ``addTo`` method.
        """
        self._label = QtWidgets.QLabel(label)
        self._label.setAlignment(QtCore.Qt.AlignCenter)

        self._now = QtWidgets.QDoubleSpinBox()
        self._now.setRange(-np.inf, np.inf)
        self._now.setReadOnly(True)
        self._now.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
        self._now.setDecimals(5)
        self._now.setStyleSheet("background-color: #f0f0f0;")

        self._moveTo = QtWidgets.QLineEdit()
        self._jogNega = QtWidgets.QPushButton(qta.icon("ri.arrow-left-fill"), "", clicked=self._nega)
        self._jogPosi = QtWidgets.QPushButton(qta.icon("ri.arrow-right-fill"), "", clicked=self._posi)
        self._jogStep = QtWidgets.QDoubleSpinBox()
        self._jogStep.setRange(0, np.inf)
        self._jogStep.setDecimals(2)

        self._alive = AliveIndicator(obj, axis=label)

    def __initValues(self, obj):
        """
        Initialize the displayed value from the controller (motor).
        """
        if self.alive:
            self._now.setValue(obj.get()[self._name])
        else:
            self.alive = False
            self._updateState()
            logging.warning(f"Axis {self._name} is not alive during initialization of MultiMotorGUI.")

    def addTo(self, grid, i, settable=True, joggable=True):
        """
        Insert the row's widgets into a grid layout.

        Args:
            grid (QGridLayout): Grid to populate.
            i (int): Row index (0-based) within the grid header region.
            settable (bool): Whether to include the Move-To editor.
            joggable (bool): Whether to include jog buttons.
        """
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
        """
        Update the displayed current level when the controller (motor) emits a new value.

        Args:
            value (dict): Mapping of axis names to numeric values emitted by the controller's ``valueChanged`` signal.
        """
        if self._name in value:
            self._now.setValue(value[self._name])

    def _busyChanged(self, busy):
        """
        Update the row's busy flag and refresh widget enablement.

        Args:
            busy (dict): Mapping of axis names to busy states emitted by the controller's ``busyStateChanged`` signal.
        """
        if self._name in busy:
            self.busy = busy[self._name]
            self._updateState()

    def _aliveChanged(self, alive):
        """
        Update the row's alive flag and refresh widget enablement.

        Args:
            alive (dict): Mapping of axis names to alive states emitted by the controller's ``aliveStateChanged`` signal.
        """
        if self._name in alive:
            self.alive = alive[self._name]
            self._updateState()

    def _updateState(self):
        """
        Enable or disable widgets according to current busy/alive flags.
        """
        self._now.setEnabled(self.alive)
        self._moveTo.setEnabled(not self.busy and self.alive)
        self._jogNega.setEnabled(not self.busy and self.alive)
        self._jogPosi.setEnabled(not self.busy and self.alive)

    def value(self):
        """
        Return the numeric value entered in the Move-To editor.

        Returns:
            float | None: Parsed float value or ``None`` if the field is empty or cannot be parsed as a float.
        """
        try:
            return float(self._moveTo.text())
        except ValueError:
            return None

    def _updateMoveTo(self):
        """
        Update the Move-To editor from the controller's (motor's) target/offset.
        """
        tar = self._obj.target.get(self._name)
        if tar is not None:
            s = str(tar - self._obj.offset[self._name])
        else:
            s = ""
        self._moveTo.setText(s)

    def _nega(self):
        """
        Handle negative jog button press for an axis.
        """
        target = self._obj.get()[self._name] - self._jogStep.value()
        self._obj.set(**{self._name: target})
        self._moveTo.setText(f"{target:.3f}")

    def _posi(self):
        """
        Handle positive jog button press for an axis.
        """
        target = self._obj.get()[self._name] + self._jogStep.value()
        self._obj.set(**{self._name: target})
        self._moveTo.setText(f"{target:.3f}")


class _SettingsDialog(QtWidgets.QDialog):
    """
    Dialog for settings.

    Provides a tabbed interface for general and optional settings of a device.
    Emits an ``updated`` signal when offsets are changed in the general settings panel.
    """

    def __init__(self, parent, objs, offsettable):
        """
        Create the motor settings dialog with general and optional tabs.

        Args:
            parent (QWidget): Parent widget (the main ``MultiMotorGUI`` instance).
            objs (Sequence[MultiMotorInterface]): Controllers (motors) used to populate optional per-controller tabs.
            offsettable (Iterable[str]): Names of axes that support offsets (passed to the general panel).
        """
        super().__init__(parent)
        self.setWindowTitle("Motor Settings")

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(_GeneralPanel(parent.controllers, offsettable), "General")
        for i, c in enumerate(objs, 1):
            tabWidget.addTab(c.settingsWidget(), f"Optional {i}")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tabWidget)
        self.setLayout(layout)


class _GeneralPanel(QtWidgets.QWidget):
    """
    General settings panel for the device.

    Provides controls for viewing and editing per-axis offsets. 
    """

    def __init__(self, controllers, offsettable):
        """
        Initialize the general settings panel.

        Args:
            controllers (dict[str, MultiMotorInterface]): Mapping of axis names to controllers (motors) used to query offsets and save state.
            offsettable (Iterable[str]): Names of axes that support offsets.
        """
        super().__init__()
        self._controllers = controllers
        self._initLayout(controllers, offsettable)

    def _initLayout(self, controllers, offsettable):
        """
        Create GUI components of the dialog and connect signals to respective slots.
        """
        # Create offset panel
        offsettable = {name: c for name, c in controllers.items() if name in offsettable}
        self._offsetBtns = {name: QtWidgets.QPushButton("Offset", clicked=lambda checked, n=name: self._offsetAxis(n)) for name in offsettable}
        self._unsetBtns = {name: QtWidgets.QPushButton("Unset", clicked=lambda checked, n=name: self._unsetAxis(n)) for name in offsettable}
        self._offsetLbls = {name: QtWidgets.QLabel(name) for name in offsettable}
        self._offsetEdits = {name: QtWidgets.QDoubleSpinBox() for name in offsettable}

        for name, c in offsettable.items():
            self._offsetLbls[name].setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
            self._offsetEdits[name].setRange(-np.inf, np.inf)
            self._offsetEdits[name].setReadOnly(True)
            self._offsetEdits[name].setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
            self._offsetEdits[name].setDecimals(5)
            self._offsetEdits[name].setValue(c.offset[name])
            self._offsetEdits[name].setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            self._offsetEdits[name].setMinimumWidth(80)

        offsetLayout = QtWidgets.QGridLayout()
        for i, name in enumerate(offsettable):
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
        Set the offset for a specific axis to its current value.

        Args:
            name (str): The axis name.
        """
        obj = self._controllers[name]
        obj.offset[name] += obj.get()[name]
        self._offsetEdits[name].setValue(obj.offset[name])
        obj.valueChanged.emit(obj.get())
        obj.save()

    def _unsetAxis(self, name):
        """
        Clear the offset for a specific axis.

        Args:
            name (str): The axis name.
        """
        obj = self._controllers[name]
        obj.offset[name] = 0
        self._offsetEdits[name].setValue(0)
        obj.valueChanged.emit(obj.get())
        obj.save()
