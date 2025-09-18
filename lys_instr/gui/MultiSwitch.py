from lys.Qt import QtWidgets, QtCore
from .Widgets import AliveIndicator, SettingsButton


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
        self._obj = obj
        self._axisNamesSettable = list(axisNamesSettable) if axisNamesSettable else list(self._obj.nameList)
        self._obj.valueChanged.connect(self._valueChanged)
        self._obj.busyStateChanged.connect(self._busyStateChanged)
        self._obj.aliveStateChanged.connect(self._aliveStateChanged)
        self._initLayout()

    def _initLayout(self):
        """
        Initializes the GUI layout and widgets for the multi-switch control panel.
        """
        # Axis labels
        self._axisNames = {name: QtWidgets.QLabel(name) for name in self._obj.nameList}
        for lbl in self._axisNames.values():
            lbl.setAlignment(QtCore.Qt.AlignCenter)
        axisNameLabel = QtWidgets.QLabel("Axis")

        # Display current state (nowAt) as label
        self._nowAt = {name: QtWidgets.QLineEdit("OFF") for name in self._obj.nameList}
        for le in self._nowAt.values():
            le.setAlignment(QtCore.Qt.AlignCenter)
            le.setReadOnly(True)
            le.setStyleSheet("background-color: #f0f0f0;")
        nowAtLabel = QtWidgets.QLabel("Now at")

        # Combo to set target state (moveTo)
        self._moveTo = {name: QtWidgets.QComboBox() for name in self._axisNamesSettable}
        for combo in self._moveTo.values():
            combo.addItems(["OFF", "ON"])
        moveToLabel = QtWidgets.QLabel("Set to")

        self._execute = QtWidgets.QPushButton("Apply", clicked=self._setMoveToValue)
        self._execute.setEnabled(True)

        aliveIndicator = {name: AliveIndicator(self._obj, axis=name) for name in self._obj.nameList}
        
        settings = SettingsButton(clicked=self._showSettings)

        # Create main layout
        gl = QtWidgets.QGridLayout()
        gl.setAlignment(QtCore.Qt.AlignTop)
        gl.addWidget(axisNameLabel, 0, 1)
        gl.addWidget(nowAtLabel, 0, 2)
        gl.addWidget(moveToLabel, 0, 3)
        for i, name in enumerate(self._obj.nameList):
            gl.addWidget(aliveIndicator[name], 1 + i, 0, alignment=QtCore.Qt.AlignCenter)
            gl.addWidget(self._axisNames[name], 1 + i, 1)
            gl.addWidget(self._nowAt[name], 1 + i, 2)
            if name in self._axisNamesSettable:
                gl.addWidget(self._moveTo[name], 1 + i, 3)
        gl.addWidget(self._execute, 1 + len(self._obj.nameList), 3)
        gl.addWidget(settings, 1 + len(self._obj.nameList), 0)

        # Set layout
        self.setLayout(gl)

    def _setMoveToValue(self):
        """
        Sets target switch states for axes based on user input in the GUI.
        """
        targetDict = {}
        for name in self._moveTo:
            combo = self._moveTo[name]
            targetDict[name] = bool(combo.currentIndex())
        if targetDict:
            self._obj.set(**targetDict)

    def _valueChanged(self, valueList):
        """
        Updates the displayed axis states in the GUI.

        Args:
            valueList (dict): Mapping of axis names to their new values.
        """
        for key, value in valueList.items():
            self._nowAt[key].setText("ON" if value else "OFF")

    def _busyStateChanged(self, busy):
        """
        Updates the GUI based on the busy state of the axes.

        Disables moveTo combos and execute button for axes that are busy, and enables them for axes that are idle.

        Args:
            busy (dict): Mapping of axis names to their busy state (bool).
        """
        anyBusy = bool(any(busy.values()))
        allAlive = all(self._obj.isAlive.values())
        self._execute.setEnabled(not anyBusy and allAlive)
        for name in self._moveTo:
            self._moveTo[name].setEnabled(not busy.get(name, False) and allAlive)

    def _aliveStateChanged(self, alive):
        """
        Updates the GUI controls based on the alive state of the axes.

        Disables moveTo combos and execute button when dead and enables them when alive.

        Args:
            alive (dict): Mapping of axis names to alive state (bool).
        """
        busy = self._obj.isBusy
        anyBusy = any(busy.values())
        allAlive = all(alive.values())
        self._execute.setEnabled(not anyBusy and allAlive)
        for name in self._moveTo:
            axisAlive = alive.get(name, True)
            self._moveTo[name].setEnabled(axisAlive and not busy.get(name, False))

    def _showSettings(self):
        """
        Opens the settings dialog for the device.
        """
        settingsWindow = _SettingsDialog(self, self._obj)
        settingsWindow.exec_()


class _SettingsDialog(QtWidgets.QDialog):
    """
    Dialog for settings.

    Provides a tabbed interface for general and optional settings of a device.
    Emits an ``updated`` signal when offsets are changed in the general settings panel.
    """
    updated = QtCore.pyqtSignal()

    def __init__(self, parent, obj):
        """
        Initializes the settings dialog.

        Args:
            parent (QWidget): The parent widget.
            obj: The motor object to configure.
        """
        super().__init__(parent)
        self.setWindowTitle("Switch Settings")
        self.generalPanel = _GeneralPanel(obj)

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(self.generalPanel, "General")
        tabWidget.addTab(obj.settingsWidget(), "Optional")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tabWidget)
        self.setLayout(layout)


class _GeneralPanel(QtWidgets.QWidget):
    """
    General settings panel for the device.
    """
    def __init__(self, obj):
        """
        Initializes the general panel for the device.
        """
        super().__init__()
        self._obj = obj




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