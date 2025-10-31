from lys.Qt import QtCore
from .Utilities import preciseSleep


def lock(func):
    """
    Decorator to ensure thread-safe execution of a method using a QMutex.

    This decorator acquires the instance's ``_mutex`` before executing the decorated method, ensuring that only one thread can execute the method at a time.

    Args:
        func (callable): The method to be decorated.

    Returns:
        callable: The wrapped method with mutex locking.
    """
    def wrapper(self, *args, **kwargs):
        with QtCore.QMutexLocker(self._mutex):
            return func(self, *args, **kwargs)
    return wrapper


class HardwareInterface(QtCore.QThread):
    """
    Abstract base class for hardware interfaces with background monitoring.

    This class provides background thread management and a standard structure for device state monitoring. 
    Each subclass represents a hardware device and runs its own monitoring thread. 
    The thread periodically calls ``_loadState()`` to poll and update device-specific state information.
    The monitoring thread can be stopped by calling the instance's ``kill()`` method, or all threads can be stopped using the ``killAll()`` class method. 
    
    Subclasses must implement ``_loadState()`` to provide device-specific behavior.
    """

    __list = []

    def __init__(self, interval=0.1, **kwargs):
        """
        Initialize the hardware interface.

        Register the device instance and append it to the internal instance list (``__list``).

        Args:
            interval (float, optional): Time interval (in seconds) between successive state polls. Defaults to 0.1.
            **kwargs: Additional keyword arguments passed to ``QtCore.QThread``.
        """
        super().__init__(**kwargs)
        self.__interval = interval
        self.__stopped = False
        self.__mutex = QtCore.QMutex()
        HardwareInterface.__list.append(self)

    def run(self):
        """
        Override ``QtCore.QThread.run()`` to define the background execution loop for a device instance.
        
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
        Stop the monitoring thread for this device instance.

        This method sets the internal stop flag under the mutex so the running thread will exit its loop and terminate cleanly.
        """
        with QtCore.QMutexLocker(self.__mutex):
            self.__stopped = True

    def _loadState(self):
        """
        Poll and update the current device state.

        Subclasses should override this method to implement device-specific polling and state-update logic.
        """
        pass

    @classmethod
    def killAll(cls):
        """
        Stop all active monitoring threads for instances of this class.

        This method calls ``kill()`` on each registered device instance and clears the internal instance list ``__list``.
        """
        for h in cls.__list:
            h.kill()
        cls.__list = []
