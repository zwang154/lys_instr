import numpy as np
import qtawesome as qta
import pyqtgraph as pg
import logging
import os
from lys.Qt import QtWidgets, QtGui, QtCore

logging.basicConfig(level=logging.INFO)


class DetectorStorageBridge:
    def __init__(self, detector, storage):
        self._detector = detector
        self._storage = storage
        if self._detector and self._storage:
            self._detector.dataAcquired.connect(self._storage.update)

    def __getattr__(self, name):
        for backend in (self._detector, self._storage):
            if backend is not None and hasattr(backend, name):
                return getattr(backend, name)
        raise AttributeError(f"{type(self).__name__} object has no attribute {name}")
    
    def _output(self, fromFile=False):
        if fromFile:
            if self._storage and self._storage._path and self._storage._type:
                return self._storage.read()
            return None
        else:
            return self._storage.getBuffer()
        
    def close(self):
        if self._detector and hasattr(self._detector, "stop"):
            self._detector.stop()
        if self._storage and hasattr(self._storage, "stop"):
            self._storage.stop()
            


class MultiDetectorGUI(QtWidgets.QGroupBox):

    def __init__(self, obj, title, wait=False, output=False):
        super().__init__(title)
        self._obj = obj
        self._image = np.zeros(obj._indexDim)
        self._wait = wait
        self._output = output
        self._mode = None  # "acquire", "stream", or None

        # Set title style
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.setFont(QtGui.QFont(self.font().family(), 12))

        # Connect signals
        self._obj.busyStateChanged.connect(self._busyStateChanged)
        self._obj.dataAcquired.connect(self._dataAcquired)
        self._obj.aliveStateChanged.connect(self._aliveStateChanged)
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

        self._fileDir = QtWidgets.QLineEdit()
        self._fileDir.setPlaceholderText("Enter file directory...")
        self._fileDir.setText("fstem/.lys_instr/GUI/DataStorage")  # Optionally set default
        self._fileDir.setStyleSheet("font-size: 12pt;")

        slashLabel = QtWidgets.QLabel("/")
        slashLabel.setStyleSheet("font-size: 12pt;")

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

        # Widgets for data displaying
        self._canvas = pg.ImageView()
        self._canvas.ui.menuBtn.hide()
        self._canvas.ui.roiBtn.hide()
        self._canvas.setMinimumSize(500, 400)
        # self._canvas.ui.histogram.hide()
        self._frameView = pg.ImageView()
        self._frameView.ui.menuBtn.hide()
        self._frameView.ui.roiBtn.hide()
        self._frameView.setMinimumSize(500, 400)
        # self._frameView.ui.histogram.hide()

        # Widgets for acquisition control
        self._expTime = QtWidgets.QDoubleSpinBox()
        self._expTime.setValue(self._obj._frameTime)
        self._expTime.setRange(0, np.infty)
        self._expTime.setDecimals(3)
        self._expTime.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._expTime.valueChanged.connect(self._onExposureChanged)

        exposeLabel = QtWidgets.QLabel("Exp. (s)")
        exposeLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self._acquire = QtWidgets.QPushButton('Acquire', clicked=self._onAcquireClicked)
        self._stream = QtWidgets.QPushButton('Stream', clicked=self._onStreamClicked)
        self._stop = QtWidgets.QPushButton('Stop', clicked=self._onStopClicked)
        self._stop.setEnabled(False)

        settings = QtWidgets.QPushButton(qta.icon("ri.settings-5-fill"), "", clicked=self._showSettings)
        settings.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        settings.setIconSize(QtCore.QSize(24, 24))

        self._aliveIndicator = QtWidgets.QLabel()
        icon = qta.icon("ri.checkbox-circle-fill", color="green") if self._obj.isAlive else qta.icon("ri.close-circle-fill", color="red")
        self._aliveIndicator.setPixmap(icon.pixmap(24, 24))
        self._aliveIndicator.setAlignment(QtCore.Qt.AlignCenter)
        self._aliveIndicator.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

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

        imageLayout = QtWidgets.QHBoxLayout()
        imageLayout.addWidget(self._canvas, stretch=1)
        imageLayout.addWidget(self._frameView, stretch=1)

        controlsLayout = QtWidgets.QHBoxLayout()
        controlsLayout.addWidget(self._aliveIndicator)
        controlsLayout.addWidget(exposeLabel)
        controlsLayout.addWidget(self._expTime)
        controlsLayout.addWidget(self._acquire)
        controlsLayout.addWidget(self._stream)
        controlsLayout.addWidget(self._stop)
        controlsLayout.addWidget(settings)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(pathLayout)
        mainLayout.addLayout(imageLayout, stretch=1)
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
        self._obj._storage.setPath(fileDir, fileName, fileType)

    def _onAcquireClicked(self):
        # self._obj._detector._frameTime = self._expTime.value()
        self._obj._detector._numFrames = np.prod(self._obj._indexDim)
        self._mode = "acquire"
        if self._wait:
            self._busyStateChanged(True)
            self._stop.setEnabled(False)
            QtWidgets.QApplication.processEvents()

        self._setPath()
        self._obj.startAcq(wait=self._wait, output=self._output)

    def _onStreamClicked(self):
        # self._obj._detector._frameTime = self._expTime.value()
        self._obj._detector._numFrames = None
        self._mode = "stream"

        self._setPath()
        self._obj.startAcq(wait=False, output=self._output)      # Need to leave wait=False

    def _onStopClicked(self):
        self._mode = None
        self._obj.stop()
        self._stream.setEnabled(True)
        self._acquire.setEnabled(True)
        self._stop.setEnabled(False)

    def _dataAcquired(self, data):
        busy = self._obj.isBusy
        alive = self._obj.isAlive
        self._stream.setEnabled(not busy and alive)
        self._acquire.setEnabled(not busy and alive)
        self._stop.setEnabled(busy)

        # Display logic
        for idx, frame in data.items():
            self._image[idx[-2:]] = self._indexDisplay(frame)
            self._frameView.setImage(self._frameDisplay(frame))
        self._canvas.setImage(self._image)

    def _busyStateChanged(self, busy):
        alive = self._obj.isAlive
        self._fileDir.setEnabled(not busy and alive)
        self._fileName.setEnabled(not busy and alive)
        self._fileType.setEnabled(not busy and alive)
        self._stream.setEnabled(not busy and alive)
        self._acquire.setEnabled(not busy and alive)
        self._stop.setEnabled(busy)

        if busy:
            if self._mode == "acquire":
                self._acquire.setText("Acquiring")
            elif self._mode == "stream":
                self._stream.setText("Streaming")
        else:
            self._acquire.setText("Acquire")
            self._stream.setText("Stream")
            self._mode = None

            # Flush buffer when acquisition finishes
            self._obj.flushBuffer()

    def _aliveStateChanged(self, alive):
        busy = self._obj.isBusy
        self._acquire.setEnabled(not busy and alive)
        self._acquire.setText("Acquiring" if busy else "Acquire")
        self._stream.setEnabled(not busy and alive)
        self._stream.setText("Streaming" if busy else "Stream")
        self._stop.setEnabled(busy)
        icon = qta.icon("ri.checkbox-circle-fill", color="green") if alive else qta.icon("ri.close-circle-fill", color="red")
        self._aliveIndicator.setPixmap(icon.pixmap(24, 24))

    def _savingStateChanged(self, saving):
        icon = qta.icon("ri.loader-2-line", color="orange") if saving else qta.icon("ri.check-line", color="green")
        self._savedIndicator.setPixmap(icon.pixmap(24, 24))

    def _onExposureChanged(self, value):
        self._obj._detector._frameTime = value

    def _showSettings(self):
        dialog = self.settingsWidget(parent=self)
        dialog.open()

    def _indexDisplay(self, data):
        return np.mean(data) 
    
    def _frameDisplay(self, frame):
        return frame

    def closeEvent(self, event):
        try:
            self._obj.close()
        except Exception as e:
            logging.warning(f"Error during cleanup: {e}")
        super().closeEvent(event)

    def settingsWidget(self, parent=None):
        """
        Returns a settings dialog for the device.

        Args:
            parent (QWidget, optional): Parent widget for the dialog.

        Returns:
            QDialog: The settings dialog for the device.
        """
        return _settingsDialog(self._obj, parent)


class _settingsDialog(QtWidgets.QDialog):

    def __init__(self, obj, parent):
        super().__init__(parent=parent)
        self.setWindowTitle('Settings')
        self._obj = obj
        self._obj.aliveStateChanged.connect(self._updateAliveState)
        self._initLayout()

    def _initLayout(self):
        self.setStyleSheet("QLineEdit {font-size: 14pt}"
                           "QLineEdit {border-radius: 12px}"
                           "QDoubleSpinBox {font-size: 14pt}"
                           "QPushButton {font-size: 12pt}"
                           "QLabel {font-size: 12pt}")

        # Create alive panel
        aliveLayout = QtWidgets.QGridLayout()
        
        self._switch = QtWidgets.QPushButton("Change", clicked=self._toggleAlive)
        self._switch.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self._aliveLineEdit = QtWidgets.QLineEdit('Alive')
        self._aliveLineEdit.setAlignment(QtCore.Qt.AlignCenter)

        self._aliveIndicator = QtWidgets.QLabel()
        alive = self._obj.isAlive
        icon = qta.icon("ri.checkbox-circle-fill", color="green") if alive else qta.icon("ri.close-circle-fill", color="red")
        self._aliveIndicator.setPixmap(icon.pixmap(24, 24))
        self._aliveIndicator.setAlignment(QtCore.Qt.AlignCenter)

        aliveLayout.addWidget(self._aliveLineEdit, 1, 0, alignment=QtCore.Qt.AlignCenter)
        aliveLayout.addWidget(self._switch, 0, 0)
        aliveLayout.setColumnStretch(0, 1)

        # Combine layouts
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(aliveLayout) 
        self.setLayout(mainLayout)

        # Initialize alive state  
        self._updateAliveState()
        
    def _toggleAlive(self):
        backend = self._obj._detector
        backend._error = not backend._error
        if (data := backend._get()):                            # _get()
            backend.dataAcquired.emit(data)
        backend.aliveStateChanged.emit(backend.isAlive)

    def _updateAliveState(self):
        if self._obj.isAlive:
            self._aliveLineEdit.setText("Alive")
            self._aliveLineEdit.setStyleSheet("background-color: #adff2f; color: #000000")
        else:
            self._aliveLineEdit.setText("Dead")
            self._aliveLineEdit.setStyleSheet("background-color: #ff0000; color: #ffffff")



# To Test the GUI run in the src\python: python -m fstem.lys_instr.GUI.MultiDetectorGUI
if __name__ == "__main__":
    import sys
    from fstem.lys_instr.dummy.MultiDetectorDummy import MultiDetectorDummy
    from fstem.lys_instr.dummy.DataStorageDummy import DataStorageDummy
    from lys.Qt import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    detector = MultiDetectorDummy(numFrames=None, indexDim=(5, 5), frameDim=(256, 256), frameTime=0.1)
    storage = DataStorageDummy(maxQueueSize=1, bufferThreshold=10, buffered=True)
    specifics = DetectorStorageBridge(detector, storage)
    gui = MultiDetectorGUI(specifics, "Multi-Detector Control", wait=False, output=False)
    gui.show()

    # storage.setPath(gui._fileDir.text(), gui._fileName.text(), gui._fileType.currentText())
    # dataIndices = specifics._output(fromFile=True).keys()
    # print(dataIndices)

    sys.exit(app.exec_())


