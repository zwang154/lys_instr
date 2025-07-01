from datetime import datetime
import time

from lys.Qt import QtCore, QtWidgets
from .Interfaces import HardwareInterface


class SingleMotorInterface(HardwareInterface):
    """
    Abstract interface for a single-axis motor device.
    
    Extends the background thread management functionality of `HardwareInterface`.
    Defines a standard structure for managing the position (value) and operational status (busy/idle) of single-axis devices such as motors.
    Subclasses should override the following protected methods to provide device-specific behavior:
        _set(value), _get(), _stop(), _isBusy()

    Signals:
        valueChanged (float): Emitted when the motor's position changes.
        busyStateChanged (bool): Emitted when the motor's busy status changes.

    Attributes:
        _prec (float): Precision threshold for detecting position value changes.
        _value (float): Last known position of the motor.
        _busy (bool): Whether the motor is currently busy.
        _alive (bool): Whether the motor is currently alive.

    Public Methods:
        set(value, wait=False, waitInterval=0.1, waitInitial=1): Sets the motor's target position, optionally waiting for motion to complete.
        get(): Returns the current position.
        stop(): Stops the motor's motion.
        isBusy(): Returns True if the motor is moving.
        isAlive(): Returns True if the motor is responsive (overrides `HardwareInterface.isAlive()`).
        settingsWidget(parent=None): Returns a settings dialog on the GUI (to be overridden in subclasses).

    Private Methods:
        _loadState(): Polls and updates the current value and status of the device (overrides `HardwareInterface._loadState()`).
        _set(value): Sets the target position (to be overridden in subclasses).
        _get(): Returns the current position (to be overridden in subclasses).
        _stop(): Stops the motor's motion (to be overridden in subclasses).
        _isBusy(): Returns True if the motor is moving (to be overridden in subclasses).
    """

    valueChanged = QtCore.pyqtSignal(float)
    busyStateChanged = QtCore.pyqtSignal(bool)

    def __init__(self, precision=1e-5, *args, **kwargs):
        """
        Initializes the `SingleMotorInterface`.

        Args:
            precision (float): Precision threshold for detecting position value changes.
            *args: Additional positional arguments for the base class.
            **kwargs: Additional keyword arguments for the base class.
        """
        super().__init__(*args, **kwargs)
        self._prec = precision
        self._value = 0
        self._busy = False
        self._alive = True

    def _loadState(self):
        """
        Polls and updates the current value and status of the device.

        Calls the device-specific `_get()` and `_isBusy()` methods to update the internal value, busy/idle status and alive/dead status.
        Emits signals through `valueChanged`, `busyStateChanged`, and `aliveStateChanged` if any changes occur or communication errors are raised.
        Overrides `HardwareInterface._loadState()`.
        """
        try:
            value = self._get()
            if abs(self._value - value) > self._prec:
                self._value = value
                self.valueChanged.emit(value)

            busy = self._isBusy()
            if self._busy != busy:
                self._busy = busy
                self.busyStateChanged.emit(busy)

        except (TimeoutError, IOError) as e:
            alive = False
            if self._alive != alive:
                self._alive = alive
                self.aliveStateChanged.emit(alive)
                self._busy = False

    def waitForReady(self, interval=0.1, initial=1):
        """
        Blocks further interaction until the device is no longer busy.

        Args:
            interval (float): Time interval (in seconds) between successive busy checks.
            initial (float): Initial wait time (in seconds) before starting the checks.

        Returns:
            bool: True once the device becomes is idle.
        """
        time.sleep(initial)
        while True:
            if self.isBusy():
                time.sleep(interval)
            else:
                return True

    # def waitForReady(self, interval=0.1, initial=1):
    #     """
    #     Blocks further interaction until the device is no longer busy or until timeout.

    #     Args:
    #         interval (float): Time interval (in seconds) between successive busy checks.
    #         initial (float): Initial wait time (in seconds) before starting the checks.

    #     Returns:
    #         bool: True once the device becomes is idle.
    #     """
    #     time.sleep(initial)
    #     nextCheck = time.perf_counter()
    #     while True:
    #         if self.isBusy():
    #             now = time.perf_counter()
    #             nextCheck += interval
    #             sleepTime = max(0, nextCheck - now)
    #             time.sleep(sleepTime)
    #         else:
    #             return True

    def set(self, value, wait=False, waitInterval=0.1, waitInitial=1):
        """
        Sets the motor's target position.

        Args:
            value (float): Target position to move to.
            wait (bool): If True, blocks until the motion is complete.
            waitInterval (float): Time interval (in seconds) between successive busy checks if waiting.
            waitInitial (float): Initial wait time (in seconds) before starting busy checks if waiting.
        """
        self._busy = True
        self._set(value)
        self.busyStateChanged.emit(True)
        if wait:
            self.waitForReady(waitInterval, waitInitial)

    def get(self):
        """
        Returns the current position of the motor.

        Returns:
            float: Current position as reported by the device.
        """
        return self._get()
    
    def stop(self):
        """
        Stops the motor's motion.
        """
        self._stop()
    
    def isBusy(self):
        """
        Returns the last known busy/idle status of the motor.

        Returns:
            bool: True if marked as busy, False otherwise.
        """
        return self._busy
    
    def isAlive(self):
        """
        Returns the last known alive/dead status of the motor.

        Returns:
            bool: True if marked as alive, False otherwise.
        """
        return self._alive
    
    def settingsWidget(self, parent=None):
        """
        Returns a settings dialog for the device.

        Intended to be overridden in subclasses.

        Args:
            parent (QWidget, optional): Parent widget for the dialog.

        Returns:
            QDialog: Settings dialog (to be specified in subclasses).
        """
        return QtWidgets.QDialog()
    

class SingleMotorDummy(SingleMotorInterface):
    """
    Dummy implementation of a single-axis motor interface for simulating and testing the behavior of `SingleMotorInterface`.

    This class simulates motor behavior by providing time-based position updates.
    The methods `_set(value)`, `_get()`, `_stop()`, and `_isBusy()` override their counterparts in `SingleMotorInterface`.

    Attributes:
        _delay (float): Current simulated position of the motor.
        _duration (float): Duration (in seconds) of a simulated move operation.
        _timing (float or None): Start time of the current move, or None if idle.
        _target (float): Target position of the current move.
        _before (float): Position before the current move started.

    Methods:
        _set(value): Starts a simulated move to the target position.
        _get(): Returns the current simulated position, updated based on elapsed time.
        _stop(): Stops the simulated motion at the current position.
        _isBusy(): Returns True if the simulated motor is in motion.
    """

    def __init__(self):
        """
        Initializes the `SingleMotorDummy` instance.

        Sets parameters and starts the background thread by calling `QtCore.QThread.start()` on this instance.
        Duration of the simmulated move operation is set to 1 second by default.
        """
        super().__init__()
        self._delay = 0
        self._duration = 1
        self._timing = None
        self._target = 0
        self._before = 0
        self._error = False  # Newly added to simulate error state
        self.start()

    # def _time(self):
    #     """
    #     Records the current time.

    #     Returns:
    #         float: Current time in seconds with microsecond precision.
    #     """
    #     dt = datetime.now()
    #     return dt.minute * 60 + dt.second + dt.microsecond * 1e-6
    
    def _time(self):
        """
        Returns a monotonic time in seconds with high precision.
        """
        return time.perf_counter()


    def _set(self, delay):
        """
        Sets a new target position and records the starting position and time of the motion.

        Args:
            delay (float): Target position to move to.
        """
        self._before = self.get()
        self._timing = self._time()
        self._target = delay

    def _get(self):
        """
        Returns the current simulated position based on elapsed time.

        Returns:
            float: Linearly interpolated position since the start of motion.
        """
        if self._error:     # Newly added
            raise TimeoutError("Device is not responding")
        if self._timing is None:
            return self._delay
        time = self._time()
        if time - self._timing < self._duration:
            self._delay = self._before + (self._target - self._before) / self._duration * (time - self._timing)
        else:
            self._delay = self._target
        return self._delay

    def _stop(self):
        """
        Stops the motion and holds its current position.
        """
        self._timing = None
        self._delay = self.get()

    def _isBusy(self):
        """
        Return whether the dummy motor is currently moving.

        Returns:
            bool: True if the motor is moving, False otherwise.
        """
        if self._timing is None:
            return False
        return self._time() - self._timing < self._duration
    

    


