from datetime import datetime
from re import I
import time
import os
import numpy as np

from lys.Qt import QtCore, QtWidgets
from .Interfaces import HardwareInterface


class StageInterface(HardwareInterface):
    # implement _set, _get, _isBusy, _stop is required.
    valueSet = QtCore.pyqtSignal(dict)          # Difference from SingleMotor: _value is an absolute value while _delay is a relatie one
    valueChanged = QtCore.pyqtSignal(dict)
    stateChanged = QtCore.pyqtSignal(bool)

    def __init__(self, n, precision=1e-5, names=["stage_x", "stage_y", "stage_z", "stage_alpha", "stage_beta", "stage_gamma"], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prec = precision
        self._value = np.zeros((n,)).astype(float)
        self._names = names[:n]
        self._busy = False

    def _loadState(self):
        val = self._get()
        if (np.abs(np.array(self._value) - np.array(val)) > self._prec).any():
            self._value = val
            self.valueChanged.emit({name: pos for name, pos in zip(self._names, val)})

        busy = self._isBusy()
        if self._busy != busy:
            self._busy = busy
            self.stateChanged.emit(busy)

    def waitForReady(self, interval=0.1):
        while(True):
            if self.isBusy():
                time.sleep(interval)
            else:
                return True

    def set(self, value, wait=False, waitInterval=0.1):
        self._set(value)
        self._busy = True
        self.stateChanged.emit(True)
        if wait:
            self.waitForReady(waitInterval)
        self.valueSet.emit({name: pos for name, pos in zip(self._names, value) if not (pos is None or np.isnan(pos))})  # Ignore empty entries

    def get(self, axis=None, withName=False):
        val = self._get()
        if axis is None:
            return {name: pos for name, pos in zip(self._names, val)} if withName else np.array(val)
        else:                                   # Specify the axis number?
            return {self._names[axis]: val[axis]} if withName else val[axis]

    def stop(self):
        self._stop()

    def isBusy(self):
        return self._busy

    def numberOfAxis(self):
        return len(self._value)

    def getNames(self):
        return self._names

    def getScans(self):             # Provide per-axis control
        return {n: SingleAxisStage(self, i, len(self._names)) for i, n in enumerate(self._names)}       # axis name: f(axis index) pairs


class SingleAxisStage(QtCore.QObject):          # a logical part of StageInterface / a convenient wrapper around StageInterface
    def __init__(self, obj, axis, n):
        self._obj = obj                         # obj is the StageInterface object
        self._axis = axis
        self._naxis = n

    def set(self, value, *args, **kwargs):
        val = [np.nan] * self._naxis
        val[self._axis] = float(value)
        self._obj.set(val, *args, **kwargs)     # Call back to the .set() of StageInterface

    def get(self):
        return self._obj.get(self._axis)        # Call back to the .get() of StageInterface 


class StageDummy(StageInterface):
    def __init__(self):                 # No need to define the duration? The duration is always 4 seconds by default?
        super().__init__(6)
        self._value = np.array([0, 0, 0, 0, 0, 0], dtype=float)     # Equivalent to _delay in the SingleMotor.py
        # self._duration = 4
        self.__time = None
        self._target = None
        self._before = 0                # Why is not None?
        self.start()

    def _time(self):
        return datetime.now().minute * 60 + datetime.now().second

    def _set(self, value):
        self._before = self.get()
        self.__time = self._time()
        self._target = np.array(value, dtype=float)

    def _get(self):
        if self.__time is None:
            return self._value
        time = self._time()
        i = np.invert(np.isnan(self._target))           # Axis to be controlled
        if time - self.__time < 4:
            self._value[i] = (self._before + (self._target - self._before) / 4 * (time - self.__time))[i]
        # if time - self.__time < self._duration:
            # self._value[i] = (self._before + (self._target - self._before) / self._duration * (time - self.__time))[i]
        else:
            self._value[i] = self._target[i]
        return np.array(self._value)

    def _stop(self):
        self.__time = None
        self._value = self.get()

    def _isBusy(self):
        if self.__time is None:
            return False
        return self._time() - self.__time < 4


class StageGUI(QtWidgets.QGroupBox):
    def __init__(self, obj, title):
        super().__init__(title)
        os.makedirs(".lys/PythonHardwares/Stage", exist_ok=True)
        self._posPath = ".lys/PythonHardwares/Stage/poslist.lst"
        if os.path.exists(self._posPath):
            with open(self._posPath, 'r') as f:
                txt = f.read()
                self._poslist = eval(txt)
        else:
            self._poslist = []
        self._obj = obj
        self.__initlayout(obj)
        self._obj.valueChanged.connect(self._setValue)
        self._obj.stateChanged.connect(self._stateChanged)
        self._setValue(self._obj.get(withName=True))
        self._updateMemory()

    def _setValue(self, value):
        for key in value.keys():
            self._present[key].setValue(value[key])

    def __initlayout(self, obj):
        self.setStyleSheet("QLineEdit {font-size: 14pt}"
                           "QDoubleSpinBox {font-size: 14pt}"
                           "QPushButton {font-size: 14pt}"
                           "QLabel {font-size: 12pt}")

        self._present = {obj.getNames()[i]: QtWidgets.QDoubleSpinBox() for i in range(obj.numberOfAxis())}
        for p in self._present.values():
            p.setRange(-np.inf, np.inf)
            p.setReadOnly(True)
            p.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
            p.setDecimals(4)

        self._target = [QtWidgets.QLineEdit() for _ in range(obj.numberOfAxis())]
        self._jog1 = [QtWidgets.QPushButton("<", clicked=self._prev) for _ in range(obj.numberOfAxis())]
        self._jog2 = [QtWidgets.QPushButton(">", clicked=self._next) for _ in range(obj.numberOfAxis())]
        self._jogLen = QtWidgets.QDoubleSpinBox()
        self._jogLen.setRange(-np.inf, np.inf)
        self._jogLen.setDecimals(4)
        self._execute = QtWidgets.QPushButton('Go', clicked=self.__set)
        stop = QtWidgets.QPushButton('Stop', clicked=obj.stop)

        self._list = QtWidgets.QTreeWidget()
        self._list.setColumnCount(2)
        self._list.setHeaderLabels(["Name", "Value"])
        self._list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        save = QtWidgets.QPushButton("Save", clicked=self._save)
        load = QtWidgets.QPushButton("Move", clicked=self._load)
        delete = QtWidgets.QPushButton("Delete", clicked=self._delete)

        gl = QtWidgets.QGridLayout()
        gl.addWidget(QtWidgets.QLabel('Present'), 0, 1)
        gl.addWidget(QtWidgets.QLabel('Move to'), 0, 2)
        gl.addWidget(QtWidgets.QLabel('Jog'), 0, 3)
        gl.addWidget(self._jogLen, 0, 4)
        gl.addWidget(QtWidgets.QLabel('Memory'), 0, 5)
        for i, name in enumerate(obj.getNames()):
            label = QtWidgets.QLabel(name.replace("stage_", ""))
            label.setAlignment(QtCore.Qt.AlignCenter)
            gl.addWidget(label, 1 + i, 0)
            gl.addWidget(self._present[name], 1 + i, 1)
            gl.addWidget(self._target[i], 1 + i, 2)
            gl.addWidget(self._jog1[i], 1 + i, 3)
            gl.addWidget(self._jog2[i], 1 + i, 4)
        gl.addWidget(self._list, 1, 5, obj.numberOfAxis(), 3)
        gl.addWidget(stop, 1 + len(self._present), 1)
        gl.addWidget(self._execute, 1 + len(self._present), 2)
        gl.addWidget(save, 1 + len(self._present), 5)
        gl.addWidget(load, 1 + len(self._present), 6)
        gl.addWidget(delete, 1 + len(self._present), 7)

#        gl.setColumnStretch(1, 0.2)
#        gl.setColumnStretch(2, 0.1)
#        gl.setColumnStretch(3, 0.1)
#        gl.setColumnStretch(4, 0.1)
#        gl.setColumnStretch(5, 0.4 / 3)
#        gl.setColumnStretch(6, 0.4 / 3)
#        gl.setColumnStretch(7, 0.4 / 3)

        self.setLayout(gl)

    def __set(self):
        value = []
        for t in self._target:
            if t.text().isnumeric():
                value.append(float(t.text()))
            else:
                value.append(np.nan)
        self._obj.set(value)

    def _stateChanged(self, busy):
        self._execute.setEnabled(not busy)
        for w in self._jog1:
            w.setEnabled(not busy)
        for w in self._jog2:
            w.setEnabled(not busy)
        if busy:
            self._execute.setText('Moving')
        else:
            self._execute.setText('Go')

    def _next(self, i):
        i = self._jog2.index(self.sender())
        value = self._obj.get()
        value[i] = value[i] + self._jogLen.value()
        value[:i] = np.nan
        value[i + 1:] = np.nan
        self._obj.set(value)

    def _prev(self):
        i = self._jog1.index(self.sender())
        value = self._obj.get()
        value[i] = value[i] - self._jogLen.value()
        value[:i] = np.nan
        value[i + 1:] = np.nan
        self._obj.set(value)

    def _save(self):
        namelist = [name for name, position in self._poslist]
        i = 1
        while "Position" + str(i) in namelist:
            i += 1
        self._poslist.append(("Position" + str(i), list(self._obj.get())))
        with open(self._posPath, 'w') as f:
            print(str(self._poslist))
            f.write(str(self._poslist))
        self._updateMemory()

    def _load(self):
        removed = [i.text(1) for i in self._list.selectedItems()]
        if len(removed) != 0:
            self._obj.set(eval(removed[0]))

    def _delete(self):
        removed = [i.text(0) for i in self._list.selectedItems()]
        self._poslist = [item for item in self._poslist if item[0] not in removed]
        with open(self._posPath, 'w') as f:
            print(str(self._poslist))
            f.write(str(self._poslist))
        self._updateMemory()

    def _updateMemory(self):
        self._list.clear()
        for name, position in self._poslist:
            self._list.addTopLevelItem(QtWidgets.QTreeWidgetItem(self._list, [name, str(position)]))




if __name__ == '__main__':              # To Test the GUI run in the src\python: python -m fstem.lys_instr.GUI.SingleMotorGUI
    import sys
    # from pythonhardwares.PythonHardwares import SingleMotorDummy
    from lys.Qt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    dummy = StageDummy()
    gui = StageGUI(dummy, 'Multi-Motor Control')
    gui.show()
    sys.exit(app.exec_())