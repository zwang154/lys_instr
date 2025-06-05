from datetime import datetime
import time
import numpy as np

# from lys.Qt import QtCore, QtWidgets, QtGui
from .Interfaces import HardwareInterface


class SingleMotorInterface(HardwareInterface):
    """
    implement _set, _get, _isBusy, _stop, _alive is required.
    """
    # valueChanged = QtCore.pyqtSignal(float)
    # busyStateChanged = QtCore.pyqtSignal(bool)
    # aliveStateChanged = QtCore.pyqtSignal(bool)

    def __init__(self, precision=1e-5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prec = precision
        self._value = 0
        self._busy = False
        self._alive = True

    def _loadState(self):
        try:
            val = self._get()
            if abs(self._value - val) > self._prec:
                self._value = val
                # self.valueChanged.emit(val)

            busy = self._isBusy()
            if self._busy != busy:
                self._busy = busy
                # self.busyStateChanged.emit(busy)

            if not self._alive:
                alive = True
                self._alive = alive
                # self.aliveStateChanged.emit(alive)

        except (TimeoutError, IOError):
            alive = False
            if self._alive != alive:
                self._alive = alive
                # self.aliveStateChanged.emit(alive)

    def waitForReady(self, interval=0.1, initial=1):
        time.sleep(initial)
        while True:
            if self.isBusy():
                time.sleep(interval)
            else:
                return True

    def set(self, value, wait=False, waitInterval=0.1, waitInitial=1):
        self._busy = True
        self._set(value)
        # self.busyStateChanged.emit(True)
        if wait:
            self.waitForReady(waitInterval, waitInitial)

    def get(self):
        return self._get()
    
    def stop(self):
        self._stop()
    
    def isBusy(self):
        return self._busy
    
    def isAlive(self):
        return self._alive
    
    # def settingWidget(self, parent=None):
    #     return QtWidgets.QDialog()
    

class SingleMotorDummy(SingleMotorInterface):
    def __init__(self):
        super().__init__()
        self._delay = 0
        self._duration = 1
        self._timing = None
        self._target = 0
        self._before = 0
        self.start()

    # def _time(self):
    #     return datetime.now().minute * 60 + datetime.now().second

    def _time(self):
        dt = datetime.now()
        return dt.minute * 60 + dt.second + dt.microsecond * 1e-6

    def _set(self, delay):
        self._before = self.get()
        self._timing = self._time()
        self._target = delay

    def _get(self):
        if self._timing is None:
            return self._delay
        time = self._time()
        if time - self._timing < self._duration:
            self._delay = self._before + (self._target - self._before) / self._duration * (time - self._timing)
        else:
            self._delay = self._target
        return self._delay

    def _stop(self):
        self._timing = None
        self._delay = self.get()

    def _isBusy(self):
        if self._timing is None:
            return False
        return self._time() - self._timing < self._duration
    
    # def settingWidget(self, parent=None):
    #     return _SettingDialog(self, parent)
    

    



    


