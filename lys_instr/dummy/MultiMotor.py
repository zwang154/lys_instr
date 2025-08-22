import numpy as np
import time

from lys_instr import MultiMotorInterface


class MultiMotorDummy(MultiMotorInterface):
    """
    Dummy implementation of ``MultiMotorInterface``.

    This class simulates a multi-axis motor controller, including axis positions, busy/alive state management, and per-axis error injection for testing purposes.
    """
    def __init__(self, *axisNamesAll, **kwargs):
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
        n = len(self.nameList)
        self.__position = np.zeros(n)
        self.__timing = np.full(n, np.nan)
        self.__target = np.full(n, np.nan)
        self.__before = np.zeros(n)
        self.__signs = np.zeros(n)
        self._speed = 0.2
        self._error = np.full(n, False)
        self.start()

    def _time(self):
        """
        Returns the current monotonic time in seconds with high precision.

        Returns:
            float: Monotonic time in seconds.
        """
        return time.perf_counter()

    def _set(self, target):
        """
        Sets target positions for the specified axes.

        Only the axes provided in the ``target`` dictionary will be updated; other axes remain unchanged.

        Args:
            target (dict): Mapping of axis names to their target positions.
        """
        self.__before = self.get(type=np.ndarray)
        self.__timing = np.full(len(self.nameList), self._time())
        self.__target = np.array([target[name] if name in target else np.nan for name in self.nameList])

    def _get(self):
        """
        Gets the current positions of all axes, updating the alive states.

        For each axis, if an error is simulated, the axis is marked as not alive and its value is set to np.nan.
        Otherwise, the current position is returned.

        Returns:
            dict: Mapping of axis names (str) to their current positions (float).
        """
        val = {}

        # When axes are dead
        for i, name in enumerate(self.nameList):
            if self._error[i]:
                self._info[name].alive = False
            else:
                self._info[name].alive = True
        
        # When axes are at rest
        if np.all(np.isnan(self.__timing)):
            for i, name in enumerate(self.nameList):
                if name not in val:
                    val[name] = self.__position[i]
            return val

        # When axes are moving
        self.__signs = np.sign(self.__target - self.__before)
        now = self._time()
        movingIndices = np.where(~np.isnan(self.__target) & ~np.isnan(self.__timing))[0]
        self.__position[movingIndices] = self.__before[movingIndices] + self.__signs[movingIndices] * self._speed * (now - self.__timing[movingIndices])
        for i in movingIndices:
            if np.sign(self.__position - self.__target)[i] == self.__signs[i]:
                self.__position[i] = self.__target[i]
                self.__timing[i] = np.nan
        for i, name in enumerate(self.nameList):
            if name not in val:
                val[name] = float(self.__position[i])
        return val

    def _stop(self):
        """
        Stops all axes in the dummy motor by clearing their timing information.
        """
        self.__timing = np.full(len(self.nameList), np.nan)

    def _isBusy(self):
        """
        Gets the busy state of all axes in the simulated multi-axis motor.

        Returns:
            dict: Mapping of axis names (str) to busy states (bool).
        """
        bs = (~np.isnan(self.__timing) & ~np.isnan(self.__target)).astype(bool)
        return {name: bs[i] for i, name in enumerate(self.nameList)}
    
    def _isAlive(self):
        """
        Gets the alive state of all axes in the simulated multi-axis motor.

        Returns:
            dict: Mapping of axis names (str) to alive states (bool).
        """
        return {name: not self._error[i] for i, name in enumerate(self.nameList)}



