from lys.Qt import QtWidgets, QtCore
from .random import RandomData, RandomData2D
from .raman import RamanData

dummyOptions = [RandomData, RandomData2D, RamanData]

def loadDataByName(name):
    if name == RamanData.name():
        return RamanData(scanLevel=0)
    elif name == RandomData.name():
        return RandomData((), (600,))
    elif name == RandomData2D.name():
        return RandomData2D()
    else:
        raise ValueError(f"Unknown dummy data name: {name}")

class DummyDataSelector(QtWidgets.QComboBox):
    changed = QtCore.pyqtSignal(object)

    def __init__(self, detector):
        super().__init__()
        self.addItems([cls.name() for cls in dummyOptions])
        self.currentTextChanged.connect(lambda text: self.changed.emit(loadDataByName(text)))
        self._setCurrentByValue(detector._obj)

    def _setCurrentByValue(self, value):
        for cls in dummyOptions:
            if cls.name() == value.name():
                self.setCurrentText(cls.name())
