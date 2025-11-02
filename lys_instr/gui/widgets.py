import qtawesome as qta
from lys.Qt import QtWidgets, QtCore


class AliveIndicator(QtWidgets.QLabel):
    """
    Alive-state indicator.
    """

    _ok = qta.icon("ri.checkbox-circle-fill", color="green").pixmap(20, 20)
    _ng = qta.icon("ri.close-circle-fill", color="red").pixmap(20, 20)

    def __init__(self, obj, axis=None):
        """
        Create the alive indicator.

        Args:
            obj (object): Object exposing an ``aliveStateChanged`` signal and an ``isAlive`` attribute (bool or dict[str, bool]).
            axis (str, optional): Axis name to monitor in ``obj.isAlive``; if ``None``, monitor the overall boolean state.
        """
        super().__init__()
        self._axis = axis
        if axis is not None:
            obj.aliveStateChanged.connect(self._aliveStateChangedDict)
            self._aliveStateChanged(obj.isAlive[axis])
        else:
            obj.aliveStateChanged.connect(self._aliveStateChanged)
            self._aliveStateChanged(obj.isAlive)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    def _aliveStateChangedDict(self, aliveDict):
        """
        Update the indicator when a dict of axis states is delivered.

        Args:
            aliveDict (dict): Mapping axis name -> bool alive state.
        """
        if self._axis in aliveDict:
            self._aliveStateChanged(aliveDict[self._axis])

    def _aliveStateChanged(self, alive):
        """
        Set the indicator pixmap according to the boolean state.

        Args:
            alive (bool): True for alive (green), False for not alive (red).
        """
        self.setPixmap(self._ok if alive else self._ng)


class SettingsButton(QtWidgets.QPushButton):
    """
    Icon-only settings button.
    """

    _icon = qta.icon("ri.settings-5-fill")

    def __init__(self, clicked=None):
        """
        Create the settings button.

        Args:
            clicked (callable, optional): Callable to connect to the button's clicked signal.
        """
        super().__init__(self._icon, "")
        if clicked is not None:
            self.clicked.connect(clicked)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.setIconSize(QtCore.QSize(20, 20))

class FolderButton(QtWidgets.QPushButton):
    """
    Icon-only folder button.
    """

    _icon = qta.icon("ri.folder-open-fill")

    def __init__(self, clicked=None):
        """
        Create the folder button.

        Args:
            clicked (callable, optional): Callable to connect to the button's clicked signal.
        """
        super().__init__(self._icon, "")
        if clicked is not None:
            self.clicked.connect(clicked)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.setIconSize(QtCore.QSize(20, 20))
