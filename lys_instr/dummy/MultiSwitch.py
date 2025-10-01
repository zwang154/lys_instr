import numpy as np
import time

from lys_instr import MultiControllerInterface
from lys_instr.dummy.MultiMotor import _OptionalPanel
from enum import Enum


def Level(levelNames):
    return Enum('Level', {name: i for i, name in enumerate(levelNames)})


class MultiSwitchDummy(MultiControllerInterface):
    def __init__(self, *axisNamesAll, levelNames=['OFF', 'LOW', 'MEDIUM', 'HIGH'], **kwargs):
        super().__init__(*axisNamesAll, **kwargs)
        n = len(self.nameList)
        self._level = Level(['NONE'] + levelNames)
        self.__state = [self._level(0) for _ in range(n)]
        self.__target = [self._level(0) for _ in range(n)]
        self.__before = [self._level(0) for _ in range(n)]
        self.__timing = np.full(n, np.nan)
        self._switchInterval = 0.1
        self._error = np.full(n, False)
        self.start()

    def _time(self):
        return time.perf_counter()

    def _set(self, **target):
        now = self._time()
        before = self.get()
        for i, name in enumerate(self.nameList):
            if name in target:
                self.__before[i] = before[name]
                self.__timing[i] = now
                self.__target[i] = target[name]

    def _get(self):
        val = {}

        # When axes are dead
        for i, name in enumerate(self.nameList):
            self._info[name].alive = not self._error[i]

        # When axes are at rest
        if np.all(np.isnan(self.__timing)):
            for i, name in enumerate(self.nameList):
                val[name] = self.__state[i]
            return val

        now = self._time()
        timeElapsed = now - self.__timing
        busyIndices = [i for i, (t, target) in enumerate(zip(self.__timing, self.__target)) if not np.isnan(t) and target.name != 'NONE']
        for i in busyIndices:
            if timeElapsed[i] < self._switchInterval:
                self.__state[i] = self.__before[i]
            else:
                self.__state[i] = self.__target[i]
                self.__timing[i] = np.nan
                self.__target[i] = self._level(0)

        for i, name in enumerate(self.nameList):
            val[name] = self.__state[i]
        return val

    def _isBusy(self):
        bs = [not np.isnan(t) and target.name != 'NONE' for t, target in zip(self.__timing, self.__target)]
        return {name: bs[i] for i, name in enumerate(self.nameList)}

    def _isAlive(self):
        return {name: not self._error[i] for i, name in enumerate(self.nameList)}

    def settingsWidget(self):
        """
        Returns a QWidget for optional settings.

        Returns:
            QtWidgets.QWidget: The optional settings panel.
        """
        return _OptionalPanel(self)
    