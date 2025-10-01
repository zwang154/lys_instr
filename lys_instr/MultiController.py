import os
import time
import logging
import weakref

import numpy as np
from .Interfaces import HardwareInterface, lock
from lys.Qt import QtCore


class _AxisInfo():
    """
    Stores the busy and alive state information for a single motor axis.

    Attributes:
        busy (bool): Whether the axis is currently busy.
        alive (bool): Whether the axis is currently alive (not in error).
    """

    def __init__(self, busy=False, alive=True):
        """
        Initializes the axis state.

        Args:
            busy (bool, optional): Initial busy state. Defaults to False.
            alive (bool, optional): Initial alive state. Defaults to True.
        """
        self.busy = busy
        self.alive = alive


class MultiControllerInterface(HardwareInterface):
    """
    Abstract interface for multi-axis motor controllers.

    This class provides background polling, state management, and Qt signals for axis value and state updates.
    Subclasses must implement device-specific methods: ``_get()``, ``_set()``, ``_isBusy()``, and ``_isAlive()``.
    ``_get()``, ``_set()``, and ``_isBusy()`` should raise RuntimeError if the device is not responding or if there is a communication error.
    ``_isAlive()`` should always return the current alive state and should not raise ``RuntimeError`` that causes interruption.

    Args:
        *axisNamesAll: Names of all axes to manage.
        **kwargs: Additional keyword arguments passed to QThread.
    """

    #: Signal (dict) emitted when axis values change.
    valueChanged = QtCore.pyqtSignal(dict)

    #: Signal (dict) emitted when busy state changes.
    busyStateChanged = QtCore.pyqtSignal(dict)

    #: Signal (dict) emitted when alive state changes.
    aliveStateChanged = QtCore.pyqtSignal(dict)

    def __init__(self, *axisNamesAll, **kwargs):
        """
        Initializes the interface with the given axis names.

        Args:
            *axisNamesAll: Names of all axes to manage.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(**kwargs)
        self._info = {name: _AxisInfo() for name in axisNamesAll}
        self._mutex = QtCore.QMutex()

    @lock
    def _loadState(self):
        """
        Polls the device and updates the state of all axes.

        Emits the ``busyStateChanged`` and ``aliveStateChanged`` signals if any axis state has changed.
        Logs any runtime errors that occur during state loading.
        """
        try:
            bs = self._isBusy()
            busyUpdate = {name: b for name, b in bs.items() if b != self._info[name].busy}

            # Emit valueChanged signal if any axis is busy
            if any(bs.values()) or len(busyUpdate) > 0:
                vs = self.get()
                self.valueChanged.emit({name: vs[name] for name, b in bs.items() if b or name in busyUpdate})

            # Update busy state log and emit busyStateChanged signal if any axis has changed its busy state
            if busyUpdate:
                for name, b in busyUpdate.items():
                    self._info[name].busy = b
                self.busyStateChanged.emit(busyUpdate)

        except RuntimeError as e:
            logging.warning(f"Runtime error in _loadState: {e}")

        finally:
            al = self._isAlive()
            aliveUpdate = {name: a for name, a in al.items() if a != self._info[name].alive}

            # Update alive state if any axis has changed its alive state
            if aliveUpdate:
                for name, a in aliveUpdate.items():
                    self._info[name].alive = a
                self.aliveStateChanged.emit(al)

    def set(self, wait=False, waitInterval=0.1, **kwargs):
        """
        Sets target values for one or more axes.

        For each axis specified in ``kwargs``, sets its target value.
        For example, to set x to 1.0 and y to 2.0, call: ``set(x=1.0, y=2.0)``.
        Optionally waits until all axes become idle after setting.

        Args:
            wait (bool, optional): If True, block until all axes become idle after setting. Defaults to False.
            waitInterval (float, optional): Polling interval in seconds while waiting. Defaults to 0.1.
            **kwargs: Axis-value pairs to set, e.g., x=1.0, y=2.0.

        Raises:
            ValueError: If any provided axis name is invalid.
        """
        with QtCore.QMutexLocker(self._mutex):
            # Validate axis names
            invalid = [name for name in kwargs if name not in self._info]
            if invalid:
                raise ValueError(f"Axis name(s) {invalid} not recognized. Available axes: {self.nameList}")

            # Update busy state for each axis in kwargs and emit busy state only for axes that are now busy
            updated = {name: True for name in kwargs if not self._info[name].busy}
            if len(updated) > 0:
                self.busyStateChanged.emit(updated)
            for name in kwargs.keys():
                self._info[name].busy = True

            # Set actual values for the axes in kwargs
            self._set(**kwargs)

        if wait:
            self.waitForReady(waitInterval)

    def get(self, type=dict):
        """
        Gets the current values of all axes in the specified data type.

        Args:
            type (type, optional): Output type (`dict`, `list`, or `np.ndarray`). Defaults to `dict`.

        Returns:
            dict or list or np.ndarray: Axis values in the requested format.

        Raises:
            TypeError: If an unsupported output type is requested.
        """
        valueDict = self._get()
        if type is dict:
            return valueDict
        elif type is list:
            return [valueDict[name] for name in self.nameList]
        else:
            raise TypeError("Unsupported type: {}".format(type))

    def stop(self):
        """
        Stops all axes.

        Calls the instance-specific ``_stop()`` method to perform the actual stopping logic.
        """
        self._stop()

    def waitForReady(self, interval=0.1):
        """
        Blocks further interaction until the device is no longer busy.

        Args:
            interval (float, optional): Polling interval in seconds. Defaults to 0.1.

        Returns:
            bool: True once all axes become idle.
        """
        while True:
            if any(self.isBusy.values()):
                time.sleep(interval)
            else:
                return True

    @property
    def isBusy(self):
        """
        Returns the current busy state of all axes.

        Returns:
            dict[str, bool]: Mapping of axis names to their busy state.

        Raises:
            RuntimeError: If the device is not responding or a communication error occurs.
        """
        with QtCore.QMutexLocker(self._mutex):
            return self._isBusy()

    @property
    def isAlive(self):
        """
        Returns the current alive state of all axes.

        Returns:
            dict[str, bool]: Mapping of axis names to their alive state.
        """
        return self._isAlive()

    @property
    def nameList(self):
        """
        Returns the list of axis names.

        Returns:
            list of str: List of axis names.
        """
        return list(self._info.keys())

    def settingsWidget(self):
        """
        Returns a generic settings dialog.

        This method is intended to be overridden in subclasses to provide a device-specific settings UI.

        Returns:
            QDialog: The settings dialog.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _isBusy(self):
        """
        Should be implemented in subclasses to provide device-specific logic for determining busy state.

        Returns:
            dict[str, bool]: Mapping of axis names to their busy state.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _isAlive(self):
        """
        Should be implemented in subclasses to provide device-specific logic for determining alive state.

        Returns:
            dict[str, bool]: Mapping of axis names to their alive state.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _get(self):
        """
        Should be implemented in subclasses to provide device-specific logic for getting axis positions.

        Returns:
            dict[str, float]: Mapping of axis names to their current positions.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def _set(self, **kwargs):
        """
        Should be implemented in subclasses to provide device-specific logic for setting axis positions.

        Args:
            kwargs (dict[str, float]): Axis-value pairs to set, e.g., x=1.0, y=2.0.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """
        raise NotImplementedError("Subclasses must implement this method.")


