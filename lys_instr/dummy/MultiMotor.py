import sys
import time

from lys_instr import MultiMotorInterface
from lys.Qt import QtWidgets, QtCore


class _ValueInfo(QtCore.QObject):
    def __init__(self, speed):
        super().__init__()
        self._position = 0
        self._speed = speed
        self._target = None
        self.error = False

    def set(self, target):
        self._before = self._position
        self._target = target
        self._timing = time.perf_counter()

    def _update(self):
        if self._target is None:
            return
        d = self._target - self._before
        t = (time.perf_counter() - self._timing)/abs(d/self._speed+sys.float_info.epsilon)
        if t >= 1:
            self._position = self._target
            self._target = None
        else:
            self._position = self._before + d * t

    def stop(self):
        self._update()
        self._target = None

    @property
    def busy(self):
        self._update()
        return self._target is not None
    
    @property
    def position(self):
        self._update()
        return self._position


class MultiMotorDummy(MultiMotorInterface):
    """
    Dummy implementation of ``MultiMotorInterface``.

    This class simulates a multi-axis motor controller, including axis positions, busy/alive state management, and per-axis error injection for testing purposes.
    """

    def __init__(self, *axisNamesAll, speed=0.2, **kwargs):
        """
        Initializes the dummy multi-axis motor with the given axis names.

        Sets up simulation parameters and starts the background polling thread.
        The simulated motion speed is set to 0.2 units per second by default.
        For testing, set ``_error`` which are a list of booleans indicating the axes to simulate errors
        ``_speed`` is the speed of simulated motion in units per second. Defaults to 0.2.

        Args:
            *axisNamesAll: Names of all axes to simulate.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(*axisNamesAll, **kwargs)
        self._data = {name: _ValueInfo(speed) for name in self.nameList}
        self.start()

    def _set(self, **target):
        """
        Sets target positions for the specified axes.

        Only the axes provided in the ``target`` dictionary will be updated; other axes remain unchanged.

        Args:
            target (dict[str, float]): Mapping of axis names to their target positions.
        """
        for name, d in self._data.items():
            if name in target:
                d.set(target[name])

    def _get(self):
        """
        Gets the current positions of all axes, updating the alive states.

        For each axis, if an error is simulated, the axis is marked as not alive and its value is set to np.nan.
        Otherwise, the current position is returned.

        Returns:
            dict[str, float]: Mapping of axis names to their current positions.
        """
        return {name: d.position for name, d in self._data.items()}

    def _stop(self):
        """
        Stops all axes in the dummy motor by clearing their timing information.
        """
        for d in self._data.values():
            d.stop()

    def _isBusy(self):
        """
        Gets the busy state of all axes in the simulated multi-axis motor.

        Returns:
            dict[str, bool]: Mapping of axis names to busy states.
        """
        return {name: d.busy for name, d in self._data.items()}

    def _isAlive(self):
        """
        Gets the alive state of all axes in the simulated multi-axis motor.

        Returns:
            dict[str, bool]: Mapping of axis names to alive states.
        """
        return {name: not d.error for name, d in self._data.items()}

    @property
    def error(self):
        """
        Gets the error state of all axes in the simulated multi-axis motor.

        Returns:
            dict[str, bool]: Mapping of axis names to error states.
        """
        return {name: d.error for name, d in self._data.items()}
    
    @error.setter
    def error(self, value):
        """
        Sets the error state of all axes in the simulated multi-axis motor.

        Args:
            value (dict[str, bool]): Mapping of axis names to error states.
        """
        for name, err in value.items():
            if name in self._data:
                self._data[name].error = err

    def settingsWidget(self):
        """
        Returns a QWidget for optional settings.

        Returns:
            QtWidgets.QWidget: The optional settings panel.
        """
        return _OptionalPanel(self)


class _OptionalPanel(QtWidgets.QWidget):
    """
    Settings panel for a multi-axis motor device.

    Allows viewing and toggling the alive state and managing offsets for each axis.
    """
    # Signal emitted when an offset is changed
    offsetChanged = QtCore.pyqtSignal()

    def __init__(self, obj):
        """
        Initializes the optional settings panel with a reference to the backend object.

        Args:
            obj: The backend motor object.
        """
        super().__init__()
        self.setWindowTitle("Settings")
        self._obj = obj
        self._initLayout()

    def _initLayout(self):
        """
        Creates and initializes all GUI components of the settings dialog, and connects signals to their respective slots.
        """
        switches = {name: QtWidgets.QPushButton("Change", clicked=lambda checked, n=name: self._toggleAlive(n)) for name in self._obj.nameList}
        nameLabels = {name: QtWidgets.QLabel(name) for name in self._obj.nameList}

        aliveLayout = QtWidgets.QGridLayout()
        for i, name in enumerate(self._obj.nameList):
            nameLabels[name].setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
            switches[name].setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
            aliveLayout.addWidget(nameLabels[name], i, 0, alignment=QtCore.Qt.AlignRight)
            aliveLayout.addWidget(switches[name], i, 1, alignment=QtCore.Qt.AlignLeft)

        group = QtWidgets.QWidget()
        group.setLayout(aliveLayout)
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addWidget(group, alignment=QtCore.Qt.AlignCenter)
        self.setLayout(mainLayout)

    def _toggleAlive(self, name):
        """
        Toggles the alive state of the specified axis and emit the corresponding signal.

        Args:
            name (str): The axis name.
        """
        backend = self._obj
        backend.error = {**backend.error, name: not backend.error[name]}
        backend.valueChanged.emit(backend.get())
        backend.aliveStateChanged.emit({name: backend.isAlive[name]})