import time

from lys.Qt import QtCore
from lys_instr import MultiSwitchInterface
from lys_instr.dummy.MultiMotor import _OptionalPanel

class _LevelInfo(QtCore.QObject):
    def __init__(self, state, interval):
        super().__init__()
        self._state = state
        self._target = None
        self._interval = interval
        self.error = False

    def set(self, state):
        self._target = state
        self._timing = time.perf_counter()

    def _update(self):
        if self._target is None:
            return
        if time.perf_counter() - self._timing >= self._interval:
            self._state = self._target
            self._target = None

    @property
    def state(self):
        self._update()
        return self._state

    @property
    def busy(self):
        self._update()
        return self._target is not None
    

class MultiSwitchDummy(MultiSwitchInterface):
    def __init__(self, *axisNamesAll, levelNames=['OFF', 'LOW', 'MEDIUM', 'HIGH'], interval=0.1, **kwargs):
        super().__init__(levelNames, *axisNamesAll, **kwargs)
        self._data = {name: _LevelInfo(levelNames[0], interval) for name in self.nameList}
        self.start()

    def _set(self, **target):
        for name, d in self._data.items():
            if name in target:
                d.set(target[name])

    def _get(self):
        return {name: d.state for name, d in self._data.items()}
    
    def _isBusy(self):
        return {name: d.busy for name, d in self._data.items()}

    def _isAlive(self):
        return {name: not d.error for name, d in self._data.items()}

    def settingsWidget(self):
        return _OptionalPanel(self)
    