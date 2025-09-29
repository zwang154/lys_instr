from lys.Qt import QtWidgets, QtCore
from lys_instr import MultiMotorInterface
from .widgets import AliveIndicator, SettingsButton


class MultiSwitchGUI(QtWidgets.QWidget):
    """
    GUI widget for controlling and monitoring a multi-axis switch.

    Provides controls for setting and displaying ON/OFF states for multiple axes.
    """
    def __init__(self, obj, axisNamesSettable=None):
        """
        Initializes the MultiSwitchGUI widget.

        Args:
            obj: The switch object to control.
            axisNamesSettable (iterable, optional): Names of axes that can be set. Defaults to all axes.
        """
        super().__init__()

        if isinstance(obj, MultiMotorInterface):
            obj = [obj]
        self._objs = obj

        settable = self.controllers.keys() if axisNamesSettable is None else list(axisNamesSettable)

        self._initLayout(settable)
        for obj in self._objs:
            obj.busyStateChanged.connect(self._busyStateChanged)
            obj.aliveStateChanged.connect(self._aliveStateChanged)

    @property
    def controllers(self):
        return {name: obj for obj in self._objs for name in obj.nameList}

    def _initLayout(self, settable):
        """
        Initializes the GUI layout and widgets for the multi-switch control panel.
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
        Sets target switch states for axes based on user input in the GUI.
        """
        targetAll = {name: item.value() for name, item in self._items.items() if item.value() is not None}
        for obj in self._objs:
            targ = {name: value for name, value in targetAll.items() if name in obj.nameList}
            if len(targ) > 0:
                obj.set(**targ)

    def _busyStateChanged(self):
        """
        Updates the GUI based on the busy state of the axes.

        Disables moveTo combos and execute button for axes that are busy, and enables them for axes that are idle.

        Args:
            busy (dict): Mapping of axis names to their busy state (bool).
        """
        anyBusy = bool(any([item.busy for item in self._items.values()]))
        allAlive = all([item.alive for item in self._items.values()])
        self._execute.setEnabled(not anyBusy and allAlive)

    def _aliveStateChanged(self):
        """
        Updates the GUI controls based on the alive state of the axes.

        Disables moveTo combos and execute button when dead and enables them when alive.

        Args:
            alive (dict): Mapping of axis names to alive state (bool).
        """
        anyBusy = bool(any([item.busy for item in self._items.values()]))
        allAlive = all([item.alive for item in self._items.values()])
        self._execute.setEnabled(not anyBusy and allAlive)

    def _showSettings(self):
        """
        Opens the settings dialog for the device.
        """
        settingsWindow = _SettingsDialog(self)
        settingsWindow.exec_()


class _SwitchRowLayout(QtCore.QObject):
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

        self._now = QtWidgets.QLineEdit("OFF" if not obj.get()[self._name] else "ON")
        self._now.setAlignment(QtCore.Qt.AlignCenter)
        self._now.setReadOnly(True)
        self._now.setStyleSheet("background-color: #f0f0f0;")

        self._moveTo = QtWidgets.QComboBox()
        self._moveTo.addItems(["OFF", "ON"])

        self._alive = AliveIndicator(obj, axis=label)

    def addTo(self, grid, i, settable=True):
        grid.addWidget(self._alive, 1 + i, 0, alignment=QtCore.Qt.AlignCenter)
        grid.addWidget(self._label, 1 + i, 1)
        grid.addWidget(self._now, 1 + i, 2)
        if settable:
            grid.addWidget(self._moveTo, 1 + i, 3)

    def _valueChanged(self, value):
        if self._name in value:
            self._now.setText("ON" if value[self._name] else "OFF")

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

    def value(self):
        try:
            return bool(self._moveTo.currentIndex())
        except ValueError:
            return None


class _SettingsDialog(QtWidgets.QDialog):
    """
    Dialog for settings.

    Provides a tabbed interface for general and optional settings of a device.
    Emits an ``updated`` signal when offsets are changed in the general settings panel.
    """

    def __init__(self, parent):
        """
        Initializes the settings dialog.

        Args:
            parent (QWidget): The parent widget.
            obj: The motor object to configure.
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
        Initializes the general panel for the device.
        """
        super().__init__()
        self._controllers = controllers




if __name__ == "__main__":
    import sys
    from lys.Qt import QtWidgets
    from lys_instr.dummy import MultiSwitchDummy

    # Create a dummy switch with two axes named "A" and "B"
    app = QtWidgets.QApplication(sys.argv)
    switch = MultiSwitchDummy("A", "B")
    gui = MultiSwitchGUI(switch)
    gui.show()

    sys.exit(app.exec_())