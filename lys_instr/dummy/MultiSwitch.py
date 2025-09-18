import numpy as np
import time

from lys_instr import MultiMotorInterface
from lys_instr.dummy.MultiMotor import _OptionalPanel
from lys.Qt import QtWidgets, QtCore


class MultiSwitchDummy(MultiMotorInterface):
    def __init__(self, *axisNamesAll, **kwargs):      
        super().__init__(*axisNamesAll, **kwargs)
        n = len(self.nameList)
        self.__position = np.zeros(n, dtype=bool)
        self.__timing = np.full(n, np.nan)
        self.__target = np.zeros(n, dtype=bool)
        self.__before = np.zeros(n, dtype=bool)
        self._switchInterval = 0.1
        self._error = np.full(n, False)
        self.start()

    def _time(self):
        return time.perf_counter()

    def _set(self, target):
        now = self._time()
        before = self.get()
        for i, name in enumerate(self.nameList):
            if name in target:
                self.__before[i] = before[name]
                self.__timing[i] = now
                self.__target[i] = bool(target[name])

    def _get(self):
        val = {}

        # When axes are dead
        for i, name in enumerate(self.nameList):
            self._info[name].alive = not self._error[i]

        # When axes are at rest
        if np.all(np.isnan(self.__timing)):
            for i, name in enumerate(self.nameList):
                val[name] = bool(self.__position[i])
            return val

        now = self._time()
        timeElapsed = now - self.__timing
        movingIndices = np.where(~np.isnan(self.__target) & ~np.isnan(self.__timing))[0]
        self.__position[movingIndices] = (self.__before[movingIndices] * (timeElapsed < self._switchInterval) + self.__target[movingIndices] * (timeElapsed >= self._switchInterval)).astype(bool)

        finishedIndices = movingIndices[timeElapsed[movingIndices] >= self._switchInterval]
        self.__timing[finishedIndices] = np.nan
        self.__target[finishedIndices] = np.nan

        for i, name in enumerate(self.nameList):
            val[name] = bool(self.__position[i])
        return val

    def _stop(self):
        self.__timing = np.full(len(self.nameList), np.nan)

    def _isBusy(self):
        bs = (~np.isnan(self.__timing) & ~np.isnan(self.__target)).astype(bool)
        return {name: bs[i] for i, name in enumerate(self.nameList)}

    def _isAlive(self):
        return {name: not self._error[i] for i, name in enumerate(self.nameList)}

    def settingsWidget(self):
        return _OptionalPanel(self)
    