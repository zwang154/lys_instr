import numpy as np
import time

from lys.Qt import QtCore, QtWidgets
from .Interfaces import HardwareInterface

class MultiMotorInterface(HardwareInterface):
    
    valueSet = QtCore.pyqtSignal(dict)              # dict of float
    valueChanged = QtCore.pyqtSignal(dict)          # dict of float
    busyStateChanged = QtCore.pyqtSignal(dict)      # dict of bool

    def __init__(self, *axisNamesAll, precision=1e-5, **kwargs):   # **kwargs: passed to QThread only
        super().__init__(**kwargs)
        self._precision = precision
        self._nameList = axisNamesAll
        self._valueList = np.zeros(len(axisNamesAll))                     # It is better to use np.nan than 0.0? Maybe not.
        self._busyList = [False] * len(axisNamesAll)
        self._aliveList = [True] * len(axisNamesAll)
        self._offsetList = np.zeros(len(axisNamesAll))

    def _loadState(self):                                                               # Avoid calling public methods in private methods?
        try:
            vl = self._get()
            if (np.abs(np.array(self._valueList) - np.array(vl)) > self._precision).any():
                self._valueList = vl
                self.valueChanged.emit({name: value for name, value in zip(self._nameList, vl)})

            bs = self._isBusy()
            if (self._busyList != bs).any():
                self._busyList = bs
                self.busyStateChanged.emit({name: busy for name, busy in zip(self._nameList, bs)})

        except (TimeoutError, IOError) as e:
            idx = np.isnan(vl)
            self._aliveList[idx] = False
            self.aliveStateChanged.emit(self._aliveList)
            self._busyList[idx] = False
         
    def set(self, *args, wait=False, waitInterval=0.1, **kwargs):       # Called by SingleMotor and MultiMotorGUI (_nega(), _posi(), _load(), _setMoveToValue())

        target = np.full(len(self._nameList), np.nan)
        if args:
            if isinstance(args[0], dict):                               # Accepts a dict with sepcified axes 
                items = args[0].items()
                for name, value in items:
                    if name in self._nameList:
                        idx = self._nameList.index(name)
                        target[idx] = value
                        self._busyList[idx] = True
            elif isinstance(args[0], (list, tuple, np.ndarray)):        # Only accepts list/tuple/array with full axes
                values = np.array(args[0])
                if len(values) != len(self._nameList):
                    raise ValueError("Length of values does not match number of axes")
                target[:] = values
                self._busyList[:] = True
            elif len(args) == len(self._nameList):                      # Accepts multiple arguments with full axes        
                target[:] = args
                self._busyList[:] = True
            else:
                raise TypeError("Unsupported argument type or wrong number of values for set(): {}".format(args))
        else:
            for name, value in kwargs.items():
                if name in self._nameList:
                    idx = self._nameList.index(name)
                    target[idx] = value
                    self._busyList[idx] = True

        self.busyStateChanged.emit({name: busy for name, busy in zip(self._nameList, self._busyList)})
        self._set(target)
        self.valueSet.emit({name: pos for name, pos in zip(self._nameList, target) if not np.isnan(pos)})

        if wait:
            self.waitForReady(waitInterval)

    def waitForReady(self, interval=0.1):
        while True:
            if self.isBusy().any():
                time.sleep(interval)
            else:
                return True

    def get(self, axis=None, withName=False):   # Called by SingleMotor and MultiMotorDummy (_nega(), _positive(), _save())
        valueList = self._get()
        if axis is None:
            return {name: value for name, value in zip(self._nameList, valueList)} if withName else np.array(valueList)
        else:
            idx = self._nameList.index(axis) if isinstance(axis, str) else axis
            return {self._nameList[idx]: valueList[idx]} if withName else valueList[idx]
        
    def stop(self):     # Called by MultiMotorGUI (_interrupt())
        self._stop()

    def isBusy(self):   # Called by waitForReady(), MultiMotorGUI (_aliveStateChanged())
        return self._busyList
    
    def isAlive(self):  # Called by MultiMotorGUI (__initLayout(), _busyStateChanged(), _toggleAlive(), _setAliveState())
        """
        Returns the last known alive/dead status of the motor.

        Returns:
            bool: True if marked as alive, False otherwise.
        """
        return self._aliveList

    def setNamesAll(self, nameList):
        self._nameList = list(nameList)

    def getNamesAll(self):
        return self._nameList
    
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




class SettableMultiMotor:
    def __init__(self, motor, axisNamesSettable=None):
        self._motor = motor
        self._allNames = self._motor.getNamesAll()
        self._settableNameList = list(axisNamesSettable) if axisNamesSettable else list(self._allNames)
        self._SettableIndices = [self._allNames.index(name) for name in self._settableNameList]

    def __getattr__(self, name):
        return getattr(self._motor, name)

    def set(self, *args, **kwargs):
        if args:
            if isinstance(args[0], dict):
                filtered = {name: value for name, value in args[0].items() if name in self._settableNameList}
                self._motor.set(filtered)
            elif isinstance(args[0], (list, tuple, np.ndarray)):
                if len(args[0]) != len(self._settableNameList):
                    raise ValueError(f"Length of values ({len(args[0])}) does not match number of Settable axes ({len(self._settableNameList)})")
                filtered = dict(zip(self._settableNameList, args[0]))
                self._motor.set(filtered)
            elif len(args) == len(self._settableNameList):
                filtered = dict(zip(self._settableNameList, args))
                self._motor.set(filtered)
            else:
                raise TypeError(f"Unsupported argument type or wrong number of values for set(): {args}")
        else:
            filtered = {name: value for name, value in kwargs.items() if name in self._settableNameList}
            self._motor.set(**filtered)

    def setNamesSettable(self, settableNameList):
        self._settableNameList = list(settableNameList)     # Use more general *args?

    def getNamesSettable(self):
        return self._settableNameList
    

class JoggableMultiMotor:
    def __init__(self, motor, axisNamesJoggable=None):
        self._motor = motor
        self._joggableNameList = axisNamesJoggable if axisNamesJoggable is not None else self._motor.getNamesAll()

    def __getattr__(self, name):
        return getattr(self._motor, name)

    def setNamesJoggable(self, joggableNameList):
        self._joggableNameList = list(joggableNameList)     # Use more general *args?
    
    def getNamesJoggable(self):
        return self._joggableNameList


class OffsettableMultiMotor:
    def __init__(self, motor, axisNamesOffsettable=None):
        self._motor = motor
        self._offsettableNameList = axisNamesOffsettable if axisNamesOffsettable is not None else self._motor.getNamesAll()

    def __getattr__(self, name):
        return getattr(self._motor, name)

    def setOffset(self, *args, toCurrent=True, **kwargs):
        if toCurrent:
            self._motor._offsetList = self._motor._get()
        self._motor.valueChanged.emit({name: value for name, value in zip(self._motor._nameList, self._motor._valueList)})  # Emit the changed values with offset applied

    def clearOffset(self):
        self._motor._offsetList = np.zeros(len(self._motor._nameList))
        self._motor.valueChanged.emit({name: value for name, value in zip(self._motor._nameList, self._motor._valueList)})  # Emit the changed values with offset applied

    def setNamesOffsettable(self, offsettableNameList):
        self._offsettableNameList = list(offsettableNameList)

    def getNamesOffsettable(self):
        return self._offsettableNameList


class MultiMotorDummy(MultiMotorInterface):
    def __init__(self, *axisNamesAll, **kwargs):
        super().__init__(*axisNamesAll, **kwargs)
        # self._position = np.zeros(len(self._nameList))
        # self._position = np.round(np.random.uniform(-5, 5, len(self._nameList)), 1)     # Random initial positions for testing
        self._position = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        self._duration = 5
        self._speed = 0.2
        self.__timing = np.full(len(self._nameList), np.nan)
        self.__target = np.full(len(self._nameList), np.nan)
        self.__before = 0       # np.full(len(self._nameList), np.nan)
        self.__signs = 0        # np.full(len(self._nameList), np.nan)
        self.__error = False
        self.start()

    def _time(self):
        """
        Returns a monotonic time in seconds with high precision.
        """
        return time.perf_counter()
    
    def _set(self, target):                       
        self.__before = self.get()
        self.__timing = np.full(len(self._nameList), self._time())
        self.__target = target  # target as an np.ndarray

    def _get(self):
        # Dead
        if self.__error:
            raise TimeoutError('Device is not responding')
        
        # At rest
        if np.all(np.isnan(self.__timing)):
            return self._position
        
        # Moving
        self.__signs = np.sign(self.__target - self.__before)
        now = self._time()
        movingIndices = np.where(~np.isnan(self.__target) & ~np.isnan(self.__timing))[0]
        self._position[movingIndices] = self.__before[movingIndices] + self.__signs[movingIndices] * self._speed * (now - self.__timing[movingIndices])
        for i in movingIndices:
            if np.sign(self._position - self.__target)[i] == self.__signs[i]:
                self._position[i] = self.__target[i]
                self.__timing[i] = np.nan
        return np.array(self._position)         # np.array() is needed to avoid returning a view of the array

    def _stop(self):
        self.__timing = np.full(len(self._nameList), np.nan)
        self._position = self.get()
    
    def _isBusy(self):
        return (~np.isnan(self.__timing) & ~np.isnan(self.__target)).astype(bool)

    

    
    
    

