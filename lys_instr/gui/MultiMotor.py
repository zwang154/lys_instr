import numpy as np
import qtawesome as qta

from lys.Qt import QtWidgets, QtCore
from lys_instr import MultiMotorInterface

from .widgets import AliveIndicator, SettingsButton
from .Memory import ControllerMemory


class MultiMotorGUI(QtWidgets.QWidget):
    """
    GUI widget for controlling and monitoring a multi-axis motor.

    Provides controls for moving, jogging, offsetting, and saving/loading positions for multiple axes.
    """

    def __init__(self, obj, axisNamesSettable=None, axisNamesJoggable=None, axisNamesOffsettable=None, memory=None, memoryPath=None):
        """
        Initializes the MultiMotorGUI widget.

        Args:
            obj: The motor's features object to control.
            axisNamesSettable (iterable, optional): Names of axes that can be set. Defaults to all axes.
            axisNamesJoggable (iterable, optional): Names of axes that can be jogged. Defaults to all axes.
            axisNamesOffsettable (iterable, optional): Names of axes that can be offset. Defaults to all axes.
            memory ('bottom', 'right', or None): Position of the memory widget.
            memoryPath (str): Name of the memory file. 
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
        return {name: obj for obj in self._objs for name in obj.nameList}

    def _initLayout(self, settable, joggable, memory, path):
        """
        Initializes the GUI layout and widgets for the multi-motor control panel.
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
        Sets target positions for axes based on user input in the GUI.
        """
        targetAll = {name: item.value() for name, item in self._items.items() if item.value() is not None}
        for obj in self._objs:
            targ = {name: value for name, value in targetAll.items() if name in obj.nameList}
            if len(targ) > 0:
                obj.set(**targ)

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

    def _stop(self):
        for obj in self._objs:
            obj.stop()

    def _showSettings(self):
        settingsWindow = _SettingsDialog(self, self._offsettable)
        settingsWindow.exec_()


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
        self._now.setDecimals(5)
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


class _SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent, offsettable):
        super().__init__(parent)
        self.setWindowTitle("Motor Settings")

        tabWidget = QtWidgets.QTabWidget()
        tabWidget.addTab(_GeneralPanel(parent.controllers, offsettable), "General")
        #tabWidget.addTab(obj.settingsWidget(), "Optional")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(tabWidget)
        self.setLayout(layout)


class _GeneralPanel(QtWidgets.QWidget):
    """
    Settings panel for a multi-axis motor device.

    Allows viewing and toggling the alive/dead status and managing offsets for each axis.
    """

    def __init__(self, controllers, offsettable):
        super().__init__()
        self._controllers = controllers
        self._initLayout(controllers, offsettable)

    def _initLayout(self, controllers, offsettable):
        """
        Creates and initializes all GUI components of the settings dialog, and connects signals to their respective slots.
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
        Sets the offset for a specific axis to its current value.

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
        Clears the offset for a specific axis.

        Args:
            name (str): The axis name.
        """
        obj = self._controllers[name]
        obj.offset[name] = 0
        self._offsetEdits[name].setValue(0)
        obj.valueChanged.emit(obj.get())
        obj.save()


if __name__ == "__main__":
    import sys
    from lys.Qt import QtWidgets
    from lys_instr.dummy import MultiMotorDummy

    app = QtWidgets.QApplication(sys.argv)
    motor = MultiMotorDummy("x", "y", "z")
    motorGUI = MultiMotorGUI(motor, axisNamesJoggable=())
    motorGUI.show()
    sys.exit(app.exec_())