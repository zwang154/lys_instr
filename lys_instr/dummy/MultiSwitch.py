import time

from lys.Qt import QtCore
from lys_instr import MultiSwitchInterface
from lys_instr.dummy.MultiMotor import _OptionalPanel

class _LevelInfo(QtCore.QObject):
    """
    Container that holds the current simulated switch level, a pending level target, and an error flag for a switch axis.
    """

    def __init__(self, state, interval):
        """
        Initialize the container.

        Args:
            state (str): Initial level of the switch axis.
            interval (float): Time for the switching to complete in seconds.
        """
        super().__init__()
        self._state = state
        self._target = None
        self._interval = interval
        self.error = False

    def set(self, state):
        """
        Set a target for the switch axis.

        Store the requested target and start timing used to determine whether the target is reached.
        The target level is applied after the configured interval elapses.

        Args:
            state (str): Target level to switch to.
        """
        self._target = state
        self._timing = time.perf_counter()

    def _update(self):
        """
        Update the level of the switch axis after the configured time interval.

        Determine the switch level based on elapsed time since ``set`` was called and the configured switch interval.
        Clear the target when it is reached.
        """
        if self._target is None:
            return
        if time.perf_counter() - self._timing >= self._interval:
            self._state = self._target
            self._target = None

    @property
    def state(self):
        """
        Current simulated level of the switch axis.

        This property updates internal state before returning.

        Returns:
            str: Current level of the switch axis.
        """
        self._update()
        return self._state

    @property
    def busy(self):
        """
        Current simulated busy state of the switch axis.

        This property updates internal state before returning.

        Returns:
            bool: True if the switching is in progress, False otherwise.
        """
        self._update()
        return self._target is not None


class MultiSwitchDummy(MultiSwitchInterface):
    """
    Dummy implementation of ``MultiSwitchInterface``.

    This class simulates a multi-axis switch, including axis levels, busy/alive state management, and per-axis error injection for testing purposes.
    """

    def __init__(self, *axisNamesAll, levelNames=['OFF', 'LOW', 'MEDIUM', 'HIGH'], interval=0.1, **kwargs):
        """
        Initialize the dummy multi-axis switch.

        Call ``start()`` to begin the background polling thread.

        Args:
            *axisNamesAll: Names of axes to simulate.
            levelNames (list[str]): Ordered level names used by the switch.
            interval (float): Time for the switching to complete in seconds.
            **kwargs: Additional keyword arguments passed to the parent class.
        """
        super().__init__(levelNames, *axisNamesAll, **kwargs)
        self._data = {name: _LevelInfo(levelNames[0], interval) for name in self.nameList}
        self.start()

    def _set(self, **target):
        """
        Set target levels for the specified axes.

        Only axes present in ``target`` are updated; other axes are left unchanged.

        Args:
            target (dict[str, str]): Mapping of axis names to respective target levels.
        """
        for name, d in self._data.items():
            if name in target:
                d.set(target[name])

    def _get(self):
        """
        Get current levels for all axes.

        Returns:
            dict[str, str]: Mapping of axis names to respective current levels.
        """
        return {name: d.state for name, d in self._data.items()}
    
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
            dict[str, bool]: Mapping of axis names to alive flags.
        """
        return {name: not d.error for name, d in self._data.items()}

    def settingsWidget(self):
        """
        Create and return an optional settings widget.

        Returns:
            QtWidgets.QWidget: The settings panel widget.
        """
        return _OptionalPanel(self)
    