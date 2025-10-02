import os
import weakref

import numpy as np
from .MultiController import MultiControllerInterface
from lys.Qt import QtCore


class OffsettableMultiMotorInterface(MultiControllerInterface):
    """
    Add offset functionality for MultiMotor.
    """
    offsetChanged = QtCore.pyqtSignal()

    class offsetDict(dict):
        valueChanged = QtCore.pyqtSignal()

        def __init__(self, axesNames, parent):
            super().__init__({name: 0 for name in axesNames})
            self._parent = weakref.ref(parent)

        def __setitem__(self, key, value):
            super().__setitem__(key, value)
            self._parent().offsetChanged.emit()

    def __init__(self, *axesNames, autoSave=True, **kwargs):
        super().__init__(*axesNames, **kwargs)
        self._offsetDict = self.offsetDict(axesNames, self)
        if autoSave:
            self.load()
            self.offsetChanged.connect(self.save)
        self.offsetChanged.connect(lambda: self.valueChanged.emit(self.get()))

    def _valueChanged(self):
        self.valueChanged.emit(self.get())

    def set(self, **kwargs):
        kwargs = {key: value + self.offset.get(key, 0) for key, value in kwargs.items()}
        super().set(**kwargs)

    def get(self, type=dict):
        valueDict = {key: value - self.offset.get(key, 0) for key, value in super().get().items()}
        if type is dict:
            return valueDict
        elif type is list:
            return [valueDict[name] for name in self.nameList]
        elif type is np.ndarray:
            return np.array([valueDict[name] for name in self.nameList])
        else:
            raise TypeError("Unsupported type: {}".format(type))

    @property
    def offset(self):
        """
        Dictionary of offset for respective axes.
        """
        return self._offsetDict

    def save(self, path=".lys/lys_instr/motorOffsets"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            with open(path, "r") as file:
                txt = file.read()
            d = eval(txt)
        else:
            d = {}
        d.update(self.offset)
        with open(path, "w") as file:
            file.write(str(d))

    def load(self, path=".lys/lys_instr/motorOffsets"):
        if not os.path.exists(path):
            return
        with open(path, "r") as file:
            txt = file.read()
            d = eval(txt)
            for key in self.offset.keys():
                self.offset[key] = d.get(key, 0)


class MultiMotorInterface(OffsettableMultiMotorInterface):
    pass
