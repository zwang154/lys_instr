import sys
import time

from lys_instr import MultiMotorInterface
from lys.Qt import QtWidgets, QtCore


class _ValueInfo(QtCore.QObject):
    """
    Container that holds the current simulated position, a pending motion target, and an error flag for a motor axis.
    """

    def __init__(self, speed):
        """
        Initialize the container.

        Args:
            speed (float): Motion speed used for simulation in units per second.
        """
        super().__init__()
        self._position = 0
        self._speed = speed
        self._target = None
        self.error = False

    def set(self, target):
        """
        Set a target for the motor axis.

        Record the current position, store the requested target, and start timing used to interpolate the position toward the target.

        Args:
            target (float): Target position to move toward.
        """
        self._before = self._position
        self._target = target
        self._timing = time.perf_counter()

    def _update(self):
        """
        Update the axis position with a simulated value.

        Compute the interpolated position based on elapsed time since ``set`` was called and the configured speed.
        Clear the target when it is reached.
        """
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
        """
        Simulate stopping the motion.

        Update the simulated position and clear any pending target.
        """
        self._update()
        self._target = None

    @property
    def busy(self):
        """
        Current simulated busy state of the motor axis.

        This property updates internal state before returning.

        Returns:
            bool: True if the motor axis motion is in progress, False otherwise.
        """
        self._update()
        return self._target is not None
    
    @property
    def position(self):
        """
        Current simulated position of the motor axis.

        Returns:
            float: Current simulated position.
        """
        self._update()
        return self._position


class MultiMotorDummy(MultiMotorInterface):
    """
    Dummy implementation of ``MultiMotorInterface``.

    This class simulates a multi-axis motor, including axis positions, busy/alive state management, and per-axis error injection for testing purposes.
    """

    def __init__(self, *axisNamesAll, speed=10, **kwargs):
        """
        Initialize the dummy multi-axis motor.

        Call ``start()`` to begin the background polling thread.

        Args:
            *axisNamesAll: Names of axes to simulate.
            speed (float): Simulated motion speed (units per second).
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(*axisNamesAll, **kwargs)
        self._data = {name: _ValueInfo(speed) for name in self.nameList}
        self.start()

    def _set(self, **target):
        """
        Set target positions for the specified axes.

        Only axes present in ``target`` are updated; other axes are left unchanged.

        Args:
            target (dict[str, float]): Mapping of axis names to respective target positions.
        """
        for name, d in self._data.items():
            if name in target:
                d.set(target[name])

    def _get(self):
        """
        Get current positions for all axes.

        Returns:
            dict[str, float]: Mapping of axis names to respective current positions.
        """
        return {name: d.position for name, d in self._data.items()}

    def _stop(self):
        """
        Stop all axes in the dummy motor.

        Clear per-axis timing information so motion targets are abandoned.
        """
        for d in self._data.values():
            d.stop()

    def _isBusy(self):
        """
        Return busy state for all axes.

        Returns:
            dict[str, bool]: Mapping of axis names to busy states.
        """
        return {name: d.busy for name, d in self._data.items()}

    def _isAlive(self):
        """
        Return alive state for all axes.

        Returns:
            dict[str, bool]: Mapping of axis names to alive states.
        """
        return {name: not d.error for name, d in self._data.items()}

    @property
    def error(self):
        """
        Per-axis error states.

        Returns:
            dict[str, bool]: Mapping of axis names to error flags.
        """
        return {name: d.error for name, d in self._data.items()}
    
    @error.setter
    def error(self, value):
        """
        Set per-axis error states.

        Args:
            value (dict[str, bool]): Mapping of axis names to error flags.
        """
        for name, err in value.items():
            if name in self._data:
                self._data[name].error = err

    def settingsWidget(self):
        """
        Create and return an optional settings widget.

        Returns:
            QtWidgets.QWidget: The settings panel widget.
        """
        return _OptionalPanel(self)


class _OptionalPanel(QtWidgets.QWidget):
    """
    Optional settings panel.

    Provides GUI to manage offsets and toggle alive states for each axis.
    """
    # Signal emitted when an offset is changed
    offsetChanged = QtCore.pyqtSignal()

    def __init__(self, obj):
        """
        Initialize the settings panel.

        Args:
            obj (MultiMotorInterface | MultiSwitchInterface): Backend controller (motor or switch) using the panel.
        """
        super().__init__()
        self.setWindowTitle("Settings")
        self._obj = obj
        self._initLayout()

    def _initLayout(self):
        """
        Build and arrange the panel's widgets and connect signal handlers.
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
        Toggle the alive state of a backend axis and emit notification signals.

        Args:
            name (str): Name of the axis to toggle.
        """
        backend = self._obj
        backend.error = {**backend.error, name: not backend.error[name]}
        backend.valueChanged.emit(backend.get())
        backend.aliveStateChanged.emit({name: backend.isAlive[name]})