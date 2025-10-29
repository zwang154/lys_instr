from lys.Qt import QtWidgets, QtCore
from .random import RandomData, RandomData2D
from .raman import RamanData

dummyOptions = [RandomData, RandomData2D, RamanData]


def loadDataByName(name):
    """
    Returns a dummy data instance matching the given class name.

    Args:
        name (str): Class name of the dummy data provider.

    Returns:
        object: Instance of the matched dummy data provider.

    Raises:
        ValueError: If no provider with the given name exists.
    """
    if name == RamanData.name():
        return RamanData(scanLevel=0)
    elif name == RandomData.name():
        return RandomData((), (600,))
    elif name == RandomData2D.name():
        return RandomData2D()
    else:
        raise ValueError(f"Unknown dummy data name: {name}")


class DummyDataSelector(QtWidgets.QComboBox):
    """
    QComboBox that selects and emits dummy data instances.

    This widget lists available dummy data providers from ``dummyOptions``.
    When the selection changes, it emits the ``changed`` signal with the new provider instance.
    """

    # Emitted with the selected data instance
    changed = QtCore.pyqtSignal(object)

    def __init__(self, detector):
        """
        Initializes the dummy data selector.

        Args:
            detector (object): Object with an ``_obj`` attribute holding the current dummy data instance.
        """
        super().__init__()
        self.addItems([cls.name() for cls in dummyOptions])
        self.currentTextChanged.connect(lambda text: self.changed.emit(loadDataByName(text)))
        self._setCurrentByValue(detector._obj)

    def _setCurrentByValue(self, value):
        """
        Sets the current combo entry to match the given data provider.

        Uses ``value.name()`` to find and select the matching provider in the combo box.

        Args:
            value (object): Dummy data instance whose class exposes a ``name()`` method.
        """
        for cls in dummyOptions:
            if cls.name() == value.name():
                self.setCurrentText(cls.name())
