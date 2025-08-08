import qtawesome as qta
import logging
import os
from lys.Qt import QtWidgets, QtGui, QtCore

logging.basicConfig(level=logging.INFO)


class DataStorageGUI(QtWidgets.QGroupBox):
    def __init__(self, obj, title):
        super().__init__(title)
        self._obj = obj

        # Set title style
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.setFont(QtGui.QFont(self.font().family(), 12))

        self._obj.savingStateChanged.connect(self._savingStateChanged)
        self._initLayout()

    def _initLayout(self):
        self.setStyleSheet("QLineEdit {font-size: 14pt}"
                           "QDoubleSpinBox {font-size: 14pt}"
                           "QPushButton {font-size: 12pt}"
                           "QLabel {font-size: 12pt}")

        # Widgets for data saving
        saveAsLabel = QtWidgets.QLabel("Save as:")

        browse = QtWidgets.QPushButton(qta.icon("ri.folder-open-fill"), "", clicked=self._browseDir)
        browse.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        browse.setIconSize(QtCore.QSize(24, 24))

        # self._fileDir = QtWidgets.QLineEdit()
        self._fileDir = QtWidgets.QLineEdit()
        self._fileDir.setPlaceholderText("Enter file directory...")
        self._fileDir.setText("fstem/.lys_instr/GUI/MultiDetector")  # Optionally set default
        self._fileDir.setStyleSheet("font-size: 12pt;")

        slashLabel = QtWidgets.QLabel("/")
        slashLabel.setStyleSheet("font-size: 12pt;")

        # self._fileName = QtWidgets.QLineEdit()
        self._fileName = QtWidgets.QLineEdit()
        self._fileName.setPlaceholderText("Enter file name...")
        self._fileName.setText("acquisition")  # Optionally set default
        self._fileName.setStyleSheet("font-size: 12pt;")

        self._fileType = QtWidgets.QComboBox()
        self._fileType.addItems(['hdf5', 'zarr'])
        self._fileType.setCurrentText('hdf5')  # Default selection
        self._fileType.setStyleSheet("QComboBox {font-size: 12pt;}")

        self._savedIndicator = QtWidgets.QLabel()
        self._savedIndicator.setPixmap(qta.icon("ri.check-line", color="green").pixmap(24, 24))
        self._savedIndicator.setAlignment(QtCore.Qt.AlignCenter)

        self._flush = QtWidgets.QPushButton("Flush", clicked=self._onFlushClicked)
        self._flush.setEnabled(False)

        self._bufferedCheck = QtWidgets.QCheckBox("Buffer enabled")
        self._bufferedCheck.setChecked(getattr(self._obj, "_buffered", False))
        self._bufferedCheck.setStyleSheet("font-size: 12pt;")
        self._bufferedCheck.toggled.connect(self._onBufferedCheckToggled)

        # Layout setup
        dirLayout = QtWidgets.QHBoxLayout()
        dirLayout.addWidget(browse)
        dirLayout.addWidget(self._fileDir)
        dirLayout.addWidget(slashLabel)
        dirLayout.addWidget(self._fileName)

        pathLayout = QtWidgets.QHBoxLayout()
        pathLayout.addWidget(saveAsLabel)
        pathLayout.addLayout(dirLayout)
        pathLayout.addWidget(self._fileType)
        pathLayout.addWidget(self._savedIndicator)

        controlsLayout = QtWidgets.QHBoxLayout()
        controlsLayout.addWidget(self._bufferedCheck)
        controlsLayout.addWidget(self._flush)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(pathLayout)
        mainLayout.addLayout(controlsLayout, stretch=0)
        self.setLayout(mainLayout)

    def _browseDir(self):
        dirStr = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory", self._fileDir.text())
        if dirStr:
            self._fileDir.setText(dirStr)
    
    def _setPath(self, overwrite=False):
        # Get directory, filename, and type from widgets
        fileDir = self._fileDir.text().rstrip("/\\")  # Remove trailing slash/backslash
        fileName = self._fileName.text()
        fileType = self._fileType.currentText()
        ext = {'hdf5': 'h5', 'zarr': 'zarr'}.get(fileType, fileType)
        
        # If not overwriting, find a unique filename
        if not overwrite:
            path = f"{os.path.join(fileDir, fileName)}.{ext}"
            i = 1
            uniqueName = fileName
            while os.path.exists(path):
                uniqueName = f"{fileName}_{i}"
                path = os.path.join(fileDir, f"{uniqueName}.{ext}")
                i += 1
            fileName = uniqueName

        # Set the path in storage
        self._obj.setPath(fileDir, fileName, fileType)

    def _savingStateChanged(self, saving):
        icon = qta.icon("ri.loader-2-line", color="orange") if saving else qta.icon("ri.check-line", color="green")
        self._savedIndicator.setPixmap(icon.pixmap(24, 24))
        self._flush.setEnabled(not saving)

    def _onFlushClicked(self):
        try:
            self._obj.flushBuffer()
        except Exception as e:
            logging.error(f"Error flushing buffer: {e}")

    def _onBufferedCheckToggled(self, checked):
        self._obj.setBuffered(checked)
        self._flush.setEnabled(checked)


# PS C:\Users\wzq19\src\python> python -m fstem.lys_instr.GUI.DataStorageGUI
if __name__ == "__main__":
    import sys
    from lys.Qt import QtWidgets
    from fstem.lys_instr.dummy.DataStorageDummy import DataStorageDummy

    app = QtWidgets.QApplication(sys.argv)
    storage = DataStorageDummy(maxQueueSize=1, bufferThreshold=10, buffered=False)
    gui = DataStorageGUI(storage, "Data Storage Control")
    gui.show()

    sys.exit(app.exec_())