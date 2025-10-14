import qtawesome as qta
import json

from lys.Qt import QtCore, QtWidgets
from .widgets import FolderButton


class DataStorageGUI(QtWidgets.QWidget):
    def __init__(self, obj):
        super().__init__()
        self._obj = obj
        self._settingPath = False

        self._initLayout()
        self._obj.base = self._base.text()
        self._obj.folder = self._folder.text()
        self._obj.name = self._name.text()
        self._obj.savingStateChanged.connect(self._savingStateChanged)

    def _initLayout(self):
        # Widgets for data saving
        browse = FolderButton(clicked=self._browse)
        browse.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self._base = QtWidgets.QLineEdit(objectName="DataStorage_base")
        self._base.setText(".")
        self._folder = QtWidgets.QLineEdit(objectName="DataStorage_folder")
        self._name = QtWidgets.QLineEdit(objectName="DataStorage_name")

        self._savedIndicator = QtWidgets.QLabel()
        self._savedIndicator.setPixmap(qta.icon("ri.check-line", color="green").pixmap(24, 24))
        self._savedIndicator.setAlignment(QtCore.Qt.AlignCenter)

        self._savingState = QtWidgets.QLabel("[Status] Waiting")
        # self._dataShapeText = QtWidgets.QLabel("Data Shape: (None)")

        self._numberedCheck = QtWidgets.QCheckBox("Numbered", checked=True, objectName="DataStorage_numbered")
        self._enabledCheck = QtWidgets.QCheckBox("Enabled", checked=True, objectName="DataStorage_enabled")

        self._number = QtWidgets.QSpinBox()
        self._number.setEnabled(True)

        # Connect signals
        self._base.textChanged.connect(self._pathChanged)
        self._folder.textChanged.connect(self._pathChanged)
        self._name.textChanged.connect(self._pathChanged)
        self._numberedCheck.toggled.connect(self._pathChanged)
        self._enabledCheck.toggled.connect(self._pathChanged)

        # Layout setup
        pathLayout = QtWidgets.QGridLayout()
        pathLayout.setAlignment(QtCore.Qt.AlignTop)
        pathLayout.addWidget(browse, 1, 0)
        pathLayout.addWidget(QtWidgets.QLabel("Base Folder"), 0, 1)
        pathLayout.addWidget(QtWidgets.QLabel("Data Folder"), 0, 2)
        pathLayout.addWidget(QtWidgets.QLabel("File Name"), 0, 3)
        pathLayout.addWidget(self._numberedCheck, 0, 4)
        pathLayout.addWidget(self._base, 1, 1)
        pathLayout.addWidget(self._folder, 1, 2)
        pathLayout.addWidget(self._name, 1, 3)
        pathLayout.addWidget(self._number, 1, 4)
        pathLayout.addWidget(self._savedIndicator, 2, 0)
        pathLayout.addWidget(self._savingState, 2, 1, 1, 3)
        pathLayout.addWidget(self._enabledCheck, 2, 4)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(pathLayout)
        self.setLayout(mainLayout)

    def _pathChanged(self):
        if self._settingPath:
            return

        self._settingPath = True

        # Update storage object properties from GUI fields
        self._obj.base = self._base.text()
        self._obj.folder = self._folder.text()
        self._obj.name = self._name.text()
        self._obj.numbered = self._numberedCheck.isChecked()
        self._obj.enabled = self._enabledCheck.isChecked()

        # Update number spinbox only if numbering is enabled
        number = self._obj.getNumber()
        self._number.setValue(number) if number is not None else self._number.clear()

        # Save last path info
        lastPath = {"base": self._base.text(), "folder": self._folder.text(), "name": self._name.text()}
        with open(".lastPath.json", "w") as f:
            json.dump(lastPath, f)

        self._settingPath = False

    def _browse(self):
        baseStr = QtWidgets.QFileDialog.getExistingDirectory(self, "Select base folder", self._base.text())
        if baseStr:
            self._base.setText(baseStr)

    def _savingStateChanged(self, saving):
        if saving:
            text = f"[Status] {len(self._obj._paths)} files reserved, {len(self._obj._threads)} files being saved."
            self._savingState.setText(text)
        else:
            self._savingState.setText("[Status] Waiting")

        icon = qta.icon("ri.loader-2-line", color="orange") if saving else qta.icon("ri.check-line", color="green")
        self._savedIndicator.setPixmap(icon.pixmap(24, 24))


# To Test the GUI run in the src\python: python -m fstem.lys_instr.GUI.DataStorageGUI
if __name__ == "__main__":
    import sys
    from fstem.lys_instr.DataStorage import DataStorage
    from lys.Qt import QtWidgets
    import numpy as np

    app = QtWidgets.QApplication(sys.argv)
    storage = DataStorage()
    gui = DataStorageGUI(storage)
    gui.show()
    sys.exit(app.exec_())
