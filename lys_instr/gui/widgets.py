import qtawesome as qta
from lys.Qt import QtWidgets, QtCore


class AliveIndicator(QtWidgets.QLabel):
    _ok = qta.icon("ri.checkbox-circle-fill", color="green").pixmap(24, 24)
    _ng = qta.icon("ri.close-circle-fill", color="red").pixmap(24, 24)

    def __init__(self, obj):
        super().__init__()
        self._aliveStateChanged(obj.isAlive)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        obj.aliveStateChanged.connect(self._aliveStateChanged)

    def _aliveStateChanged(self, alive):
        self.setPixmap(self._ok if alive else self._ng)


class SettingButton(QtWidgets.QPushButton):
    _icon = qta.icon("ri.settings-5-fill")

    def __init__(self, clicked=None):
        super().__init__(self._icon, "")
        if clicked is not None:
            self.clicked.connect(clicked)
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.setIconSize(QtCore.QSize(24, 24))
