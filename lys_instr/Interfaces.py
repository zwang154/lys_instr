from lys.Qt import QtCore
from .Utilities import preciseSleep


def lock(func):
    """
    Decorator to ensure thread-safe execution of a method using a QMutex.

    Acquires the instance's ``_mutex`` before executing the decorated method, ensuring that only one thread can execute the method at a time.

    Parameters
    ----------
    func : callable
        The method to be decorated.

    Returns
    -------
    callable
        The wrapped method with mutex locking.
    """
    def wrapper(self, *args, **kwargs):
        with QtCore.QMutexLocker(self._mutex):
            # func(self, *args, **kwargs)
            return func(self, *args, **kwargs)
    return wrapper


class HardwareInterface(QtCore.QThread):
    """
    Abstract base class for hardware interfaces with background monitoring.

    This class provides background thread management and a standard structure for device state monitoring.
    Each subclass represents a hardware device and runs its own monitoring thread.
    The thread periodically calls ``_loadState()`` to poll and update device-specific state information.
    The monitoring thread can be stopped by calling the instance's ``kill()`` method, or all threads can be stopped using the ``killAll()`` class method.

    ``_loadState()`` must be implemented in subclasses to provide device-specific behavior.

    Parameters
    ----------
    interval : float, optional
        Time interval (in seconds) between successive state polls. Default is 0.1.
    **kwargs
        Additional keyword arguments passed to ``QtCore.QThread``.
    """

    __list = []

    def __init__(self, interval=0.1, **kwargs):
        """
        Initializes the hardware interface.
        
        It registers the device instance and appends the instance to the internal instance ``__list``.
        """
        super().__init__(**kwargs)
        self.__interval = interval
        self.__stopped = False
        self.__mutex = QtCore.QMutex()
        HardwareInterface.__list.append(self)

    def run(self):
        """
        Overrides ``QtCore.QThread.run()`` to define the background execution loop for a device instance.
        
        This method is executed automatically when ``start()`` is called, which is typically done in subclasses.
        It repeatedly calls ``_loadState()`` at the specified interval until ``kill()`` is called.
        """
        while(True):
            if self.__stopped:
                return
            self._loadState()
            preciseSleep(self.__interval)

    def kill(self):
        """
        Stops the monitoring thread for this device instance.
        """
        with QtCore.QMutexLocker(self.__mutex):
            self.__stopped = True

    def _loadState(self):
        """
        Polls and updates the current device state.

        This method is intended to be overridden in subclasses.
        """
        pass

    @classmethod
    def killAll(cls):
        """
        Stops all active monitoring threads for devices instantiated from this class
         
        It calls the ``kill()`` method on each device instance on the internal instance ``__list`` and clears the list.
        """
        for h in cls.__list:
            h.kill()
        cls.__list = []
