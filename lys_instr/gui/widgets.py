import qtawesome as qta
from lys.Qt import QtWidgets, QtCore


class AliveIndicator(QtWidgets.QLabel):
    _ok = qta.icon("ri.checkbox-circle-fill", color="green").pixmap(20, 20)
    _ng = qta.icon("ri.close-circle-fill", color="red").pixmap(20, 20)

    def __init__(self, obj, axis=None):
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
        if self._axis in aliveDict:
            self._aliveStateChanged(aliveDict[self._axis])

    def _aliveStateChanged(self, alive):
        self.setPixmap(self._ok if alive else self._ng)


class SettingsButton(QtWidgets.QPushButton):
    _icon = qta.icon("ri.settings-5-fill")

    def __init__(self, clicked=None):
        super().__init__(self._icon, "")
        if clicked is not None:
            self.clicked.connect(clicked)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.setIconSize(QtCore.QSize(20, 20))

class FolderButton(QtWidgets.QPushButton):
    _icon = qta.icon("ri.folder-open-fill")

    def __init__(self, clicked=None):
        super().__init__(self._icon, "")
        if clicked is not None:
            self.clicked.connect(clicked)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.setIconSize(QtCore.QSize(20, 20))

class MemoryButton(QtWidgets.QPushButton):
    _icon = qta.icon("ri.bookmark-2-fill")

    def __init__(self, clicked=None):
        super().__init__(self._icon, "")
        self.setCheckable(True)
        if clicked is not None:
            self.clicked.connect(clicked)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.setIconSize(QtCore.QSize(20, 20))
