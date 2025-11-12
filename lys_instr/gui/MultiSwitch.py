from lys.Qt import QtWidgets, QtCore
from lys_instr import MultiControllerInterface
from .widgets import AliveIndicator, SettingsButton


class MultiSwitchGUI(QtWidgets.QWidget):
    """
    GUI widget for controlling and monitoring a multi-axis switch.

    Provides controls for setting and displaying switch states for multiple axes.
    Accepts a ``MultiControllerInterface`` instance or a sequence of such instances. 
    Listens to their ``busyStateChanged`` and ``aliveStateChanged`` signals to update the GUI.
    """
    def __init__(self, obj, axisNamesSettable=None):
        """
        Initialize the switch GUI.

        Args:
            obj (MultiSwitchInterface | Sequence[MultiSwitchInterface]): The controller (switch) or a sequence of such objects.
            axisNamesSettable (iterable, optional): Names of axes that can be set. Defaults to all axes.
        """
        super().__init__()

        if isinstance(obj, MultiControllerInterface):
            obj = [obj]
        self._objs = obj

        settable = self.controllers.keys() if axisNamesSettable is None else list(axisNamesSettable)

        self._initLayout(settable)
        for obj in self._objs:
            obj.busyStateChanged.connect(self._busyStateChanged)
            obj.aliveStateChanged.connect(self._aliveStateChanged)

    @property
    def controllers(self):
        """
        Mapping of axis names to respective controllers (switches).

        Returns:
            dict[str, MultiSwitchInterface]: Mapping of axis names to controllers (later controllers overwrite earlier ones when axis names collide).
        """
        return {name: obj for obj in self._objs for name in obj.nameList}

    def _initLayout(self, settable):
        """
        Create and arrange the widgets for the control panel.

        Args:
            settable (Iterable[str]): Names of axes that are settable from the GUI.
        """
        self._items = {name: _SwitchRowLayout(c, name) for name, c in self.controllers.items()}

        self._execute = QtWidgets.QPushButton("Apply", clicked=self._setMoveToValue)
        self._execute.setEnabled(True)

        # Axis controls layout
        gl = QtWidgets.QGridLayout()
        gl.setAlignment(QtCore.Qt.AlignTop)
        gl.addWidget(QtWidgets.QLabel("Axis"), 0, 1)
        gl.addWidget(QtWidgets.QLabel("Now at"), 0, 2)
        gl.addWidget(QtWidgets.QLabel("Move to"), 0, 3)
        for i, (key, item) in enumerate(self._items.items()):
            item.addTo(gl, i+1, key in settable)
        gl.addWidget(self._execute, 2 + len(self._items), 3)
        gl.addWidget(SettingsButton(clicked=self._showSettings), 2 + len(self._items), 0)

        self.setLayout(gl)

    def _setMoveToValue(self):
        """
        Apply GUI-entered target states to connected controllers (switches).
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
        self._execute.setEnabled(not anyBusy and allAlive)

    def _aliveStateChanged(self):
        """
        Update the GUI enabled state based on axis alive flags.
        """
        anyBusy = bool(any([item.busy for item in self._items.values()]))
        allAlive = all([item.alive for item in self._items.values()])
        self._execute.setEnabled(not anyBusy and allAlive)

    def _showSettings(self):
        """
        Open the settings dialog.
        """
        settingsWindow = _SettingsDialog(self)
        settingsWindow.exec_()


class _SwitchRowLayout(QtCore.QObject):
    """
    Helper to manage the widgets and state for a single switch-axis row.

    Each instance creates the label, current-value display, and a selector for the axis' target level.
    It listens to the controller's (switch's) signals to keep the row in sync.
    """

    def __init__(self, obj, label):
        """
        Initialize the switch-row helper.

        Args:
            obj (MultiSwitchInterface): Controller (switch) owning this axis.
            label (str): Axis name used for labels and lookups.
        """
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
        """
        Create widgets for the axis row.

        Construct the label, current-value display and the selector widget for the axis but leaves layout placement to the ``addTo`` method.
        """
        self._label = QtWidgets.QLabel(label)
        self._label.setAlignment(QtCore.Qt.AlignCenter)

        self._now = QtWidgets.QLineEdit(obj.get()[self._name])
        self._now.setAlignment(QtCore.Qt.AlignCenter)
        self._now.setReadOnly(True)
        self._now.setStyleSheet("background-color: #f0f0f0;")

        self._moveTo = QtWidgets.QComboBox()
        self._moveTo.addItems([" "] + obj.labelNames)

        self._alive = AliveIndicator(obj, axis=label)

    def addTo(self, grid, i, settable=True):
        """
        Insert the row's widgets into a grid layout.

        Args:
            grid (QGridLayout): Grid to populate.
            i (int): Row index (0-based) within the grid header region.
            settable (bool): Whether to include the Move-To selector.
        """
        grid.addWidget(self._alive, 1 + i, 0, alignment=QtCore.Qt.AlignCenter)
        grid.addWidget(self._label, 1 + i, 1)
        grid.addWidget(self._now, 1 + i, 2)
        if settable:
            grid.addWidget(self._moveTo, 1 + i, 3)

    def _valueChanged(self, value):
        """
        Update the displayed current level when the controller (switch) emits a new value.

        Args:
            value (dict): Mapping of axis names to level strings emitted by the controller's ``valueChanged`` signal.
        """
        if self._name in value:
            self._now.setText(value[self._name])

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

    def value(self):
        """
        Return the currently selected target level from the Move-To selector.

        Returns:
            str | None: Selected level string, or ``None`` if no selection was made.
        """
        v = self._moveTo.currentText()
        if v == " ":
            return None
        return v 


class _SettingsDialog(QtWidgets.QDialog):
    """
    Settings dialog for the device.

    Provides a tabbed interface for general and optional settings.
    """

    def __init__(self, parent):
        """
        Create the switch settings dialog with general and optional tabs.

        Args:
            parent (QWidget): Parent widget (the main ``MultiSwitchGUI`` instance).
        """
        super().__init__(parent)
        self.setWindowTitle("Switch Settings")

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(_GeneralPanel(parent.controllers), "General")
        #tabWidget.addTab(obj.settingsWidget(), "Optional")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tabWidget)
        self.setLayout(layout)


class _GeneralPanel(QtWidgets.QWidget):
    """
    General settings panel for the device.
    """
    def __init__(self, controllers):
        """
        Initialize the general settings panel.

        Args:
            controllers (dict[str, MultiSwitchInterface]): Mapping of axis names to controllers (switches) to configure.
        """
        super().__init__()
        self._controllers = controllers
