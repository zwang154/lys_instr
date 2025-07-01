import time
from lys.Qt import QtCore


def preciseSleep(sleepTime):
    """
    Sleeps for the specified interval (in seconds) with improved temporal precision.
    Avoids overshoot by busy-waiting for the last ~0.5 ms.
    """
    wakeTime = time.perf_counter() + sleepTime
    while True:
        now = time.perf_counter()
        remaining = wakeTime - now
        if remaining > 0.001:  # sleep if more than 1 ms left
            time.sleep(remaining - 0.0005)  # leave a small margin
        elif remaining > 0:
            pass  # busy-wait for the last microseconds
        else:
            break


class HardwareInterface(QtCore.QThread):
    """
    Abstract interface for hardware devices.
    
    Provides background thread management and a standard structure for device state monitoring.
    Each subclass represents a hardware device and runs its own monitoring thread.
    The thread periodically calls `_loadState()` to poll and update device-specific state information, and checks the device's alive status using `isAlive()`.
    If the result of `isAlive()` changes, the internal status is updated and the `aliveStateChanged` signal on the thread is emitted with the new status.
    The monitoring thread can be stopped by calling the instance's `kill()` method, or all threads can be stopped using the `killAll()` class method.

    Subclasses should override the following protected methods to provide device-specific behavior:
        _loadState()

    Signals:
        aliveStateChanged (bool): Emitted when the alive status of the device changes.

    Args:
        interval (float, optional): Time interval (in seconds) between successive state polls. Default is 0.1.

    Public Methods:
        isAlive(): Returns True if the device is responsive (to be overridden in subclasses).
        kill(): Stops the monitoring thread for this device instance.
        killAll(): Stops all active monitoring threads for devices instantiated from this class.
    
    Private Methods
        _loadState(): Polls and updates the current value and status of the device (to be overridden in subclasses).
    """

    __list = []

    # aliveStateChanged = QtCore.pyqtSignal(bool)
    aliveStateChanged = QtCore.pyqtSignal(list)

    def __init__(self, interval=0.1, **kwargs):          # *args is not needed for QThread; **kwargs passes all other arguments
        """
        Initializes the class, sets up internal tracking, and registers the device instance for monitoring.
        
        It also appends the instance to the internal list.

        Args:
            interval (float, optional): Time interval (in seconds) between `_loadState()` calls. Default is 0.1.
        """
        super().__init__(**kwargs)                              # **kwargs is exactly the same here as above
        self.__interval = interval
        self.__stopped = False
        self.__mutex = QtCore.QMutex()
        self.__alive = True
        HardwareInterface.__list.append(self)

    def run(self):
        """
        Overrides `QThread.run()` to define the background execution loop for a device instance.
        
        This method is executed automatically when `start()` is called, which is typically done in subclasses.
        Within the loop, it repeatedly calls `_loadState()` and `isAlive()` at the specified time interval.
        If the result of `isAlive()` changes, the `aliveStateChanged` signal is emitted with the new status.
        The loop continues until `kill()` is called on the instance.
        """
        while(True):
            if self.__stopped:
                return
            self._loadState()
            alive = self.isAlive()
            # alive = self.isAlive().all()
            if self.__alive != alive:
                self.__alive = alive
                self.aliveStateChanged.emit(self.__alive)
            preciseSleep(self.__interval)

    def kill(self):
        """
        Stops the monitoring thread for the device by calling it on its instance.
        """
        with QtCore.QMutexLocker(self.__mutex):
            self.__stopped = True

    def isAlive(self):
        """
        Returns the alive status of the device instance. 
        
        Intended to be overridden in subclasses.

        Returns:
            bool: True if the device is alive, otherwise False.
        """
        return True

    def _loadState(self):
        """
        Polls and updates the current device state.

        Intended to be overridden in subclasses.
        """
        pass

    @classmethod
    def killAll(cls):
        """
        Stops all active monitoring threads for devices instantiated from this class by calling their `kill()` method, and then clears the internal instance list.
        """
        for h in cls.__list:
            h.kill()
        cls.__list = []
